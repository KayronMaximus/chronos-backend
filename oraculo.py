import os
import json
import requests
from bs4 import BeautifulSoup

# Configurações do Telegram
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def enviar_telegram(mensagem):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    requests.post(url, json=payload, timeout=10)

def vasculhar_site(url, termos):
    """Função genérica para procurar termos em links de um site"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(res.text, 'html.parser')
        achados = []
        for link in soup.find_all('a'):
            texto = link.get_text().lower()
            if any(termo in texto for termo in termos):
                achados.append(f"🔗 [{link.get_text().strip()}]({link.get('href')})")
        return list(set(achados[:3])) # Retorna até 3 links únicos
    except:
        return []

if __name__ == "__main__":
    print("🤖 Golem iniciando patrulha expandida...")
    
    # 🎯 CONFIGURAÇÃO DE BUSCA - CHRONOS (MILITAR)
    sites_militar = [
        ("UEMA PAES", "https://www.paes.uema.br/", ["cfo", "pmma", "bombeiro", "oficiais"]),
        ("PCI Nordeste", "https://www.pciconcursos.com.br/concursos/nordeste/ma", ["pm", "militar", "segurança"])
    ]
    
    # 🎯 CONFIGURAÇÃO DE BUSCA - NAMORADA (PEDAGOGIA)
    sites_pedagogia = [
        ("PCI Maranhão", "https://www.pciconcursos.com.br/concursos/nordeste/ma", ["pedagogia", "professor", "educação", "semed"]),
        ("Diário Oficial MA", "https://www.diariooficial.ma.gov.br/", ["seletivo", "educação"])
    ]

    relatorio = "🔔 *RELATÓRIO DO ORÁCULO*\n\n"
    
    # Busca Militar
    relatorio += "⚔️ *Vigilância Chronos (CFO/Militar):*\n"
    encontrou_militar = False
    for nome, url, termos in sites_militar:
        links = vasculhar_site(url, termos)
        if links:
            relatorio += f"📍 {nome}:\n" + "\n".join(links) + "\n"
            encontrou_militar = True
    if not encontrou_militar: relatorio += "✅ Nada de novo na frente de batalha.\n"

    relatorio += "\n" + "—" * 15 + "\n\n"

    # Busca Pedagogia
    relatorio += "🎓 *Vigilância Yasmin (Pedagogia):*\n"
    encontrou_pedag = False
    for nome, url, termos in sites_pedagogia:
        links = vasculhar_site(url, termos)
        if links:
            relatorio += f"📍 {nome}:\n" + "\n".join(links) + "\n"
            encontrou_pedag = True
    if not encontrou_pedag: relatorio += "✅ Nenhuma vaga nova para Pedagogia.\n"

    relatorio += "\n_Golem de Vigília v2.0_"
    
    enviar_telegram(relatorio)
    print("🏁 Patrulha concluída com sucesso!")