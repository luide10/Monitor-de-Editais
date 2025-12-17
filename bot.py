import os
import telebot
import requests # Usaremos requests para falar com a IA diretamente
import feedparser
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

bot = telebot.TeleBot(TELEGRAM_TOKEN)
ARQUIVO_HISTORICO = "historico_enviados.txt"

# --- 2. INTELIGÊNCIA ARTIFICIAL (VIA HTTP DIRETO) ---
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

    # Lista de modelos para tentar via URL direta
    modelos = [
        "gemini-1.5-flash",      # O Trator (Cota Alta)
        "gemini-1.5-flash-8b",   # Versão leve
        "gemini-1.5-pro",        # Versão potente
        "gemini-2.0-flash-exp"   # Versão nova (Cota baixa)
    ]

    for modelo in modelos:
        try:
            # URL Mágica da API REST do Google
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={GOOGLE_API_KEY}"
            
            # O "Pacote" JSON que enviamos
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "safetySettings": [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                ]
            }
            
            headers = {'Content-Type': 'application/json'}
            
            # Envia a requisição
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            # Verifica se deu certo (Código 200 = OK)
            if response.status_code == 200:
                dados = response.json()
                try:
                    # Tenta pegar o texto da resposta
                    texto_resposta = dados['candidates'][0]['content']['parts'][0]['text']
                    return texto_resposta
                except (KeyError, IndexError):
                    # Se a resposta veio vazia ou bloqueada
                    print(f"⚠️ Modelo {modelo} respondeu mas sem texto (Bloqueio?).")
                    continue
            
            elif response.status_code == 429:
                print(f"⏳ Cota cheia no {modelo} (429). Tentando próximo...")
                time.sleep(1)
                continue
            
            elif response.status_code == 404:
                print(f"⚠️ Modelo {modelo} não encontrado na API (404).")
                continue
                
            else:
                print(f"❌ Erro HTTP {response.status_code} no modelo {modelo}: {response.text}")
                continue
            
        except Exception as e:
            print(f"❌ Erro de conexão com {modelo}: {e}")
            continue

    print("❌ Todos os modelos falharam.")
    return None

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

def enviar_telegram(mensagem_ia, link, titulo_original):
    try:
        prefixo = "🧪 [TESTE]\n" if MODO_TESTE else ""
        
        if mensagem_ia:
            msg_final = f"{prefixo}{mensagem_ia}\n\n🔗 **Link:** {link}"
        else:
            msg_final = (
                f"{prefixo}📢 **ALERTA DE OPORTUNIDADE**\n\n"
                f"📌 **Título:** {titulo_original}\n"
                f"⚠️ _IA indisponível (Fallback), acesse o link:_\n\n"
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

# --- 4. MOTOR DE BUSCA ---

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
                enviar_telegram(analise, link, entry.title)
                
                salvar_historico(link)
                enviados.add(link)
                time.sleep(15) 
                count += 1
    print(f"   > Fim {nome_motor}: {count} itens.")

def main():
    print(f"🚀 Monitor V10 (Direct HTTP - No SDK)")
    
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
