import os
import json
import requests
import firebase_admin
import google.generativeai as genai
from firebase_admin import credentials, firestore
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# ==========================================
# 🔐 CONFIGURAÇÃO DE CHAVES
# ==========================================
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
FIREBASE_JSON = os.environ.get('FIREBASE_JSON')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Configura o Gemini (Cérebro IA)
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    print("⚠️ AVISO: GEMINI_API_KEY não encontrada. O bot ficará sem IA.")
    model = None

# Configura o Firebase (Memória)
if not firebase_admin._apps:
    if FIREBASE_JSON:
        cred_dict = json.loads(FIREBASE_JSON)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    else:
        print("⚠️ ERRO: FIREBASE_JSON ausente. A memória falhará.")
        exit(1)

db = firestore.client()

# ==========================================
# 🧠 INTELIGÊNCIA ARTIFICIAL
# ==========================================
def analisar_com_ia(titulo, link, contexto):
    """Lê o site e pede um resumo para o Gemini"""
    if not model: return f"🔗 <a href='{link}'>{titulo}</a>"

    texto_site = ""
    try:
        # Tenta entrar no link para ler o conteúdo (se não for PDF)
        if not link.lower().endswith('.pdf'):
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(link, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            # Pega parágrafos de texto
            paragrafos = [p.get_text() for p in soup.find_all('p')]
            texto_site = " ".join(paragrafos)[:3000] # Limita a 3000 caracteres
    except:
        texto_site = "Não foi possível ler o site (talvez seja PDF ou bloqueado)."

    # O Prompt para o Gemini
    prompt = f"""
    Você é um assistente de concursos chamado Golem.
    Analise este link encontrado.
    Contexto desejado: {contexto}
    
    Título: {titulo}
    Link: {link}
    Conteúdo extraído do site: {texto_site}

    TAREFA:
    1. Se for irrelevante para o contexto (ex: propaganda, erro, nada a ver), responda apenas "SKIP".
    2. Se for relevante, escreva um resumo CURTO (máx 2 linhas) com EMOJIS.
    3. Destaque salários, vagas ou datas se encontrar.
    4. Termine com o link clicável em HTML: <a href='{link}'>Acessar Edital</a>
    """

    try:
        response = model.generate_content(prompt)
        resposta = response.text.strip()
        
        if "SKIP" in resposta:
            return None
        return resposta
    except Exception as e:
        print(f"Erro na IA: {e}")
        return f"🔗 <a href='{link}'>{titulo}</a>"

# ==========================================
# 💾 MEMÓRIA
# ==========================================
def link_ja_existe(url):
    doc_id = url.replace('/', '_').replace(':', '').replace('.', '_')[-100:] 
    doc_ref = db.collection('historico_links').document(doc_id)
    return doc_ref.get().exists

def memorizar_link(url, titulo):
    doc_id = url.replace('/', '_').replace(':', '').replace('.', '_')[-100:]
    db.collection('historico_links').document(doc_id).set({
        'url': url, 'titulo': titulo, 'data': firestore.SERVER_TIMESTAMP
    })

# ==========================================
# 📡 RADAR E ENVIO
# ==========================================
def enviar_telegram(mensagem):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "HTML", "disable_web_page_preview": True}
    requests.post(url, json=payload, timeout=15)

def vasculhar_google_news(termo, contexto):
    novidades = []
    try:
        url = f"https://news.google.com/rss/search?q={termo}+when:1d&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        res = requests.get(url, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        for item in soup.find_all('item')[:4]: # Analisa os top 4
            titulo = item.title.get_text()
            link = item.link.get_text() if item.link else ""
            
            if link and not link_ja_existe(link):
                # Aqui chamamos a IA para analisar ANTES de decidir enviar
                print(f"🤖 Analisando com IA: {titulo}...")
                resumo = analisar_com_ia(titulo, link, contexto)
                
                if resumo: # Se a IA não disse "SKIP"
                    novidades.append(resumo)
                    memorizar_link(link, titulo)
                    
        return novidades
    except Exception as e:
        print(f"Erro Google News: {e}")
        return []

def vasculhar_site(url_base, termos, contexto):
    novidades = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url_base, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        for link in soup.find_all('a'):
            texto = link.get_text().strip()
            href = link.get('href')
            
            if texto and href:
                if any(termo in texto.lower() for termo in termos):
                    link_completo = urljoin(url_base, href)
                    if not link_ja_existe(link_completo):
                        print(f"🤖 Analisando com IA: {texto}...")
                        resumo = analisar_com_ia(texto, link_completo, contexto)
                        if resumo:
                            novidades.append(resumo)
                            memorizar_link(link_completo, texto)
        return novidades[:3]
    except Exception as e:
        print(f"Erro site {url_base}: {e}")
        return []

# ==========================================
# 🚀 EXECUÇÃO
# ==========================================
if __name__ == "__main__":
    print("🤖 Golem v4.0 (IA Gemini) iniciando...")
    relatorio = "⚡ <b>RELATÓRIO DE INTELIGÊNCIA</b>\n\n"
    tem_novidade = False

    # 1. MILITAR
    msgs_militar = []
    # Google News Militar
    msgs_militar += vasculhar_google_news("concurso pmma maranhão cfo", "Concurso Militar, PM, Bombeiro, CFO Maranhão")
    # Sites Diretos
    msgs_militar += vasculhar_site("https://www.paes.uema.br/", ["cfo", "oficiais", "bombeiro"], "Vestibular CFO UEMA")
    
    if msgs_militar:
        relatorio += "⚔️ <b>SETOR MILITAR:</b>\n" + "\n\n".join(msgs_militar) + "\n\n"
        tem_novidade = True

    # 2. PEDAGOGIA
    msgs_pedag = []
    # Google News Pedagogia
    msgs_pedag += vasculhar_google_news("processo seletivo professor maranhão", "Concurso Professor, Pedagogia, SEMED Maranhão")
    # PCI
    msgs_pedag += vasculhar_site("https://www.pciconcursos.com.br/concursos/nordeste/ma", ["pedagogia", "professor"], "Concurso Professor Maranhão")

    if msgs_pedag:
        relatorio += "🎓 <b>SETOR PEDAGOGIA:</b>\n" + "\n\n".join(msgs_pedag) + "\n\n"
        tem_novidade = True

    relatorio += "——————————\n<i>Golem IA v4.0</i>"

    if tem_novidade:
        print("🚀 Enviando relatório inteligente...")
        enviar_telegram(relatorio)
    else:
        msg_teste = "🔊 <b>TESTE DE SOM 1, 2, 3...</b>\n\nChronos, se você está lendo isso, o Golem achou o caminho do Grupo! 🛡️❤️\n\n(Nenhuma novidade real, apenas testando a conexão)"
        enviar_telegram(msg_teste)
        print("🔊 Mensagem de teste enviada!")
        #print("🤫 Nada relevante encontrado pela IA.")
    
    print("🏁 Fim da execução.")