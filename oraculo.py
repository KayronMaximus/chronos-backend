import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin  # <--- A FERRAMENTA NOVA ESTÁ AQUI

# Configurações do Telegram
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def enviar_telegram(mensagem):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    # Mudámos para HTML para evitar erros de formatação em links estranhos
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "HTML", "disable_web_page_preview": True}
    requests.post(url, json=payload, timeout=10)

def vasculhar_site(url_base, termos):
    """Função que procura termos e corrige os links quebrados"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url_base, headers=headers, timeout=20)
        soup = BeautifulSoup(res.text, 'html.parser')
        achados = []
        
        for link in soup.find_all('a'):
            texto = link.get_text().strip()
            href = link.get('href')
            
            if texto and href: # Garante que tem texto e link
                texto_lower = texto.lower()
                if any(termo in texto_lower for termo in termos):
                    # A MÁGICA ACONTECE AQUI:
                    # Se o link for "/edital.pdf", ele vira "https://site.com/edital.pdf"
                    link_completo = urljoin(url_base, href)
                    
                    # Formatação em HTML: <a href="LINK">TITULO</a>
                    achados.append(f"🔗 <a href='{link_completo}'>{texto}</a>")
                    
        return list(set(achados[:5])) # Retorna até 5 links únicos
    except Exception as e:
        print(f"Erro ao ler {url_base}: {e}")
        return []

if __name__ == "__main__":
    print("🤖 Golem a iniciar patrulha com correção de links...")
    
    # 🎯 CONFIGURAÇÃO DE BUSCA - CHRONOS (MILITAR)
    sites_militar = [
        ("UEMA PAES", "https://www.paes.uema.br/", ["cfo", "pmma", "bombeiro", "oficiais"]),
        ("PCI Nordeste", "https://www.pciconcursos.com.br/concursos/nordeste/ma", ["pm", "militar", "segurança"])
    ]
    
    # 🎯 CONFIGURAÇÃO DE BUSCA - NAMORADA (PEDAGOGIA)
    sites_pedagogia = [
        ("PCI Maranhão", "https://www.pciconcursos.com.br/concursos/nordeste/ma", ["pedagogia", "professor", "educação", "semed", "seletivo"]),
        ("Diário Oficial MA", "https://www.diariooficial.ma.gov.br/", ["educação", "semed"])
    ]

    relatorio = "🔔 <b>RELATÓRIO DO ORÁCULO</b>\n\n"
    has_content = False

    # Busca Militar
    temp_msg = "⚔️ <b>Vigilância Chronos (CFO/Militar):</b>\n"
    encontrou_militar = False
    for nome, url, termos in sites_militar:
        links = vasculhar_site(url, termos)
        if links:
            temp_msg += f"📍 {nome}:\n" + "\n".join(links) + "\n\n"
            encontrou_militar = True
    
    if encontrou_militar:
        relatorio += temp_msg
        has_content = True
    else:
        relatorio += "⚔️ Nada de novo na frente de batalha.\n\n"

    relatorio += "———————————————\n\n"

    # Busca Pedagogia
    temp_msg = "🎓 <b>Vigilância Amor (Pedagogia):</b>\n"
    encontrou_pedag = False
    for nome, url, termos in sites_pedagogia:
        links = vasculhar_site(url, termos)
        if links:
            temp_msg += f"📍 {nome}:\n" + "\n".join(links) + "\n\n"
            encontrou_pedag = True
            
    if encontrou_pedag:
        relatorio += temp_msg
        has_content = True
    else:
        relatorio += "🎓 Nenhuma vaga nova para Pedagogia.\n"

    relatorio += "\n<i>Golem de Vigília v2.1</i>"
    
    # Envia a mensagem apenas se houver novidades (ou sempre, como preferires)
    enviar_telegram(relatorio)
    print("🏁 Patrulha concluída.")