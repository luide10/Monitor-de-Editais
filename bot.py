import os
import telebot
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import urllib3
from urllib.parse import unquote

# Configurações iniciais
urllib3.disable_warnings()
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
CHAT_ID = os.environ.get('MEU_CHAT_ID')

# Configura as IAs
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')
bot = telebot.TeleBot(TELEGRAM_TOKEN)

def limpar_link_google(link_sujo):
    """Remove o redirecionamento do Google e deixa o link limpo"""
    try:
        if "url=" in link_sujo:
            parte_importante = link_sujo.split("url=")[1]
            if "&" in parte_importante:
                url_codificada = parte_importante.split("&")[0]
            else:
                url_codificada = parte_importante
            return unquote(url_codificada)
        return link_sujo
    except:
        return link_sujo

def analisar_com_ia(titulo):
    """Pede para a IA resumir o título de forma atraente"""
    try:
        prompt = f"""
        Aja como um recrutador. Resuma esta oportunidade em UMA frase curta e impactante com emojis: 
        '{titulo}'
        """
        return model.generate_content(prompt).text
    except:
        return "📢 Nova oportunidade detectada!"

def verificar():
    print("--- INICIANDO VARREDURA (MODO PRODUÇÃO) ---", flush=True)
    
    # Busca focada em editais recentes no domínio do governo
    # Filtra por REDA, Processo Seletivo ou Inscrições Abertas
    url = "https://www.google.com/search?q=site:ba.gov.br+(REDA+OR+%22Processo+Seletivo%22+OR+%22Inscrições+Abertas%22)&tbm=nws&sort=date"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Timeout de 15s para não travar
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Pega os resultados (Google News usa h3 ou div heading)
        resultados = soup.find_all('div', role='heading')
        if not resultados:
            resultados = soup.find_all('h3')

        encontrou_algo = False
        count = 0
        
        # Analisa os 5 primeiros resultados para garantir relevância
        for item in resultados:
            titulo = item.get_text().strip()
            
            # Pula títulos inúteis ou curtos
            if len(titulo) < 10 or "Portal" in titulo: continue

            parent = item.find_parent('a')
            if not parent or 'href' not in parent.attrs: continue
            
            raw_link = parent['href']
            link_limpo = limpar_link_google(raw_link)

            # FILTRO DE SEGURANÇA: Só manda se for site oficial do governo da Bahia
            if ".ba.gov.br" not in link_limpo:
                continue

            print(f"🔎 Processando: {titulo}")
            
            # Gera o resumo com IA
            resumo = analisar_com_ia(titulo)

            # Monta a mensagem final "Gatinha"
            msg = (
                f"🤖 **NOVIDADE NO RADAR**\n\n"
                f"{resumo}\n\n"
                f"📰 **Fonte:** {titulo}\n"
                f"🔗 {link_limpo}"
            )
            
            if CHAT_ID:
                try:
                    bot.send_message(CHAT_ID, msg)
                    print("✅ Enviado para o canal.")
                    encontrou_algo = True
                    count += 1
                except Exception as e:
                    print(f"Erro Telegram: {e}")
            
            # Limite de segurança: Manda no máximo 3 notícias por vez para não fazer spam
            if count >= 3: 
                break 

        if not encontrou_algo:
            print("Nenhuma novidade relevante encontrada nesta rodada.")

    except Exception as e:
        print(f"❌ Erro na execução: {e}")

if __name__ == "__main__":
    verificar()
