import os
import telebot
import google.generativeai as genai
import feedparser
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

# --- 1. CONFIGURAÇÕES ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
CHAT_ID = os.environ.get('MEU_CHAT_ID')

# Captura se o Modo Teste foi ativado no GitHub (Vem como string 'true')
MODO_TESTE = os.environ.get('MODO_TESTE', 'false').lower() == 'true'

PALAVRAS_CHAVE = [
    "concurso", "edital", "reda", "processo seletivo", "vaga", 
    "policia", "polícia", "militar", "civil", "federal", 
    "cientifica", "científica", "portuaria", "portuária", 
    "perito", "investigador", "delegado", "soldado"
]

# --- CONFIGURAÇÃO DA IA ---
genai.configure(api_key=GOOGLE_API_KEY)
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]
model = genai.GenerativeModel('gemini-1.5-flash', safety_settings=safety_settings)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

ARQUIVO_HISTORICO = "historico_enviados.txt"

# --- 2. FUNÇÕES ---

def carregar_historico():
    # Se estiver em modo teste, ignoramos o histórico para forçar reenvio!
    if MODO_TESTE:
        print("⚠️ MODO TESTE ATIVO: Ignorando histórico para reenviar mensagens.")
        return set()
    
    try:
        with open(ARQUIVO_HISTORICO, "r") as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()

def salvar_historico(link):
    # No modo teste, a gente não salva para não sujar o histórico real
    if not MODO_TESTE:
        with open(ARQUIVO_HISTORICO, "a") as f:
            f.write(f"{link}\n")

def analisar_com_ia(titulo, texto_site, link, fonte):
    print(f"🧠 [DEBUG] Enviando para IA: {titulo}")
    prompt = f"""
    Aja como um especialista em concursos públicos. Analise:
    FONTE: {fonte}
    TÍTULO: {titulo}
    TEXTO: {texto_site}
    
    Responda EXATAMENTE neste formato (se faltar info, preencha "Não informado"):
    📢 **ALERTA ({fonte})**
    🏢 **Órgão:** [Nome]
    💼 **Cargo:** [Cargos]
    🏛️ **Banca:** [Nome]
    📝 **Redação:** [Sim/Não]
    🎯 **Resumo:** [1 frase]
    """
    try:
        response = model.generate_content(prompt)
        print(f"🤖 [DEBUG] Resposta IA: {response.text[:100]}...") 
        return response.text
    except Exception as e:
        print(f"❌ [ERRO IA] {e}")
        return f"⚠️ **Erro na Análise IA**\nErro: {e}"

def enviar_telegram(mensagem, link):
    try:
        prefixo = "🧪 [TESTE DE FORMATAÇÃO]\n" if MODO_TESTE else ""
        msg_final = f"{prefixo}{mensagem}\n\n🔗 **Link:** {link}"
        
        bot.send_message(CHAT_ID, msg_final, parse_mode="Markdown")
        print("✅ Enviado Telegram!")
    except Exception as e:
        print(f"❌ Erro Telegram: {e}")

def extrair_texto(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.content, 'html.parser')
        return soup.get_text(" ", strip=True)[:4000]
    except:
        return "Texto inacessível."

# --- 3. MOTOR ---

def processar_rss(url_rss, nome_motor):
    # SE FOR MODO TESTE: Pega últimas 24h. SE FOR NORMAL: Pega 3h.
    horas_filtro = 24 if MODO_TESTE else 3
    
    print(f"--- 📡 Motor: {nome_motor} (Janela: {horas_filtro}h | Teste: {MODO_TESTE}) ---")
    
    feed = feedparser.parse(url_rss)
    enviados = carregar_historico()
    agora = datetime.now()
    margem = agora - timedelta(hours=horas_filtro)
    
    count = 0
    for entry in feed.entries:
        link = entry.link
        
        # Só pula se NÃO for teste E já estiver no histórico
        if not MODO_TESTE and link in enviados: 
            continue

        try:
            data_pub = parsedate_to_datetime(entry.published).replace(tzinfo=None)
        except:
            data_pub = agora 

        if data_pub > margem:
            if any(p in entry.title.lower() for p in PALAVRAS_CHAVE):
                print(f"🔎 Processando: {entry.title}")
                texto = extrair_texto(link)
                analise = analisar_com_ia(entry.title, texto, link, nome_motor)
                enviar_telegram(analise, link)
                
                salvar_historico(link)
                enviados.add(link)
                time.sleep(2)
                count += 1
    print(f"   > Fim {nome_motor}: {count} processados.")

def main():
    print(f"🚀 Monitor Iniciado (Modo Teste: {MODO_TESTE})")
    
    rss_geral = "https://news.google.com/rss/search?q=concurso+bahia+OR+policia+bahia+OR+reda+bahia&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    rss_gov = "https://news.google.com/rss/search?q=site:ba.gov.br+(reda+OR+processo+seletivo+OR+edital)&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    
    processar_rss(rss_geral, "Geral")
    processar_rss(rss_gov, "Governo")
    print("🏁 Fim.")

if __name__ == "__main__":
    main()
