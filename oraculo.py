import os
import json
import requests
import firebase_admin
from firebase_admin import credentials, firestore
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# ==========================================
# 🛡️ CONFIGURAÇÃO E SEGURANÇA
# ==========================================
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
FIREBASE_JSON = os.environ.get('FIREBASE_JSON')

# Inicializa o Banco de Dados (Memória)
if not firebase_admin._apps:
    if FIREBASE_JSON:
        cred_dict = json.loads(FIREBASE_JSON)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    else:
        print("⚠️ ERRO CRÍTICO: FIREBASE_JSON não encontrado nos Secrets!")
        exit(1)

db = firestore.client()

# ==========================================
# 🧠 FUNÇÕES DE MEMÓRIA
# ==========================================
def link_ja_existe(url):
    """Pergunta ao cérebro se esse link já foi enviado antes"""
    # Usa a URL como ID do documento (substituindo caracteres inválidos)
    doc_id = url.replace('/', '_').replace(':', '').replace('.', '_')[-100:] 
    doc_ref = db.collection('historico_links').document(doc_id)
    doc = doc_ref.get()
    return doc.exists

def memorizar_link(url, titulo):
    """Grava o link no cérebro para não repetir"""
    doc_id = url.replace('/', '_').replace(':', '').replace('.', '_')[-100:]
    db.collection('historico_links').document(doc_id).set({
        'url': url,
        'titulo': titulo,
        'data': firestore.SERVER_TIMESTAMP
    })

# ==========================================
# 📡 FUNÇÕES DE RADAR
# ==========================================
def enviar_telegram(mensagem):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "HTML", "disable_web_page_preview": True}
    requests.post(url, json=payload, timeout=10)

def vasculhar_site(url_base, termos):
    novidades = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url_base, headers=headers, timeout=20)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        for link in soup.find_all('a'):
            texto = link.get_text().strip()
            href = link.get('href')
            
            if texto and href:
                texto_lower = texto.lower()
                if any(termo in texto_lower for termo in termos):
                    link_completo = urljoin(url_base, href)
                    
                    # O FILTRO MÁGICO ACONTECE AQUI
                    if not link_ja_existe(link_completo):
                        novidades.append((texto, link_completo))
                        memorizar_link(link_completo, texto)
                        
        return novidades[:5]
    except Exception as e:
        print(f"Erro no site {url_base}: {e}")
        return []

def vasculhar_google_news(termo_busca):
    novidades = []
    try:
        url = f"https://news.google.com/rss/search?q={termo_busca}+when:1d&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        res = requests.get(url, timeout=20)
        soup = BeautifulSoup(res.text, 'html.parser') # Parser simples para XML
        
        items = soup.find_all('item')
        for item in items[:5]:
            titulo = item.title.get_text()
            link = item.link.get_text() if item.link else ""
            
            if link and not link_ja_existe(link):
                novidades.append((titulo, link))
                memorizar_link(link, titulo)
                
        return novidades
    except Exception as e:
        print(f"Erro no Google News: {e}")
        return []

# ==========================================
# 🚀 FLUXO PRINCIPAL
# ==========================================
if __name__ == "__main__":
    print("🤖 Golem v3.0 (Com Memória) iniciando...")

    relatorio = "🔔 <b>NOVIDADES DETECTADAS!</b>\n\n"
    tem_novidade = False

    # ⚔️ MILITAR
    msg_militar = ""
    sites_militar = [
        ("UEMA PAES", "https://www.paes.uema.br/", ["cfo", "pmma", "bombeiro", "oficiais"]),
        ("PCI Nordeste", "https://www.pciconcursos.com.br/concursos/nordeste/ma", ["pm ", "militar", "bombeiro"])
    ]
    
    # Checa sites normais
    for nome, url, termos in sites_militar:
        itens = vasculhar_site(url, termos)
        if itens:
            msg_militar += f"📍 {nome}:\n"
            for titulo, link in itens:
                msg_militar += f"🔗 <a href='{link}'>{titulo}</a>\n"
            msg_militar += "\n"
    
    # Checa Google News
    news_items = vasculhar_google_news("concurso pmma maranhão")
    if news_items:
        msg_militar += f"📍 Google News:\n"
        for titulo, link in news_items:
            msg_militar += f"📰 <a href='{link}'>{titulo}</a>\n"
        msg_militar += "\n"

    if msg_militar:
        relatorio += "⚔️ <b>Chronos (Militar):</b>\n" + msg_militar
        tem_novidade = True

    # 🎓 PEDAGOGIA
    msg_pedag = ""
    sites_pedagogia = [
        ("PCI Maranhão", "https://www.pciconcursos.com.br/concursos/nordeste/ma", ["pedagogia", "professor", "educação", "seletivo"]),
    ]
    
    for nome, url, termos in sites_pedagogia:
        itens = vasculhar_site(url, termos)
        if itens:
            msg_pedag += f"📍 {nome}:\n"
            for titulo, link in itens:
                msg_pedag += f"🔗 <a href='{link}'>{titulo}</a>\n"
            msg_pedag += "\n"

    news_items = vasculhar_google_news("processo seletivo professor maranhão")
    if news_items:
        msg_pedag += f"📍 Google News:\n"
        for titulo, link in news_items:
            msg_pedag += f"📰 <a href='{link}'>{titulo}</a>\n"
        msg_pedag += "\n"

    if msg_pedag:
        relatorio += "🎓 <b>Amor (Pedagogia):</b>\n" + msg_pedag
        tem_novidade = True
        
    relatorio += "———————————————\n<i>Golem v3.0 - Modo Silencioso Ativo</i>"

    # SÓ ENVIA SE TIVER NOVIDADE (IMPLEMENTAÇÃO DO PASSO 2)
    if tem_novidade:
        print("🚀 Novidades encontradas! Enviando Telegram...")
        enviar_telegram(relatorio)
    else:
        print("🤫 Nenhuma novidade no radar. Golem permanece em silêncio.")

    print("🏁 Patrulha concluída.")