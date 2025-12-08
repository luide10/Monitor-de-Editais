import os
import telebot
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import urllib3
from urllib.parse import unquote # Ferramenta para limpar a bagunça do link

# Configurações iniciais
urllib3.disable_warnings()
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
CHAT_ID = os.environ.get('MEU_CHAT_ID')

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')
bot = telebot.TeleBot(TELEGRAM_TOKEN)

def limpar_link_google(link_sujo):
    """
    Transforma aquele link ridículo do Google (/url?q=...) em um link bonito.
    """
    try:
        # O link real geralmente vem depois de "url="
        if "url=" in link_sujo:
            # Pega tudo que vem depois do "url="
            parte_importante = link_sujo.split("url=")[1]
            
            # O link termina quando começa o próximo parâmetro (geralmente um "&")
            if "&" in parte_importante:
                url_codificada = parte_importante.split("&")[0]
            else:
                url_codificada = parte_importante
            
            # Traduz os códigos de internet (%3A, %2F) para texto normal (:, /)
            return unquote(url_codificada)
            
        return link_sujo # Se não achar o padrão, devolve como tá
    except:
        return link_sujo

def verificar():
    print("--- INICIANDO SISTEMA VIA GOOGLE V2 ---", flush=True)
    
    # BUSCA MELHORADA: Procura termos exatos de seleção na Bahia
    url = "https://www.google.com/search?q=site:ba.gov.br+(REDA+OR+%22Processo+Seletivo%22+OR+Inscrições)&tbm=nws&sort=date"
    
    print(f"📡 Consultando o Google...", flush=True)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Procura os títulos (o Google usa h3 ou div role='heading')
        resultados = soup.find_all('div', role='heading')
        if not resultados:
            resultados = soup.find_all('h3')

        encontrou_algo = False
        count = 0
        
        # Analisa os 5 primeiros resultados
        for item in resultados:
            titulo = item.get_text().strip()
            
            # Pula títulos inúteis
            if len(titulo) < 10 or "Portal" in titulo: continue

            parent = item.find_parent('a')
            if not parent or 'href' not in parent.attrs: continue
            
            raw_link = parent['href']
            
            # A MÁGICA ACONTECE AQUI: Limpa o link
            link_limpo = limpar_link_google(raw_link)

            # Filtro de segurança: Só aceita se for site .ba.gov.br mesmo
            if ".ba.gov.br" not in link_limpo:
                continue

            print(f"🔎 Encontrei: {titulo}")
            
            # Chama a IA para fazer um resumo bonito
            try:
                prompt = f"Resuma esta oportunidade de concurso/seleção em 1 frase curta com emojis: '{titulo}'"
                resumo = model.generate_content(prompt).text
            except:
                resumo = "Oportunidade detectada!"

            msg = (
                f"🤖 **NOVIDADE ENCONTRADA**\n"
                f"{resumo}\n\n"
                f"📰 **Manchete:** {titulo}\n"
                f"🔗 {link_limpo}"
            )
            
            if CHAT_ID:
                try:
                    bot.send_message(CHAT_ID, msg)
                    encontrou_algo = True
                    count += 1
                except Exception as e:
                    print(f"Erro Telegram: {e}")
            
            if count >= 1: break # Manda só 1 pra testar e não floodar

        if not encontrou_algo:
            print("Google acessado, mas nenhum edital relevante encontrado na primeira página.")

    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")

if __name__ == "__main__":
    verificar()
