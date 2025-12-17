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

genai.configure(api_key=GOOGLE_API_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)
ARQUIVO_HISTORICO = "historico_enviados.txt"

# --- 2. SELETOR DE MODELO BLINDADO ---
def configurar_modelo():
    print("🔍 Configurando IA (Buscando modelo estável)...")
    
    # LISTA DE PRIORIDADE ATUALIZADA
    # Removemos as versões 2.0/2.5 (cota baixa) e priorizamos os "latest"
    preferencias = [
        'models/gemini-flash-latest',   # Geralmente aponta para 1.5 Flash (Cota Alta)
        'models/gemini-1.5-flash',
        'models/gemini-1.5-flash-001',
        'models/gemini-1.5-flash-8b',
        'models/gemini-pro',            # Clássico estável
        'models/gemini-1.0-pro'
    ]
    
    try:
        # Pega a lista real do Google
        todos_modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        modelo_escolhido = None

        # Tenta achar um da nossa lista de preferidos
        for pref in preferencias:
            if pref in todos_modelos:
                modelo_escolhido = pref
                break
        
        # Se não achar nenhum dos preferidos, tenta um fallback seguro
        if not modelo_escolhido:
            # Evita pegar modelos experimentais (exp) ou previews numéricos altos se possível
            for m in todos_modelos:
                if 'gemini' in m and 'flash' in m and 'exp' not in m and '2.' not in m:
                    modelo_escolhido = m
                    break
        
        # Se ainda assim não achar, pega o primeiro que tiver gemini
        if not modelo_escolhido:
             for m in todos_modelos:
                if 'gemini' in m:
                    modelo_escolhido = m
                    break

        print(f"✅ MODELO DEFINIDO: {modelo_escolhido}")
        
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        return genai.GenerativeModel(modelo_escolhido, safety_settings=safety_settings)

    except Exception as e:
        print(f"⚠️ Erro ao listar modelos: {e}. Forçando gemini-flash-latest.")
        return genai.GenerativeModel('gemini-flash-latest')

model = configurar_modelo()

# --- 3. FUNÇÕES ---

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
    print(f"🧠 [IA] Analisando: {titulo}")
    prompt = f"""
    Aja como especialista em concursos. Analise:
    FONTE: {fonte}
    TÍTULO: {titulo}
    TEXTO: {texto_site}
    
    Responda EXATAMENTE neste formato:
    📢 **ALERTA ({fonte})**
    🏢 **Órgão:** [Nome]
    💼 **Cargo:** [Cargos]
    🏛️ **Banca:** [Nome]
    📝 **Redação:** [Sim/Não]
    🎯 **Resumo:** [1 frase]
    """
    
    # TENTATIVA COM RETRY (TEIMOSIA)
    tentativas = 0
    max_tentativas = 3
    
    while tentativas < max_tentativas:
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            erro_str = str(e)
            # Se for erro de cota (429), espera e tenta de novo
            if "429" in erro_str or "quota" in erro_str.lower():
                print(f"⏳ Cota excedida (429). Esperando 60s... (Tentativa {tentativas+1}/{max_tentativas})")
                time.sleep(60) 
                tentativas += 1
            # Se for erro 404 (Modelo não encontrado), aborta logo
            elif "404" in erro_str:
                 print(f"❌ Erro 404 (Modelo não existe).")
                 return f"⚠️ Erro Técnico: Modelo IA não encontrado."
            else:
                print(f"❌ Erro IA: {e}")
                return f"⚠️ Erro técnico na IA: {str(e)[:100]}"
    
    return "⚠️ IA indisponível após várias tentativas (Cota estourada)."

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

# --- 4. MOTOR ---

def processar_rss(url_rss, nome_motor):
    horas_filtro = 24 if MODO_TESTE else 3
    print(f"--- 📡 Motor: {nome_motor} (Janela: {horas_filtro}h) ---")
    
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
                print(f"🔎 Achou: {entry.title}")
                texto = extrair_texto(link)
                analise = analisar_com_ia(entry.title, texto, link, nome_motor)
                enviar_telegram(analise, link)
                salvar_historico(link)
                enviados.add(link)
                
                # Pausa padrão
                time.sleep(10)
                count += 1
    print(f"   > Fim {nome_motor}: {count} itens.")

def main():
    print(f"🚀 Monitor V5 (Lista Prioritária)")
    rss_geral = "https://news.google.com/rss/search?q=concurso+bahia+OR+policia+bahia+OR+reda+bahia&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    rss_gov = "https://news.google.com/rss/search?q=site:ba.gov.br+(reda+OR+processo+seletivo+OR+edital)&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    processar_rss(rss_geral, "Geral")
    processar_rss(rss_gov, "Governo")
    print("🏁 Fim.")

if __name__ == "__main__":
    main()
