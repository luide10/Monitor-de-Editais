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

def analisar_edital(titulo, link):
    prompt = f"""
    Você é um assistente de carreira. Analise este título de vaga pública na Bahia:
    '{titulo}'
    Link: {link}

    Responda EXATAMENTE neste formato:
    📢 **ALERTA DE VAGA**
    🏢 **Órgão:** [Nome]
    💼 **Área:** [Áreas principais]
    🤖 **Serve para TI/Gestão?** [Sim/Não/Talvez]
    💡 **Resumo:** [Explicação em 1 frase]
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Erro na análise de IA."

def verificar():
    print("--- Iniciando verificação ---")
    # Site de notícias do servidor
    url = "https://www.ba.gov.br/servidores"

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Pega as manchetes
        noticias = soup.find_all(['h2', 'h3'])

        keywords = ['REDA', 'SELEÇÃO', 'CONCURSO', 'INSCRIÇÃO', 'EDITAL']

        encontrou = False

        # Verifica as 5 primeiras
        for item in noticias[:5]:
            texto = item.get_text().strip()
            link_tag = item.find('a')

            if link_tag:
                link = link_tag['href']
                if not link.startswith('http'): link = 'https://www.ba.gov.br' + link

                if any(k in texto.upper() for k in keywords):
                    print(f"Encontrado: {texto}")
                    encontrou = True

                    analise = analisar_edital(texto, link)
                    msg = f"{analise}\n\n🔗 {link}"

                    if CHAT_ID and CHAT_ID != '0':
                        bot.send_message(CHAT_ID, msg)
                    else:
                        print("ID não configurado ou mensagem enviada para o log.")

        if not encontrou:
            print("Nenhuma vaga encontrada nas manchetes recentes.")

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    verificar()