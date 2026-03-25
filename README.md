# Centralizador de Análise — Charles River Capital

Ferramenta de coleta e síntese automatizada de dados públicos de empresas listadas na B3, desenvolvida como PoC para o processo seletivo DS&AI da Charles River Capital.

---

## Visão Geral

O projeto automatiza a coleta semanal de dados que um analista senior realiza manualmente antes da reunião de comitê. A solução é composta por um pipeline de extração de dados e um dashboard interativo com visão consolidada por empresa.

---

## Arquitetura — Fase 1 (PoC)

```
┌─────────────────────────────────────────────────────┐
│                  CAMADA DE EXTRAÇÃO                  │
│                                                      │
│  [API 1] Fonte Pública Geral                         │
│          Dados de mercado, preço, indicadores        │
│          Fonte: Yahoo Finance / Status Invest / CVM  │
│                                                      │
│  [API 2] ASAI3 — Assaí Atacadista (Varejo)           │
│  [API 3] PRIO3 — PetroRio (Commodities/Petróleo)    │
│  [API 4] RENT3 — Localiza (Serviços)                 │
└───────────────────┬─────────────────────────────────┘
                    │
                    ▼ armazenamento em nuvem (TBD)
┌─────────────────────────────────────────────────────┐
│                  CAMADA DE SÍNTESE                   │
│          LLM (Claude / OpenAI) via API               │
│  - Resumo do negócio (2-3 frases)                    │
│  - Interpretação dos indicadores                     │
│  - Classificação de notícias (pos/neg/neutro)        │
│  - 3 perguntas de investigação para o analista       │
└───────────────────┬─────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│               DASHBOARD INTERATIVO                   │
│   Uma página por empresa | Indicadores selecionados  │
│   Streamlit                                          │
└─────────────────────────────────────────────────────┘
```

---

## Empresas — PoC

| Ticker | Empresa | Setor |
|--------|---------|-------|
| ASAI3 | Assaí Atacadista | Varejo Alimentar |
| PRIO3 | PetroRio | Commodities / Petróleo |
| RENT3 | Localiza Hertz | Serviços / Mobilidade |

---

## Indicadores Monitorados

> Definidos em alinhamento com a tese de valor do analista.
> Em uma implementação real, esses indicadores seriam escolhidos diretamente pelo analista responsável.

| # | Indicador | Por quê importa |
|---|-----------|-----------------|
| 1 | TBD | — |
| 2 | TBD | — |
| 3 | TBD | — |
| 4 | TBD | — |

---

## Fontes de Dados

| Fonte | O que fornece |
|-------|---------------|
| [CVM](https://dados.cvm.gov.br) | Dados cadastrais, DRE, documentos regulatórios |
| [B3](https://www.b3.com.br) | Classificação setorial, segmento de listagem |
| [Yahoo Finance](https://finance.yahoo.com) | Preço, indicadores de mercado |
| [Status Invest](https://statusinvest.com.br) | Indicadores fundamentalistas consolidados |

---

## Pré-requisitos

```bash
python >= 3.10
```

Instalar dependências:

```bash
pip install -r requirements.txt
```

---

## Variáveis de Ambiente

Copie o arquivo de exemplo e preencha suas chaves:

```bash
cp .env.example .env
```

| Variável | Descrição |
|----------|-----------|
| `LLM_API_KEY` | Chave da API do modelo de linguagem (Claude ou OpenAI) |
| `LLM_PROVIDER` | Provedor do LLM: `anthropic` ou `openai` |
| `CLOUD_STORAGE_URL` | URL do armazenamento em nuvem (TBD) |

---

## Como Executar

```bash
# 1. Coletar dados de todas as empresas
python pipeline/run_extraction.py

# 2. Subir o dashboard
streamlit run dashboard/app.py
```

---

## Estrutura do Projeto

```
centralizador_de_analise/
├── pipeline/
│   ├── extractors/
│   │   ├── market_data.py       # API 1 — dados gerais de mercado
│   │   ├── asai3.py             # API 2 — ASAI3
│   │   ├── prio3.py             # API 3 — PRIO3
│   │   └── rent3.py             # API 4 — RENT3
│   └── run_extraction.py        # orquestrador do pipeline
├── synthesis/
│   └── llm_report.py            # geração de relatório via LLM
├── dashboard/
│   └── app.py                   # interface Streamlit
├── .env.example
├── requirements.txt
└── README.md
```

---

## Status

- [ ] Fase 1 — Coleta de dados (em desenvolvimento)
- [ ] Fase 1 — Síntese LLM
- [ ] Fase 1 — Dashboard interativo
- [ ] Fase 2 — Pipeline recorrente + banco de dados
- [ ] Fase 3 — RAG / Memória institucional (opcional)

---

*PoC desenvolvida para o Case DS&AI — Charles River Capital, março/2026.*
