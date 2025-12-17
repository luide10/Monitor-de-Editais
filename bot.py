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

# --- 2. NOVA INTELIGÊNCIA (TÁTICA DA METRALHADORA) ---
def tentar_gerar_conteudo(prompt):
    """
    Tenta vários modelos diferentes em sequência. 
    Se o 1.5 Flash falhar (404), tenta o Pro, depois o 1.0.
    """
    # Lista de nomes para tentar (do mais moderno para o mais antigo/estável)
    modelos_para_tentar = [
        'gemini-1.5-flash',
        'gemini-1.5-flash-001',
        'gemini-pro',
        'models/gemini-1.5-flash', # Tenta com prefixo também
        'models/gemini-pro'
    ]
    
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    for nome_modelo in modelos_para_tentar:
        try:
            # Configura o modelo da vez
            model = genai.GenerativeModel(nome_modelo, safety_settings=safety_settings)
            
            # Tenta gerar
            response = model.generate_content(prompt)
            
            # Se chegou aqui, funcionou! Retorna o texto.
            return response.text
            
        except Exception as e:
            erro = str(e)
            if "429" in erro:
                print(f"⏳ Cota estourada no modelo {nome_modelo}. Tentando próximo...")
                time.sleep(2) # Pequena pausa
            elif "404" in erro:
                print(f"⚠️ Modelo {nome_modelo} não encontrado (404). Tentando próximo...")
            else:
                print(f"❌ Erro no modelo {nome_modelo}: {erro}")
            
            # Se der erro, o loop continua para o próximo modelo da lista
            continue
            
    # Se sair do loop, todos falharam
    return None

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
    
    # Chama a função nova que tenta vários modelos
    resposta = tentar_gerar_conteudo(prompt)
    
    if resposta:
        return resposta
    else:
        print("❌ FALHA TOTAL: Nenhum modelo de IA funcionou.")
        return None

def enviar_telegram(mensagem_ia, link, titulo_original):
    try:
        prefixo = "🧪 [TESTE]\n" if MODO_TESTE else ""
        
        if mensagem_ia:
            msg_final = f"{prefixo}{mensagem_ia}\n\n🔗 **Link:** {link}"
        else:
            # FALLBACK FINAL: Se a IA falhar tudo, manda só o link
            msg_final = (
                f"{prefixo}📢 **ALERTA DE OPORTUNIDADE**\n\n"
                f"📌 **Título:** {titulo_original}\n"
                f"⚠️ _IA indisponível no momento, confira o link:_\n\n"
                f"🔗 **Link:** {link}"
            )

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
                
                # Análise inteligente
                analise = analisar_com_ia(entry.title, texto, link, nome_motor)
                
                # Envio
                enviar_telegram(analise, link, entry.title)
                
                salvar_historico(link)
                enviados.add(link)
                time.sleep(15) 
                count += 1
    print(f"   > Fim {nome_motor}: {count} itens.")

def main():
    print(f"🚀 Monitor V8 (Multi-Modelos)")
    
    rss_geral = "https://news.google.com/rss/search?q=concurso+bahia+OR+policia+bahia+OR+reda+bahia&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    rss_gov = "https://news.google.com/rss/search?q=site:ba.gov.br+(reda+OR+processo+seletivo+OR+edital)&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    rss_pci = "https://news.google.com/rss/search?q=site:pciconcursos.com.br+concurso+bahia&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    rss_folha = "https://news.google.com/rss/search?q=site:folha.qconcursos.com+concurso+bahia&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    rss_jc = "https://news.google.com/rss/search?q=site:jcconcursos.com.br+concurso+bahia&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    
    processar_rss(rss_gov, "Governo BA")
    processar_rss(rss_pci, "PCI Concursos")
    processar_rss(rss_folha, "Folha Dirigida")
    processar_rss(rss_jc, "JC Concursos")
    processar_rss(rss_geral, "Mídia Geral")
    
    print("🏁 Fim da Varredura.")

if __name__ == "__main__":
    main()
