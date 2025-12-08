import os
import telebot
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import urllib3

# Desabilita avisos de segurança para garantir acesso ao site do governo
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Pega as senhas
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
CHAT_ID = os.environ.get('MEU_CHAT_ID')

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')
bot = telebot.TeleBot(TELEGRAM_TOKEN)

def verificar():
    print("--- Acessando Portal RH BAHIA ---")
    
    # URL CORRIGIDA: Este é o site onde as notícias realmente estão
    url = "https://servidores.rhbahia.ba.gov.br/"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        # verify=False ajuda a pular bloqueios de certificado do governo
        response = requests.get(url, headers=headers, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Nesse portal novo, as manchetes podem estar em links diretos (a) dentro de destaques
        # Vamos pegar textos de links que tenham tamanho razoável
        elementos = soup.find_all('a')
        
        manchetes_encontradas = []
        
        # Filtra apenas textos que pareçam manchetes (mais de 20 letras)
        for item in elementos:
            texto = item.get_text().strip()
            if len(texto) > 25:
                manchetes_encontradas.append(texto)

        # --- DIAGNÓSTICO VISUAL (PROVA DE VIDA) ---
        if len(manchetes_encontradas) > 0:
            primeira = manchetes_encontradas[0] # Pega a primeira que achou
            
            msg = (
                f"🤖 **DIAGNÓSTICO: AGORA FOI!**\n"
                f"Acessei: RH Bahia\n"
                f"Manchetes lidas: {len(manchetes_encontradas)}\n\n"
                f"📰 **Destaque da Capa:**\n"
                f"_{primeira}_"
            )
            
            if CHAT_ID:
                try:
                    bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
                    print("✅ Diagnóstico enviado para o canal!")
                except Exception as e:
                    print(f"Erro ao enviar: {e}")
            return # Para o teste aqui para não flodar
        else:
            print("Ainda não achei textos longos. A estrutura pode ser diferente.")
            # Se não achou links, tenta procurar parágrafos de destaque
            destaques = soup.find_all('p')
            if len(destaques) > 0:
                 print(f"Achei parágrafos: {destaques[0].get_text()}")

    except Exception as e:
        print(f"Erro Crítico: {e}")
        if CHAT_ID:
            bot.send_message(CHAT_ID, f"Erro técnico: {e}")

if __name__ == "__main__":
    verificar()
