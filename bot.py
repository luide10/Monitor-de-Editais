import os
import telebot
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

# Pega as senhas do cofre do GitHub
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
CHAT_ID = os.environ.get('MEU_CHAT_ID')

# Configurações
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')
bot = telebot.TeleBot(TELEGRAM_TOKEN)

def verificar():
    print("--- Iniciando Diagnóstico de Visão ---")
    url = "https://www.ba.gov.br/servidores"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Pega as manchetes
        noticias = soup.find_all(['h2', 'h3'])
        
        if len(noticias) > 0:
            # --- BLOCO DE DIAGNÓSTICO (Força o envio da primeira notícia) ---
            primeira_manchete = noticias[0].get_text().strip()
            
            # Monta uma mensagem de status
            msg_status = (
                f"🤖 **STATUS DO SISTEMA: ONLINE**\n"
                f"✅ Conexão com site: OK\n"
                f"👀 Manchetes lidas: {len(noticias)}\n\n"
                f"📰 **Manchete mais recente na capa:**\n"
                f"_{primeira_manchete}_\n\n"
                f"(O bot continua monitorando vagas em segundo plano...)"
            )
            
            # Envia para o canal para provar que está vendo
            try:
                if CHAT_ID and CHAT_ID != '0':
                    bot.send_message(CHAT_ID, msg_status, parse_mode='Markdown')
                    print("Mensagem de diagnóstico enviada!")
            except Exception as e:
                print(f"Erro ao enviar diagnóstico: {e}")
            # -------------------------------------------------------------

        # Agora continua a verificação normal de vagas (seu código antigo)
        keywords = ['REDA', 'SELEÇÃO', 'CONCURSO', 'INSCRIÇÃO', 'EDITAL', 'ESTÁGIO', 'CURSO']
        
        for item in noticias[:10]:
            texto = item.get_text().strip()
            link_tag = item.find('a')
            
            if link_tag:
                link = link_tag['href']
                if not link.startswith('http'): link = 'https://www.ba.gov.br' + link
                
                # Só manda a análise detalhada SE for uma das palavras chaves
                if any(k in texto.upper() for k in keywords):
                    # Lógica de análise aqui (simplificada para não duplicar código)
                    print(f"Vaga encontrada: {texto}")
                    # Se quiser ativar o envio das vagas também, descomente as linhas de envio normal

    except Exception as e:
        print(f"Erro: {e}")
        # Se der erro, avisa no log
        if CHAT_ID:
            bot.send_message(CHAT_ID, f"⚠️ Erro ao acessar o site: {e}")

if __name__ == "__main__":
    verificar()
