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
MODO_TESTE = os.environ.get('MODO_TESTE', 'false').lower() == 'true'

PALAVRAS_CHAVE = [
    "concurso", "edital", "reda", "processo seletivo", "vaga", 
    "policia", "polícia", "militar", "civil", "federal", 
    "cientifica", "científica", "portuaria", "portuária", 
    "perito", "investigador", "delegado", "soldado"
]

# Configura a API
genai.configure(api_key=GOOGLE_API_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)
ARQUIVO_HISTORICO = "historico_enviados.txt"

# --- 2. FUNÇÃO MÁGICA DE SELEÇÃO DE MODELO ---
def configurar_modelo_automatico():
    """
    Pergunta ao Google quais modelos estão disponíveis para esta Chave API
    e escolhe o melhor automaticamente para evitar Erro 404.
    """
    print("🔍 Buscando modelos disponíveis para sua Chave API...")
    try:
        # Lista todos os modelos que sua chave tem acesso
        modelos_disponiveis = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                modelos_disponiveis.append(m.name)
        
        print(f"📋 Modelos encontrados: {modelos_disponiveis}")

        # Tenta achar o melhor na ordem de preferência
        preferencias = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro', 'models/gemini-1.0-pro']
        
        modelo_escolhido = None
        
        # 1. Tenta achar um dos preferidos na lista
        for pref in preferencias:
            if pref in modelos_disponiveis:
                modelo_escolhido = pref
                break
        
        # 2. Se não achar nenhum preferido, pega o primeiro que tiver 'gemini' no nome
        if not modelo_escolhido:
            for m in modelos_disponiveis:
                if 'gemini' in m:
                    modelo_escolhido = m
                    break
        
        # 3. Se deu tudo errado, tenta forçar o flash
        if not modelo_escolhido:
            modelo_escolhido = 'gemini-1.5-flash'

        print(f"✅ MODELO SELECIONADO: {modelo_escolhido}")
        
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        return genai.GenerativeModel(modelo_escolhido, safety_settings=safety_settings)

    except Exception as e:
        print(f"❌ Erro ao listar modelos (Usando fallback): {e}")
        return genai.GenerativeModel('gemini-1.5-flash')

# Inicializa o modelo usando a função automática
model = configurar_modelo_automatico()

# --- 3. FUNÇÕES DE SUPORTE ---

def carregar_historico():
    if MODO_TESTE: return set()
    try:
        with open(ARQUIVO_HISTORICO, "r") as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()

def salvar_historico(link):
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
        if response.prompt_feedback.block_reason:
            return "⚠️ A IA bloqueou o conteúdo por segurança."
        return response.text
    except Exception as e:
        print(f"❌ [ERRO IA] {e}")
        # Se der erro, tenta listar os modelos de novo no log para debug
        return f"⚠️ **Erro Técnico na IA**\nO modelo falhou. Verifique os logs do GitHub.\nErro: {str(e)[:100]}"

def enviar_telegram(mensagem, link):
    try:
        prefixo = "🧪 [TESTE]\n" if MODO_TESTE else ""
        if not mensagem: mensagem = "⚠️ Erro: Mensagem vazia."
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

# --- 4. MOTORES ---

def processar_rss(url_rss, nome_motor):
    horas_filtro = 24 if MODO_TESTE else 3
    print(f"--- 📡 Motor: {nome_motor} (Janela: {horas_filtro}h | Teste: {MODO_TESTE}) ---")
    
    feed = feedparser.parse(url_rss)
    enviados = carregar_historico()
    agora = datetime.now()
    margem = agora - timedelta(hours=horas_filtro)
    
    count = 0
    for entry in feed.entries:
        link = entry.link
        if not MODO_TESTE and link in enviados: continue

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
    print(f"🚀 Monitor Iniciado (v3.0 Auto-Fix)")
    rss_geral = "https://news.google.com/rss/search?q=concurso+bahia+OR+policia+bahia+OR+reda+bahia&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    rss_gov = "https://news.google.com/rss/search?q=site:ba.gov.br+(reda+OR+processo+seletivo+OR+edital)&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    processar_rss(rss_geral, "Geral")
    processar_rss(rss_gov, "Governo")
    print("🏁 Fim.")

if __name__ == "__main__":
    main()
