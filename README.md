# 🤖 Monitor de Editais & Oportunidades - Bahia

![Status](https://img.shields.io/badge/Status-Operacional-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![AI](https://img.shields.io/badge/AI-Google%20Gemini-orange)
![Pipeline](https://img.shields.io/badge/Pipeline-GitHub%20Actions-blueviolet)

> **Automação Inteligente para Monitoramento de Vagas e Processos Seletivos**

Este projeto é um **Agente Autônomo** desenvolvido para monitorar oportunidades públicas no Governo da Bahia (REDA, Estágios, Processos Seletivos). O sistema utiliza uma estratégia de **Search Scraping** para contornar bloqueios de região, sanitiza os dados e utiliza **Inteligência Artificial (LLM)** para resumir e notificar novas vagas em tempo real via Telegram.

---

## 🚀 Destaques Técnicos

O diferencial deste projeto é a resiliência e a capacidade de filtrar informações úteis:

* 🛡️ **Bypass de Firewall:** Utiliza consultas estruturadas no **Google Search** para acessar editais hospedados em servidores governamentais que bloqueiam requisições externas (GitHub Cloud), eliminando erros de *Timeout*.
* 🧹 **Sanitização de URLs:** Módulo dedicado para decodificar e limpar links de redirecionamento (`unquote`), garantindo acesso direto à fonte oficial.
* 🧠 **Análise Cognitiva:** Integração com a API **Google Gemini (GenAI)** para ler títulos técnicos e transformá-los em resumos atrativos para divulgação.
* ☁️ **Arquitetura Serverless:** Operação 100% em nuvem via **GitHub Actions** (Cron Jobs), sem custos de infraestrutura.

## 🛠️ Arquitetura da Solução

O fluxo de dados segue uma lógica de funil para garantir qualidade:

```mermaid
graph TD
    A[Cron Job (2h)] -->|Inicia| B[Bot Python]
    B -->|Query Avançada| C[Google Search Engine]
    C -->|Resultados Brutos| D{Filtro de Segurança}
    D -->|Link Externo| X[Descartar]
    D -->|Dominio .ba.gov.br| E[Limpador de Links]
    E -->|Link Limpo| F[Google Gemini AI]
    F -->|Resumo Gerado| G[📢 Canal Telegram]
