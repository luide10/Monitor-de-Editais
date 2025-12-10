import os
import telebot
import google.generativeai as genai
import feedparser
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

# --- 1. CONFIGURAÇÕES E SEGREDOS ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
CHAT_ID = os.environ.get('MEU_CHAT_ID')

# Palavras que acionam o alerta
PALAVRAS_CHAVE = [
    "concurso", "edital", "reda", "processo seletivo", "vaga", 
    "policia", "polícia", "militar", "civil", "federal", 
    "cientifica", "científica", "portuaria", "portuária", 
    "perito", "investigador", "delegado", "soldado"
]

# Configuração dos Serviços
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
bot = telebot.TeleBot(TELEGRAM_TOKEN)

ARQUIVO_HISTORICO = "historico_enviados.txt"

# --- 2. FUNÇÕES DE SUPORTE (HISTÓRICO E IA) ---

def carregar_historico():
    try:
        with open(ARQUIVO_HISTORICO, "r") as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()

def salvar_historico(link):
    with open(ARQUIVO_HISTORICO, "a") as f:
        f.write(f"{link}\n")

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
        print("✅ Enviado Telegram!")
    except Exception as e:
        print(f"❌ Erro Telegram: {e}")

# --- 3. MOTORES DE BUSCA ---

def motor_google_news():
    print("--- 🌍 Verificando Google News... ---")
    url_rss = "https://news.google.com/rss/search?q=concurso+bahia+OR+policia+bahia+OR+reda+bahia+OR+edital+bahia&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    feed = feedparser.parse(url_rss)
    enviados = carregar_historico()
    
    # Filtro de tempo: Apenas notícias das últimas 3 horas
    agora = datetime.now()
    margem = agora - timedelta(hours=3)

    for entry in feed.entries:
        link = entry.link
        if link in enviados: continue

        titulo = entry.title
        
        # Tenta descobrir a data da notícia
        try:
            data_publicacao = parsedate_to_datetime(entry.published).replace(tzinfo=None)
        except:
            data_publicacao = agora 

        # Só processa se for RECENTE e tiver PALAVRA CHAVE
        if data_publicacao > margem:
            if any(p in titulo.lower() for p in PALAVRAS_CHAVE):
                
                # Extrai texto do site
                try:
                    resp = requests.get(link, timeout=10)
                    soup = BeautifulSoup(resp.content, 'html.parser')
                    texto = soup.get_text(" ", strip=True)[:3000]
                except:
                    texto = "Texto não acessível."
                
                analise = analisar_com_ia(titulo, texto, link, "Google News")
                enviar_telegram(analise, link)
                salvar_historico(link)
                enviados.add(link)
                time.sleep(2)

def motor_ba_gov():
    print("--- 🏛️ Verificando BA.GOV (Modo Varredura de Links)... ---")
    url = "https://www.ba.gov.br/servidores"
    
    try:
        # User-Agent fingindo ser um Chrome comum para não tomar bloqueio
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Status da conexão: {response.status_code}") # Espero ver 200 aqui

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # AGORA PEGANDO TODOS OS LINKS, NÃO SÓ MANCHETES
        todos_links = soup.find_all('a')
        print(f"🔎 O Robô encontrou {len(todos_links)} links totais. Filtrando...")

        contagem = 0
        enviados = carregar_historico()

        for link_tag in todos_links:
            # Tenta pegar o texto visível ou o título do link
            texto = link_tag.get_text(" ", strip=True)
            if not texto:
                texto = link_tag.get('title', '')
            
            url_destino = link_tag.get('href')
            
            # Validação básica
            if not texto or not url_destino:
                continue

            # Corrige link relativo (ex: /noticia-tal vira ba.gov.br/noticia-tal)
            if not url_destino.startswith('http'):
                url_destino = 'https://www.ba.gov.br' + url_destino

            # Verifica se já mandamos esse link antes
            if url_destino in enviados:
                continue

            # O FILTRO DE OURO: Verifica se tem nossas palavras-chave
            if any(p in texto.lower() for p in PALAVRAS_CHAVE):
                contagem += 1
                print(f"   > Candidato encontrado: {texto}")

                # Entra no link para ler o conteúdo completo
                try:
                    resp = requests.get(url_destino, headers=headers, timeout=10)
                    soup_d = BeautifulSoup(resp.content, 'html.parser')
                    texto_completo = soup_d.get_text(" ", strip=True)[:3000]
                except:
                    texto_completo = "Conteúdo não acessível."

                # Manda para a IA e depois pro Telegram
                analise = analisar_com_ia(texto, texto_completo, url_destino, "Portal BA.GOV")
                enviar_telegram(analise, url_destino)
                
                salvar_historico(url_destino)
                enviados.add(url_destino)
                time.sleep(2)
                
                # Limite de segurança para não mandar 50 mensagens de vez
                if contagem >= 5:
                    break
        
        if contagem == 0:
            print("   > Nenhum link relevante encontrado nesta varredura.")

    except Exception as e:
        print(f"Erro ao ler ba.gov: {e}")

# --- 4. EXECUÇÃO PRINCIPAL ---

def main():
    print("🚀 Execução Única Iniciada (GitHub Actions)")
    # Roda os dois motores sequencialmente
    motor_ba_gov()
    motor_google_news()
    print("🏁 Fim da execução.")

if __name__ == "__main__":
    main()
