import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, messaging
import requests
from bs4 import BeautifulSoup

# ==========================================
# 🛡️ SEGURANÇA E CREDENCIAIS
# ==========================================
service_account_info = os.environ.get('FIREBASE_JSON')
TELEGRAM_TOKEN = os.environ.get('8496652168:AAEjYrA9c2-K6CsxAbcWoWrBF6rH2tU7f6o')
TELEGRAM_CHAT_ID = os.environ.get('8217910497')

if service_account_info:
    print("🤖 Golem iniciado: Usando credenciais de ambiente.")
    cred_dict = json.loads(service_account_info)
    cred = credentials.Certificate(cred_dict)
else:
    print("🏠 PC Local: Usando arquivo serviceAccountKey.json")
    cred = credentials.Certificate("serviceAccountKey.json")

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

# ==========================================
# 🛰️ FUNÇÃO TELEGRAM (INFALÍVEL NO CELULAR)
# ==========================================
def enviar_telegram(mensagem):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram não configurado nos Secrets.")
        return
    
    print("🚀 Enviando sinal via Telegram...")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    
    try:
        requests.post(url, json=payload, timeout=10)
        print("✅ Telegram entregue!")
    except Exception as e:
        print(f"❌ Falha no Telegram: {e}")

# ==========================================
# 🔎 BUSCA DE DADOS (SITE UEMA)
# ==========================================
def buscar_dados_externos():
    print("🔎 Vasculhando editais...")
    url = "https://www.paes.uema.br/" 
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    noticia = "Nenhuma movimentação suspeita no PAES/CFO."
    
    try:
        res = requests.get(url, headers=headers, timeout=20)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        termos = ["cfo", "oficiais", "bombeiro", "pmma", "edital 2026"]
        for link in soup.find_all('a'):
            texto = link.get_text().lower()
            if any(termo in texto for termo in termos):
                noticia = f"🚨 ALERTA: Link detectado: '{link.get_text().strip()}'"
                break
    except:
        noticia = "⚠️ Radar offline: Falha ao acessar site da UEMA."

    return noticia

# ==========================================
# 🌙 VIGÍLIA (EXECUÇÃO ÚNICA PARA O GOLEM)
# ==========================================
if __name__ == "__main__":
    resumo = buscar_dados_externos()
    msg_telegram = f"🔔 *RELATÓRIO DO ORÁCULO*\n\n{resumo}\n\n_Não esqueça da meta de TI hoje!_"
    
    # Envia para os dois canais
    enviar_telegram(msg_telegram)
    print("🏁 Patrulha concluída.")
