# 🤖 Monitor de Editais REDA - Bahia

![Status](https://img.shields.io/badge/Status-Operacional-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![AI](https://img.shields.io/badge/AI-Google%20Gemini-orange)

> **Automação Inteligente para Monitoramento de Vagas Públicas**

Este projeto é um bot autônomo desenvolvido para monitorar o portal de servidores do Governo da Bahia em busca de novos Processos Seletivos (REDA). O sistema utiliza **Web Scraping** para coletar dados e **Inteligência Artificial (LLM)** para analisar se as vagas são relevantes para profissionais de Tecnologia da Informação e Gestão.

## 🚀 Funcionalidades

- 🕵️ **Web Scraping Automático:** Verifica o site oficial do governo a cada 2 horas.
- 🧠 **Análise com IA:** Utiliza a API do **Google Gemini** para ler os títulos e links, filtrando apenas o que é relevante (TI, Suporte, Administrativo).
- 📢 **Notificações em Tempo Real:** Envia um alerta formatado para um Canal no **Telegram** assim que uma oportunidade é detectada.
- ☁️ **Arquitetura Serverless:** Roda 100% na nuvem via **GitHub Actions**, sem custo de servidor e sem necessidade de máquina local ligada.

## 🛠️ Arquitetura do Projeto

O fluxo de dados segue a seguinte lógica:

```mermaid
graph LR
    A[Portal Bahia] -->|Scraping| B(Bot Python)
    B -->|Texto Bruto| C{Google Gemini AI}
    C -->|Analisa e Resume| D[Formatador]
    D -->|Mensagem Pronta| E[📢 Canal do Telegram]
