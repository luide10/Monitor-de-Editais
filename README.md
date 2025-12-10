# 🤖 Monitor Inteligente de Concursos & REDA - Bahia

![Status](https://img.shields.io/badge/Status-Operacional-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![AI](https://img.shields.io/badge/AI-Google%20Gemini-orange)
![Pipeline](https://img.shields.io/badge/Pipeline-GitHub%20Actions-blueviolet)

> **"O Detetive de Editais": Monitoramento de Vagas com IA e Busca Avançada**

Este projeto é um agente autônomo focado em encontrar oportunidades de **Concursos Públicos** (Polícia, Tribunais, Administrativo) e vagas **REDA** (Regime Especial de Direito Administrativo) no estado da Bahia.

Diferente de bots comuns, este sistema utiliza uma **Estratégia de Busca Dupla (Dual-Search Engine)** para contornar limitações técnicas de sites governamentais e utiliza **Inteligência Artificial (LLM)** para ler e resumir os editais.

---

## 🚀 Destaques Técnicos & Soluções

O projeto resolveu desafios complexos de automação:

* 🛡️ **Bypass de Sites Dinâmicos (Anti-Scraping):** O portal oficial do governo utiliza renderização via JavaScript (React/Angular), o que bloqueia crawlers tradicionais. A solução implementada utiliza **Google Dorking via RSS** (`site:ba.gov.br`) para extrair os dados indexados diretamente do cache do Google, contornando a necessidade de navegadores pesados (Selenium/Puppeteer).
* 🧠 **Análise Cognitiva com Gemini:** Cada notícia encontrada é processada pela IA do Google, que estrutura os dados não-estruturados:
    * *Qual a Banca?*
    * *Tem Redação?*
    * *Resumo da vaga em 1 frase.*
* ⏱️ **Filtro Temporal de Produção:** No ambiente Serverless (GitHub Actions), o bot calcula janelas de tempo precisas (ex: últimas 3 horas) para evitar duplicidade de envio, já que não possui banco de dados persistente.
* ☁️ **Serverless & Free:** Roda via Cron Job no GitHub Actions, sem custos de servidor.

## 🛠️ Arquitetura da Solução

O sistema opera com dois motores de busca rodando em paralelo:

```mermaid
graph TD
    A["🕒 Cron Job (GitHub Actions)"] -->|A cada 2h| B["🚀 Iniciar Bot"]
    
    subgraph "Motores de Busca (RSS)"
    B -->|"Busca Ampla"| C["📡 Google News Geral"]
    B -->|"Busca Cirúrgica"| D["🎯 Google Index: site:ba.gov.br"]
    end
    
    C -->|"Notícias Recentes"| E["Filtro de Palavras-Chave"]
    D -->|"Editais Oficiais"| E
    
    E -->|"Texto Bruto"| F["🧠 Google Gemini AI"]
    
    F -->|"Dados Estruturados"| G{"Decisor"}
    G -- "Nova Oportunidade" --> H["📢 Telegram Bot"]
