import os
import telebot
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import urllib3

# Configurações iniciais
urllib3.disable_warnings()
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
CHAT_ID = os.environ.get('MEU_CHAT_ID')

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')
bot = telebot.TeleBot(TELEGRAM_TOKEN)

def verificar():
    print("--- INICIANDO SISTEMA VIA GOOGLE ---", flush=True)
    
    # ESTRATÉGIA ANTI-BLOQUEIO:
    # Vamos pesquisar no Google News por editais recentes na Bahia
    url = "https://www.google.com/search?q=site:ba.gov.br+REDA+2025+inscrições&tbm=nws"
    
    print(f"📡 Consultando o Google...", flush=True)
    
    try:
        # Headers essenciais para o Google não bloquear
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Timeout curto, pois o Google responde rápido
        response = requests.get(url, headers=headers, timeout=10)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # O Google News geralmente coloca títulos em divs com role='heading' ou tags h3
        resultados = soup.find_all('div', role='heading')
        
        if not resultados:
            resultados = soup.find_all('h3')

        encontrou_algo = False
        
        # Pega o primeiro resultado só para provar que funcionou
        for item in resultados[:1]:
            titulo = item.get_text().strip()
            
            # Tenta limpar o link (o Google suja o link com redirecionamentos)
            parent = item.find_parent('a')
            link = "Link do Google"
            if parent and 'href' in parent.attrs:
                raw_link = parent['href']
                if "/url?q=" in raw_link:
                    link = raw_link.split("/url?q=")[1].split("&")[0]
                else:
                    link = raw_link

            print(f"🔎 Encontrei: {titulo}")
            
            # Manda para o canal a prova de vida
            msg = (
                f"🤖 **STATUS: CONEXÃO RECUPERADA!**\n"
                f"Usei o Google para pular o bloqueio.\n\n"
                f"📰 **Última notícia encontrada:**\n"
                f"_{titulo}_\n\n"
                f"🔗 {link}"
            )
            
            if CHAT_ID:
                try:
                    bot.send_message(CHAT_ID, msg)
                    print("✅ Sucesso! Mensagem enviada.")
                    encontrou_algo = True
                except Exception as e:
                    print(f"Erro Telegram: {e}")
            
        if not encontrou_algo:
            print("Google acessado, mas estrutura HTML diferente da esperada.")
            if CHAT_ID:
                bot.send_message(CHAT_ID, "⚠️ Google acessado, mas sem manchetes legíveis.")

    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")

if __name__ == "__main__":
    verificar()
