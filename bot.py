import os
import telebot
import google.generativeai as genai
import feedparser
import requests
from bs4 import BeautifulSoup
<<<<<<< HEAD
import time
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

# --- CONFIGURAÇÕES ---
=======
import urllib3
from urllib.parse import unquote

# Configurações iniciais
urllib3.disable_warnings()
>>>>>>> 7bcb809c8e3f1eef30bae1b8b86ba044812c3cbd
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
CHAT_ID = os.environ.get('MEU_CHAT_ID')

<<<<<<< HEAD
PALAVRAS_CHAVE = [
    "concurso", "edital", "reda", "processo seletivo", "vaga", 
    "policia", "polícia", "militar", "civil", "federal", 
    "cientifica", "científica", "portuaria", "portuária", 
    "perito", "investigador", "delegado", "soldado"
]

=======
# Configura as IAs
>>>>>>> 7bcb809c8e3f1eef30bae1b8b86ba044812c3cbd
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
bot = telebot.TeleBot(TELEGRAM_TOKEN)

<<<<<<< HEAD
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
=======
def limpar_link_google(link_sujo):
    """Remove o redirecionamento do Google e deixa o link limpo"""
>>>>>>> 7bcb809c8e3f1eef30bae1b8b86ba044812c3cbd
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
<<<<<<< HEAD
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
=======
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
    
>>>>>>> 7bcb809c8e3f1eef30bae1b8b86ba044812c3cbd
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Timeout de 15s para não travar
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
<<<<<<< HEAD
        noticias = soup.find_all(['h2', 'h3'])
        
        # Analisa apenas as 3 primeiras manchetes para evitar spam de coisas velhas
        for item in noticias[:3]: 
            titulo = item.get_text().strip()
            link_tag = item.find('a')
            if link_tag:
                link = link_tag['href']
                if not link.startswith('http'): link = 'https://www.ba.gov.br' + link
                
                if any(p in titulo.lower() for p in PALAVRAS_CHAVE):
                    # Como esse site não tem data fácil, mandamos para a IA analisar
                    try:
                        resp = requests.get(link, headers=headers)
                        soup_d = BeautifulSoup(resp.content, 'html.parser')
                        texto = soup_d.get_text(" ", strip=True)[:3000]
                    except:
                        texto = "..."
                    
                    analise = analisar_com_ia(titulo, texto, link, "Portal BA.GOV")
                    enviar_telegram(analise, link)
                    time.sleep(2)
=======
        
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
>>>>>>> 7bcb809c8e3f1eef30bae1b8b86ba044812c3cbd

    except Exception as e:
        print(f"❌ Erro na execução: {e}")

def main():
    print("🚀 Execução Única Iniciada (GitHub Actions)")
    # Roda uma vez e para. O GitHub vai chamar de novo daqui a 2 horas.
    motor_ba_gov()
    motor_google_news()
    print("🏁 Fim da execução.")

if __name__ == "__main__":
<<<<<<< HEAD
    main()
=======
    verificar()
>>>>>>> 7bcb809c8e3f1eef30bae1b8b86ba044812c3cbd
