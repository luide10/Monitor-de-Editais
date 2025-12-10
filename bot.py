import os
import telebot
import google.generativeai as genai
import feedparser
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

# --- CONFIGURAÇÕES ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
CHAT_ID = os.environ.get('MEU_CHAT_ID')

PALAVRAS_CHAVE = [
    "concurso", "edital", "reda", "processo seletivo", "vaga", 
    "policia", "polícia", "militar", "civil", "federal", 
    "cientifica", "científica", "portuaria", "portuária", 
    "perito", "investigador", "delegado", "soldado"
]

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
bot = telebot.TeleBot(TELEGRAM_TOKEN)

def analisar_com_ia(titulo, texto_site, link, fonte):
    print(f"🧠 IA Analisando ({fonte}): {titulo}...")
    prompt = f"""
    Analise esta oportunidade de trabalho/concurso na Bahia.
    FONTE: {fonte}
    TÍTULO: {titulo}
    TEXTO: {texto_site}
    
    Responda EXATAMENTE neste formato:
    📢 **ALERTA DE OPORTUNIDADE ({fonte})**
    🏢 **Órgão:** [Nome]
    💼 **Cargo:** [Cargos principais]
    🏛️ **Banca:** [Nome da banca ou "Processo Simplificado/REDA"]
    📝 **Redação:** [Sim/Não/Não informado]
    🎯 **Resumo:** [Explicação breve em 1 frase]
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return f"Erro na IA. Veja o link: {link}"

def enviar_telegram(mensagem, link):
    try:
        msg_final = f"{mensagem}\n\n🔗 **Link:** {link}"
        bot.send_message(CHAT_ID, msg_final, parse_mode="Markdown")
        print("✅ Enviado!")
    except Exception as e:
        print(f"❌ Erro telegram: {e}")

def motor_google_news():
    print("--- 🌍 Verificando Google News... ---")
    url_rss = "https://news.google.com/rss/search?q=concurso+bahia+OR+policia+bahia+OR+reda+bahia+OR+edital+bahia&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    feed = feedparser.parse(url_rss)
    
    # Pega o horário de agora e subtrai 3 horas (para pegar só o que é novo)
    # Como o bot roda a cada 2h, pegamos 3h de margem de segurança
    agora = datetime.now()
    margem = agora - timedelta(hours=3)

    for entry in feed.entries:
        titulo = entry.title
        link = entry.link
        
        # Tenta pegar a data de publicação da notícia
        try:
            data_publicacao = parsedate_to_datetime(entry.published).replace(tzinfo=None)
        except:
            data_publicacao = agora # Se não tiver data, assume que é agora

        # Só processa se a notícia for RECENTE (das últimas 3 horas)
        if data_publicacao > margem:
            if any(p in titulo.lower() for p in PALAVRAS_CHAVE):
                try:
                    resp = requests.get(link, timeout=10)
                    soup = BeautifulSoup(resp.content, 'html.parser')
                    texto = soup.get_text(" ", strip=True)[:3000]
                except:
                    texto = "Texto não acessível."
                
                analise = analisar_com_ia(titulo, texto, link, "Google News")
                enviar_telegram(analise, link)
                time.sleep(2) # Pausa pequena entre envios

def motor_ba_gov():
    print("--- 🏛️ Verificando BA.GOV... ---")
    url = "https://www.ba.gov.br/servidores"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        
        # --- LINHAS DE TESTE NOVAS ---
        print(f"Status da conexão: {response.status_code}") # Deve ser 200
        # -----------------------------

        soup = BeautifulSoup(response.text, 'html.parser')
        noticias = soup.find_all(['h2', 'h3'])
        
        # --- LINHA DE TESTE NOVA ---
        print(f"🔎 O Robô enxergou {len(noticias)} manchetes nesta página.")
        # ---------------------------
        
        # Analisa apenas as 3 primeiras
        for item in noticias[:3]: 
            titulo = item.get_text().strip()
            # Imprime o título nos logs para você ver o que ele leu
            print(f"   > Manchete lida: {titulo}") 
            
            link_tag = item.find('a')
            if link_tag:
                link = link_tag['href']
                if not link.startswith('http'): link = 'https://www.ba.gov.br' + link
                
                if any(p in titulo.lower() for p in PALAVRAS_CHAVE):
                    try:
                        resp = requests.get(link, headers=headers)
                        soup_d = BeautifulSoup(resp.content, 'html.parser')
                        texto = soup_d.get_text(" ", strip=True)[:3000]
                    except:
                        texto = "..."
                    
                    analise = analisar_com_ia(titulo, texto, link, "Portal BA.GOV")
                    enviar_telegram(analise, link)
                    time.sleep(2)

    except Exception as e:
        print(f"Erro CRÍTICO ao ler ba.gov: {e}")

def main():
    print("🚀 Execução Única Iniciada (GitHub Actions)")
    # Roda uma vez e para. O GitHub vai chamar de novo daqui a 2 horas.
    motor_ba_gov()
    motor_google_news()
    print("🏁 Fim da execução.")

if __name__ == "__main__":
    main()
