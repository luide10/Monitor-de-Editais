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

def analisar_noticia(titulo, link):
    prompt = f"""
    Você é um assistente de carreira e oportunidades públicas.
    Analise este título encontrado no Portal do Servidor da Bahia:
    '{titulo}'
    Link: {link}
    
    Responda EXATAMENTE neste formato resumido para Telegram:
    📢 **NOVIDADE NO RADAR!**
    🏷️ **Tópico:** [Ex: Vaga, Curso, Estágio, Benefício]
    📝 **O que é:** [Explique em 1 frase curta]
    💡 **Interessa?** [Diga por que isso é útil]
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Erro na análise de IA."

def verificar():
    print("--- Iniciando varredura por Oportunidades Úteis ---")
    
    # Portal de Notícias do Servidor (Agregador de oportunidades)
    url = "https://www.ba.gov.br/servidores"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Pega as manchetes (H2 e H3 são os padrões de título desse site)
        noticias = soup.find_all(['h2', 'h3'])
        
        # LISTA EXPANDIDA: Agora pega Cursos, Estágios e Benefícios também
        keywords = [
            'REDA', 'SELEÇÃO', 'CONCURSO', 'INSCRIÇÃO', 'EDITAL', 
            'ESTÁGIO', 'CURSO', 'CAPACITAÇÃO', 'PRÊMIO', 'CONVOCAÇÃO',
            'MATRÍCULA', 'BOLSA', 'TECNOLOGIA'
        ]
        
        encontrou = False
        
        # Analisa as 10 primeiras manchetes para aumentar a chance de achar algo útil agora
        for item in noticias[:10]:
            texto = item.get_text().strip()
            link_tag = item.find('a')
            
            if link_tag:
                link = link_tag['href']
                # Corrige link se vier cortado
                if not link.startswith('http'): 
                    link = 'https://www.ba.gov.br' + link
                
                # Se tiver qualquer uma das palavras chaves, MANDA!
                if any(k in texto.upper() for k in keywords):
                    print(f"✅ Encontrado: {texto}")
                    encontrou = True
                    
                    # Chama a IA para resumir
                    analise = analisar_noticia(texto, link)
                    msg = f"{analise}\n\n🔗 {link}"
                    
                    # Envia para o Canal
                    if CHAT_ID and CHAT_ID != '0':
                        try:
                            bot.send_message(CHAT_ID, msg)
                        except Exception as e:
                            print(f"Erro Telegram: {e}")
                    else:
                        print(f"Simulação de Envio:\n{msg}")

        if not encontrou:
            print("Nenhuma palavra-chave encontrada nas manchetes de hoje.")

    except Exception as e:
        print(f"Erro geral: {e}")

if __name__ == "__main__":
    verificar()
