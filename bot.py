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

# Palavras para validação final
PALAVRAS_CHAVE = [
    "concurso", "edital", "reda", "processo seletivo", "vaga", 
    "policia", "polícia", "militar", "civil", "federal", 
    "cientifica", "científica", "portuaria", "portuária", 
    "perito", "investigador", "delegado", "soldado"
]

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
bot = telebot.TeleBot(TELEGRAM_TOKEN)

ARQUIVO_HISTORICO = "historico_enviados.txt"

# --- 2. FUNÇÕES ÚTEIS ---

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
    TEXTO (Resumo): {texto_site}
    
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

def extrair_texto(url):
    """Tenta pegar o texto real da página. Se falhar, retorna vazio."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.content, 'html.parser')
        return soup.get_text(" ", strip=True)[:3000]
    except:
        return "Texto não acessível, baseie-se no título."

# --- 3. MOTORES DE BUSCA (ESTRATÉGIA DUPLA RSS) ---

def processar_rss(url_rss, nome_motor, filtro_tempo_horas=3):
    """
    MODO PRODUÇÃO: filtro_tempo_horas definido para 3 horas.
    """
    print(f"--- 📡 Rodando Motor: {nome_motor} (Olhando últimas {filtro_tempo_horas}h) ---")
    
    feed = feedparser.parse(url_rss)
    enviados = carregar_historico()
    agora = datetime.now()
    
    # Janela de tempo curta para evitar repetições no GitHub Actions
    margem = agora - timedelta(hours=filtro_tempo_horas)
    
    contador = 0

    for entry in feed.entries:
        link = entry.link
        titulo = entry.title
        
        if link in enviados: continue

        try:
            data_pub = parsedate_to_datetime(entry.published).replace(tzinfo=None)
        except:
            data_pub = agora 

        # Se a notícia for recente (> 3h)
        if data_pub > margem:
            if any(p in titulo.lower() for p in PALAVRAS_CHAVE):
                print(f"   > Encontrado: {titulo}")
                
                texto = extrair_texto(link)
                analise = analisar_com_ia(titulo, texto, link, nome_motor)
                enviar_telegram(analise, link)
                
                salvar_historico(link)
                enviados.add(link)
                time.sleep(2)
                contador += 1
    
    print(f"   > {nome_motor} finalizado. {contador} novos itens processados.")

def main():
    print("🚀 Monitor de Editais Rodando (Modo Silencioso)")
    
    # MOTOR 1: Busca Geral (Jornais, Blogs, G1, etc)
    rss_geral = "https://news.google.com/rss/search?q=concurso+bahia+OR+policia+bahia+OR+reda+bahia&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    processar_rss(rss_geral, "Busca Geral Notícias")

    # MOTOR 2: Busca Cirúrgica no Governo
    rss_governo = "https://news.google.com/rss/search?q=site:ba.gov.br+(reda+OR+processo+seletivo+OR+edital)&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    processar_rss(rss_governo, "Raio-X Governo BA")

    print("🏁 Fim da execução.")

if __name__ == "__main__":
    main()
