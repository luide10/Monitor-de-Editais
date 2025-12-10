# 🤖 Monitor Inteligente de Concursos & REDA - Bahia

![Status](https://img.shields.io/badge/Status-Operacional-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![AI](https://img.shields.io/badge/AI-Google%20Gemini-orange)
![Pipeline](https://img.shields.io/badge/Pipeline-GitHub%20Actions-blueviolet)

> **"O Detetive de Editais": Monitoramento Autônomo com Análise de IA**

Este projeto é um agente de software autônomo focado em encontrar oportunidades de **Concursos Públicos (Polícias, Administrativo, Tribunais)** e vagas **REDA** no estado da Bahia. 

Diferente de bots comuns que apenas repassam links, este sistema **lê a notícia/edital** e utiliza **Inteligência Artificial (LLM)** para extrair dados técnicos vitais (Banca, Disciplinas, Redação) antes de notificar o usuário.

---

## 🚀 Diferenciais da Versão 2.0

O sistema evoluiu para uma arquitetura híbrida de monitoramento:

* 🌐 **Motor de Busca Híbrido:**
    * **Google News RSS:** Monitora em tempo real jornais, blogs de cursinhos e portais de notícias para pegar furos sobre Polícia Militar, Civil e Federal.
    * **Crawler Oficial:** Monitoramento direto no portal `ba.gov.br` para garantir vagas de REDA e seleções internas que o Google demora a indexar.
* 🧠 **Deep Reading com IA:** O bot entra no link, faz o *scraping* do texto completo e envia para o Google Gemini responder:
    * *Qual é a Banca? (FGV, Cebraspe, etc)*
    * *Tem prova de Redação?*
    * *Quais as matérias principais?*
* ⏱️ **Filtro Temporal Inteligente:** No ambiente Serverless (GitHub Actions), o bot calcula o "delta" de tempo para processar apenas notícias das últimas 3 horas, evitando spam e duplicidade.
* ☁️ **Serverless & Free:** Roda via Cron Job no GitHub Actions, sem custos de servidor.

## 🛠️ Arquitetura da Solução

O fluxo de dados utiliza múltiplos extratores convergindo para um único analista de IA:

```mermaid
graph TD
    A[🕒 Cron Job GitHub Actions] -->|A cada 2h| B[🚀 Iniciar Bot]
    
    subgraph "Motores de Busca"
    B -->|Busca Ampla| C[📰 Google News RSS]
    B -->|Busca Oficial| D[🏛️ Portal BA.GOV]
    end
    
    C -->|Link Encontrado| E[🕷️ Web Scraper]
    D -->|Link Encontrado| E
    
    E -->|Texto Bruto da Notícia| F[🧠 Google Gemini AI]
    
    F -->|Extração de Entidades| G{Dados Técnicos}
    G -- Banca, Matérias, Redação --> H[📢 Telegram Bot]
