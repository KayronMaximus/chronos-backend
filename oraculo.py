import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, messaging
import requests
from bs4 import BeautifulSoup

# ==========================================
# 🛡️ CONFIGURAÇÃO DE SEGURANÇA
# ==========================================
service_account_info = os.environ.get('FIREBASE_JSON')
TELEGRAM_TOKEN = os.environ.get('8496652168:AAEjYrA9c2-K6CsxAbcWoWrBF6rH2tU7f6o')
TELEGRAM_CHAT_ID = os.environ.get('8217910497')

if service_account_info:
    cred_dict = json.loads(service_account_info)
    cred = credentials.Certificate(cred_dict)
else:
    # Caso rode localmente, ele tenta o arquivo
    cred = credentials.Certificate("serviceAccountKey.json")

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

# ==========================================
# 🛰️ COMUNICAÇÃO (TELEGRAM)
# ==========================================
def enviar_telegram(mensagem):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram não configurado nos Secrets.")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"✅ Resposta Telegram: {r.status_code}")
    except Exception as e:
        print(f"❌ Erro no envio: {e}")

# ==========================================
# 🔎 RADAR DE EDITAIS
# ==========================================
def buscar_dados_externos():
    url = "https://www.paes.uema.br/" 
    headers = {'User-Agent': 'Mozilla/5.0'}
    noticia = "Nenhuma movimentação suspeita no PAES/CFO."
    
    try:
        res = requests.get(url, headers=headers, timeout=20)
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
# 🌙 VIGÍLIA
# ==========================================
if __name__ == "__main__":
    print("🤖 Golem em patrulha...")
    resumo = buscar_dados_externos()
    msg = f"🔔 *RELATÓRIO DO ORÁCULO*\n\n{resumo}\n\n_Meta de TI batida?_"
    enviar_telegram(msg)
    print("🏁 Patrulha concluída.")