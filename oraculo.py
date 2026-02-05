import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, messaging

# 1. Tenta pegar a chave do cofre do GitHub
service_account_info = os.environ.get('FIREBASE_JSON')

if service_account_info:
    # Se encontrou a variável (Está no GitHub)
    print("🤖 Golem iniciado: Usando credenciais de ambiente.")
    cred_dict = json.loads(service_account_info)
    cred = credentials.Certificate(cred_dict)
else:
    # Se NÃO encontrou (Está no seu PC)
    print("🏠 PC Local: Usando arquivo serviceAccountKey.json")
    # Certifique-se de que o nome do arquivo abaixo está correto no seu PC
    cred = credentials.Certificate("serviceAccountKey.json")

# 2. Inicializa o App
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()
#import os
#import json
#import firebase_admin
#from firebase_admin import credentials, firestore, messaging
#import time
#from datetime import datetime
#import requests
#from bs4 import BeautifulSoup

# ==========================================
# CONFIGURAÇÃO DE SEGURANÇA (GOLEM LOGIC)
# ==========================================
# O GitHub Actions vai preencher essa variável automaticamente
#service_account_info = os.environ.get('FIREBASE_JSON')

#if service_account_info:
    # Se estiver rodando no GitHub (Golem)
    #print("🤖 Golem iniciado: Usando credenciais de ambiente.")
    #cred_dict = json.loads(service_account_info)
    #cred = credentials.Certificate(cred_dict)
#else:
    # Se estiver rodando no seu PC local
 #   print("🏠 PC Local: Usando serviceAccountKey.json")
  #  cred = credentials.Certificate("serviceAccountKey.json")

# Inicializa o Firebase apenas se não tiver sido inicializado antes
#if not firebase_admin._apps:
 #   firebase_admin.initialize_app(cred)
# 1. CONEXÃO COM O OLIMPO
#cred = credentials.Certificate("serviceAccountKey.json")
#firebase_admin.initialize_app(cred)
#db = firestore.client()

def buscar_dados_externos():
    print("🔎 Oráculo vasculhando editais na UEMA...")
    url = "https://www.paes.uema.br/" 
    headers = {'User-Agent': 'Mozilla/5.0'} # Evita ser bloqueado pelo servidor
    noticia = "Nenhuma movimentação suspeita no PAES/CFO."
    
    try:
        # 1. Faz a requisição com um User-Agent (simulando navegador)
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status() # Garante que o site respondeu 200 OK
        
        # 2. Transforma o HTML em algo que o Python entende
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 3. Procura especificamente em links e títulos
        termos_chave = ["cfo", "oficiais", "bombeiro", "pmma", "cbmma", "edital 2026", "concurso 2026", "edital oficial", "concurso oficial", "edital de oficiais", "concurso de oficiais", "edital de bombeiro", "concurso de bombeiro", ]
        encontrado = False
        
        # Varre todos os links do site
        for link in soup.find_all('a'):
            texto = link.get_text().lower()
            if any(termo in texto for termo in termos_chave):
                noticia = f"🚨 ALERTA: Link detectado: '{link.get_text().strip()}'"
                encontrado = True
                break
        
        # Se não achou em links, faz uma busca rápida no texto visível
        if not encontrado:
            texto_visivel = soup.get_text().lower()
            if "edital 2026" in texto_visivel or "cfo 2026" in texto_visivel:
                noticia = "🚨 ALERTA: Menção ao CFO 2026 encontrada no site!"

    except Exception as e:
        print(f"❌ Erro técnico: {e}")
        noticia = "⚠️ Radar offline: Falha ao acessar site da UEMA."

    # Salva no Firestore (Exatamente como você já faz)
    db.collection('oraculo_updates').add({
        'tipo': 'radar_estudos',
        'conteudo': noticia,
        'data': firestore.SERVER_TIMESTAMP
    })
    return noticia

# No oraculo.py (Pasta Backend)
def enviar_notificacao_push(titulo, corpo):
    print(f"📡 Disparando sinal de ALTA PRIORIDADE...")
    all_tokens = db.collection_group('tokens').stream()
    
    for doc in all_tokens:
        token = doc.to_dict().get('token')
        if token:
            try:
                message = messaging.Message(
                        data={
                                "title": "🚨 ALERTA DO ORÁCULO",
                                "body": "Movimentação detectada no CFO!",
                                "link": "https://kayronmaximus.github.io/ai-plus-defce/"
                            },
                    notification=messaging.Notification(
                        title=titulo,
                        body=corpo,
                    ),
                    android=messaging.AndroidConfig(
                        ttl=3600,
                        priority='high', # Isso aqui já define a prioridade alta
                        notification=messaging.AndroidNotification(
                            channel_id='default',
                            priority='high', # Aqui também
                            default_sound=True,
                            default_vibrate_timings=True,
                            click_action='https://kayronmaximus.github.io/ai-plus-defce/'
                        ),
                    ),
webpush=messaging.WebpushConfig(
        fcm_options=messaging.WebpushFCMOptions(
            link='https://kayronmaximus.github.io/ai-plus-defce/'
        ),
        headers={"Urgency": "high"}
                    ),
                    token=token,
                )
                messaging.send(message)
                print(f"✅ Sinal enviado com sucesso!")
            except Exception as e:
                print(f"❌ Erro: {e}")

def vigilia_noturna():
    # 1. Vasculha o site da UEMA
    resumo = buscar_dados_externos()
    
    # 2. Prepara a mensagem
    msg = f"{resumo} Não esqueça de bater sua meta de TI hoje!"
    
    # 3. Dispara a notificação
    enviar_notificacao_push("🌙 Relatório da Vigília", msg)
    
    # 4. Encerra (O GitHub Actions acordará o script novamente em 1 hora)
    print("✅ Vigília concluída. O Golem vai descansar até a próxima hora.")

if __name__ == "__main__":
    vigilia_noturna()