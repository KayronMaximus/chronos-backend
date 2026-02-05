import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Configurações do Telegram
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def enviar_telegram(mensagem):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "HTML", "disable_web_page_preview": True}
    requests.post(url, json=payload, timeout=10)

def vasculhar_site(url_base, termos):
    """Lê sites normais (HTML)"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url_base, headers=headers, timeout=20)
        soup = BeautifulSoup(res.text, 'html.parser')
        achados = []
        for link in soup.find_all('a'):
            texto = link.get_text().strip()
            href = link.get('href')
            if texto and href:
                texto_lower = texto.lower()
                if any(termo in texto_lower for termo in termos):
                    link_completo = urljoin(url_base, href)
                    achados.append(f"🔗 <a href='{link_completo}'>{texto}</a>")
        return list(set(achados[:5]))
    except Exception as e:
        print(f"Erro no site {url_base}: {e}")
        return []

def vasculhar_google_news(termo_busca):
    """Lê o Feed do Google News (XML) para furar bloqueios"""
    try:
        # Cria o link do RSS do Google News para o Maranhão
        url = f"https://news.google.com/rss/search?q={termo_busca}+when:1d&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        res = requests.get(url, timeout=20)
        # Usa 'html.parser' para garantir compatibilidade sem instalar lxml
        soup = BeautifulSoup(res.text, 'html.parser')
        achados = []
        
        # No RSS, as notícias ficam dentro de tags <item>
        items = soup.find_all('item')
        for item in items[:3]: # Pega só as 3 mais recentes
            titulo = item.title.get_text()
            link = item.link.get_text() # Às vezes o link vem sujo, mas o Telegram resolve
            if link:
                achados.append(f"📰 <a href='{link}'>{titulo}</a>")
        return achados
    except Exception as e:
        print(f"Erro no Google News: {e}")
        return []

if __name__ == "__main__":
    print("🤖 Golem v2.2 iniciando patrulha...")

    relatorio = "🔔 <b>RELATÓRIO DO ORÁCULO</b>\n\n"
    has_content = False

    # ==============================
    # ⚔️ SETOR 1: MILITAR (CHRONOS)
    # ==============================
    temp_msg = "⚔️ <b>Vigilância Chronos (CFO/Militar):</b>\n"
    encontrou_militar = False
    
    # Sites Normais
    sites_militar = [
        ("UEMA PAES", "https://www.paes.uema.br/", ["cfo", "pmma", "bombeiro", "oficiais"]),
        ("PCI Nordeste", "https://www.pciconcursos.com.br/concursos/nordeste/ma", ["pm ", "militar", "bombeiro"])
    ]
    for nome, url, termos in sites_militar:
        links = vasculhar_site(url, termos)
        if links:
            temp_msg += f"📍 {nome}:\n" + "\n".join(links) + "\n\n"
            encontrou_militar = True
            
    # Google News (Reforço)
    news_links = vasculhar_google_news("concurso pmma maranhão")
    if news_links:
        temp_msg += f"📍 Google News (Últimas 24h):\n" + "\n".join(news_links) + "\n\n"
        encontrou_militar = True

    if encontrou_militar:
        relatorio += temp_msg
        has_content = True
    else:
        relatorio += "⚔️ Nada de novo no front.\n\n"

    relatorio += "———————————————\n\n"

    # ==============================
    # 🎓 SETOR 2: PEDAGOGIA (AMOR)
    # ==============================
    temp_msg = "🎓 <b>Vigilância Amor (Pedagogia):</b>\n"
    encontrou_pedag = False

    # Sites Normais
    sites_pedagogia = [
        ("PCI Maranhão", "https://www.pciconcursos.com.br/concursos/nordeste/ma", ["pedagogia", "professor", "educação", "seletivo"]),
    ]
    for nome, url, termos in sites_pedagogia:
        links = vasculhar_site(url, termos)
        if links:
            temp_msg += f"📍 {nome}:\n" + "\n".join(links) + "\n\n"
            encontrou_pedag = True

    # Google News (Substituindo o Diário Oficial bloqueado)
    news_links = vasculhar_google_news("processo seletivo professor maranhão")
    if news_links:
        temp_msg += f"📍 Google News (Últimas 24h):\n" + "\n".join(news_links) + "\n\n"
        encontrou_pedag = True

    if encontrou_pedag:
        relatorio += temp_msg
        has_content = True
    else:
        relatorio += "🎓 Nenhuma vaga nova para Pedagogia.\n"

    relatorio += "\n<i>Golem de Vigília v2.2</i>"
    
    enviar_telegram(relatorio)
    print("🏁 Patrulha concluída.")