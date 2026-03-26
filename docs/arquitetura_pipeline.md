# Arquitetura do Pipeline — Centralizador de Análise

```mermaid
flowchart TD

    %% ─── FONTES DE DADOS ───────────────────────────────────────
    subgraph FONTES["📡 Fontes de Dados (Públicas & Gratuitas)"]
        BCB["🏦 BCB\napi.bcb.gov.br\n─────────────\nSELIC · IPCA\nDesemprego · Câmbio\nBalanço Comercial"]
        YF["📈 Yahoo Finance\nyfinance\n─────────────\nPreço · P/L · P/VP\nEV/EBITDA · ROE\nMargem · DY"]
        CVM["📄 CVM\ndados.cvm.gov.br\n─────────────\nDRE · Balanço\nFatos Relevantes\nCadastro"]
    end

    %% ─── ORQUESTRAÇÃO ──────────────────────────────────────────
    subgraph AIRFLOW["⚙️ Orquestração — Apache Airflow"]
        DAG["DAG: monday_briefing\ncron: 0 8 * * 1\n(toda segunda às 8h)"]
        T1["Task: extract_macro\nBCB → raw"]
        T2["Task: extract_market\nyfinance → raw"]
        T3["Task: extract_fundamentals\nCVM → raw"]
        T4["Task: validate_data\nchecks de qualidade"]
    end

    %% ─── ARMAZENAMENTO RAW ─────────────────────────────────────
    subgraph RAW["🗄️ Camada Raw — Parquet (Google Drive)"]
        P1["macro/\ndate=YYYY-MM-DD\n.parquet"]
        P2["market/\nticker=XXXX\ndate=YYYY-MM-DD\n.parquet"]
        P3["fundamentals/\nticker=XXXX\ndate=YYYY-MM-DD\n.parquet"]
    end

    %% ─── TRANSFORMAÇÃO ─────────────────────────────────────────
    subgraph TRANSFORM["🔄 Transformação & Normalização"]
        T5["Task: transform\n─────────────────────\n· Tipagem e casting\n· Normalização de nomes\n· Join macro + micro\n· Cálculo de indicadores\n  derivados"]
        P4["analytical/\ndate=YYYY-MM-DD\n.parquet\n(camada final)"]
    end

    %% ─── SÍNTESE LLM ────────────────────────────────────────────
    subgraph LLM["🤖 Síntese — LLM"]
        T6["Task: llm_report\n─────────────────────\n· Resumo do negócio\n· Interpretação indicadores\n· Classificação notícias\n· 3 perguntas ao analista"]
        P5["reports/\nticker=XXXX\ndate=YYYY-MM-DD\n.parquet"]
    end

    %% ─── DASHBOARD ─────────────────────────────────────────────
    subgraph DASH["📊 Dashboard Interativo — Streamlit"]
        D1["Página ASAI3\nAssaí Atacadista"]
        D2["Página PRIO3\nPetroRio"]
        D3["Página RENT3\nLocaliza"]
        D4["Visão Macro\nContexto Brasil"]
    end

    %% ─── FLUXO PRINCIPAL ────────────────────────────────────────
    BCB --> T1
    YF  --> T2
    CVM --> T3

    DAG --> T1 & T2 & T3
    T1 & T2 & T3 --> T4

    T4 -->|passa validação| P1 & P2 & P3
    T4 -->|falha| ALERT["🚨 Alerta de erro\n(log + notificação)"]

    P1 & P2 & P3 --> T5
    T5 --> P4

    P4 --> T6
    T6 --> P5

    P4 --> D1 & D2 & D3 & D4
    P5 --> D1 & D2 & D3

    %% ─── ESTILOS ────────────────────────────────────────────────
    style FONTES   fill:#1e3a5f,color:#fff,stroke:#4a90d9
    style AIRFLOW  fill:#2d4a1e,color:#fff,stroke:#6abf40
    style RAW      fill:#4a2d1e,color:#fff,stroke:#d97a40
    style TRANSFORM fill:#2d1e4a,color:#fff,stroke:#9b6abf
    style LLM      fill:#4a1e3a,color:#fff,stroke:#d94a8c
    style DASH     fill:#1e4a4a,color:#fff,stroke:#40bfbf
    style ALERT    fill:#7a1e1e,color:#fff,stroke:#d94a4a
```

---

## Camadas do Pipeline

| Camada | Tecnologia | Responsabilidade |
|--------|-----------|-----------------|
| **Extração** | `python-bcb`, `yfinance`, `requests` | Coleta dados brutos das fontes públicas |
| **Orquestração** | Apache Airflow | Agendamento, dependências entre tasks, retry e alertas |
| **Raw** | Parquet · Google Drive | Armazena dados brutos particionados por data/ticker |
| **Transformação** | pandas / polars | Normalização, join das fontes, cálculo de indicadores |
| **Analítica** | Parquet · Google Drive | Camada final limpa, pronta para consumo |
| **Síntese** | LLM API (Claude / OpenAI) | Relatório interpretativo por empresa |
| **Visualização** | Streamlit | Dashboard interativo por empresa + visão macro |

---

## Tickers Monitorados (PoC)

| Ticker | Empresa | Setor |
|--------|---------|-------|
| ASAI3 | Assaí Atacadista | Varejo Alimentar |
| PRIO3 | PetroRio | Commodities / Petróleo |
| RENT3 | Localiza Hertz | Serviços / Mobilidade |

---

## Frequência de Execução

```
DAG agendada: toda segunda-feira às 8h
Objetivo: dados prontos antes da reunião de comitê das 14h
```
