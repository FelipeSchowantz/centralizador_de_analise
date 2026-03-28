# Centralizador de Análise — Charles River Capital

Ferramenta de coleta e síntese automatizada de dados públicos de empresas listadas na B3, desenvolvida como PoC para o processo seletivo DS&AI da Charles River Capital.

O projeto automatiza a coleta semanal de dados que um analista senior realiza manualmente antes da reunião de comitê das 14h. A solução é composta por um pipeline de extração, armazenamento em Parquet (data-lakehouse), transformação via dbt, síntese via LLM e um dashboard interativo com visão consolidada por empresa.

---

## Empresas Monitoradas — PoC

| Ticker | Empresa | Setor |
|--------|---------|-------|
| ASAI3 | Assaí Atacadista | Varejo Alimentar |
| PRIO3 | PetroRio | Commodities / Petróleo |
| RENT3 | Localiza Hertz | Serviços / Mobilidade |

> A escolha cobre três setores distintos para validar a generalidade do pipeline. Em produção, qualquer ticker B3 pode ser adicionado sem alterações estruturais.

---

## Arquitetura

```
┌──────────────────────────────────────────────────────────────────┐
│                     FONTES DE DADOS                              │
│                                                                  │
│  [Macro]  BCB — api.bcb.gov.br                                   │
│           SELIC · IPCA · Desemprego · Câmbio · Bal. Comercial    │
│                                                                  │
│  [Micro]  Yahoo Finance (yfinance)                               │
│           Preço · P/L · P/VP · EV/EBITDA · ROE · Margem · DY    │
│                                                                  │
│  [DRE]    CVM — dados.cvm.gov.br                                 │
│           Receita · EBIT · Lucro Líquido (ITR/DFP)              │
└─────────────────────┬────────────────────────────────────────────┘
                      │
                      ▼  Apache Airflow — DAG: monday_briefing
                      │  Agendamento: toda segunda às 8h (cron: 0 8 * * 1)
                      │
┌─────────────────────▼────────────────────────────────────────────┐
│                    DATA-LAKEHOUSE                                │
│                                                                  │
│  raw/bcb/          → Parquet bruto do Banco Central              │
│  raw/yfinance/     → Parquet bruto do Yahoo Finance              │
│  raw/cvm/          → Parquet bruto da CVM                        │
│  analytical/       → dados transformados e prontos               │
│                                                                  │
│  Backup: Google Drive (upload automático pelo loader)            │
└─────────────────────┬────────────────────────────────────────────┘
                      │
                      ▼  PostgreSQL + dbt core
                      │  staging → marts (por empresa)
                      │
┌─────────────────────▼────────────────────────────────────────────┐
│                    SÍNTESE — LLM                                 │
│                                                                  │
│  A LLM não emite opiniões qualitativas genéricas.                │
│  Ela descreve brevemente grandes mudanças ou alterações          │
│  relevantes nos dados, sempre ancorada na tese de                │
│  investimento do fundo (value investing · downside first).       │
│                                                                  │
│  Exemplo de output:                                              │
│  "Receita líquida cresceu 18% vs trimestre anterior.             │
│   Dívida líq./EBITDA recuou de 3,2x para 2,8x — alinhado        │
│   à tese de desalavancagem. Margem EBITDA contraiu 1,2pp."       │
└─────────────────────┬────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────▼────────────────────────────────────────────┐
│                 DASHBOARD — Streamlit                            │
│   Uma página por empresa + visão macro consolidada              │
│   Indicadores definidos em alinhamento com a tese do analista    │
└──────────────────────────────────────────────────────────────────┘
```

---

## Stack Tecnológico

| Camada | Tecnologia | Função |
|--------|-----------|--------|
| Orquestração | Apache Airflow | DAG semanal toda segunda às 8h |
| Extração macro | `python-bcb` | SELIC, IPCA, câmbio, desemprego |
| Extração micro | `yfinance` | Preço, múltiplos, margens |
| Extração DRE | `requests` + CVM API | Linhas de DRE (ITR/DFP) |
| Armazenamento raw | Parquet + Google Drive | Camada raw auditável |
| Banco analítico | PostgreSQL | Persistência estruturada |
| Transformação | dbt core | Staging → Marts com testes |
| Síntese | LLM (Anthropic/OpenAI) | Detecção de mudanças pela tese |
| Dashboard | Streamlit + Plotly | Interface interativa |

---

## Fontes de Dados

| Fonte | Tipo | O que fornece |
|-------|------|---------------|
| [BCB](https://api.bcb.gov.br) | Macro | SELIC, IPCA, desemprego, câmbio, balanço comercial |
| [Yahoo Finance](https://finance.yahoo.com) | Micro | Preço, múltiplos de mercado, margens |
| [CVM](https://dados.cvm.gov.br) | Micro | DRE completa (ITR/DFP), dados cadastrais |

Todas as fontes são **públicas e gratuitas**, sem autenticação paga.

---

## Indicadores Monitorados

> Definidos em alinhamento com a tese de value investing do analista.
> Em uma implementação real, esses indicadores são configurados diretamente pelo analista responsável.

| # | Indicador | Fonte | Por quê importa |
|---|-----------|-------|-----------------|
| 1 | TBD | — | — |
| 2 | TBD | — | — |
| 3 | TBD | — | — |
| 4 | TBD | — | — |

---

## Papel da LLM

A LLM atua como um **detector de mudanças relevantes**, não como analista.

- **Faz:** descreve variações significativas nos indicadores em relação ao período anterior e sinaliza se impactam a tese
- **Não faz:** emite opiniões qualitativas genéricas, avalia gestão, cultura ou perspectivas subjetivas

O prompt é construído com base na tese do fundo (value investing, proteção ao downside) e na comparação histórica dos dados coletados.

---

## Estrutura do Projeto

```
centralizador_de_analise/
│
├── data-pipeline/
│   ├── dags/
│   │   └── monday_briefing.py       # DAG Airflow — cron toda segunda às 8h
│   ├── extractors/
│   │   ├── macro_bcb.py             # Extrator BCB (SELIC, IPCA, câmbio…)
│   │   ├── market_yfinance.py       # Extrator Yahoo Finance (preço, múltiplos)
│   │   └── fundamentals_cvm.py      # Extrator CVM (DRE via ITR/DFP)
│   └── loaders/
│       ├── parquet_loader.py        # Upload Parquet → Google Drive
│       └── postgres_loader.py       # Carga Parquet → PostgreSQL (staging)
│
├── data-lakehouse/
│   ├── raw/
│   │   ├── bcb/                     # Parquets brutos do Banco Central
│   │   ├── yfinance/                # Parquets brutos do Yahoo Finance
│   │   └── cvm/                     # Parquets brutos da CVM
│   └── analytical/                  # Dados processados (gerados pelo dbt)
│
├── dbt/
│   ├── models/
│   │   ├── staging/
│   │   │   ├── stg_bcb.sql          # Normalização macro BCB
│   │   │   ├── stg_yfinance.sql     # Normalização múltiplos yfinance
│   │   │   └── stg_cvm.sql          # Normalização DRE CVM
│   │   └── marts/
│   │       ├── mart_asai3.sql       # Visão consolidada ASAI3
│   │       ├── mart_prio3.sql       # Visão consolidada PRIO3
│   │       └── mart_rent3.sql       # Visão consolidada RENT3
│   ├── tests/
│   │   └── test_quality.yml         # Testes de qualidade dbt
│   └── dbt_project.yml
│
├── synthesis/
│   └── llm_report.py                # Síntese via LLM (mudanças pela tese)
│
├── dashboard/
│   └── app.py                       # Streamlit — uma página por empresa + macro
│
├── docs/
│   └── arquitetura_pipeline.md      # Fluxograma detalhado
│
├── Documentos/                      # Case e e-mail originais (referência)
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Roadmap — Módulos Futuros

### Agentes de Transcrição de Reuniões de Resultado

Módulo planejado para leitura automatizada dos transcritos de earnings calls das empresas, com dois agentes de propósito distinto:

**Agente 1 — Thesis Tracker**
- Varre o transcrito procurando menções aos temas e indicadores da tese do analista
- Ex: menções a alavancagem, expansão de margem, geração de caixa, capex
- Output: trechos relevantes mapeados por tema da tese, exibidos no dashboard

**Agente 2 — Blind Spot Detector**
- Procura informações que estão *fora* da tese mas foram mencionadas na reunião
- Ex: mudança de gestão, risco regulatório, novo competidor, guidance revisado
- Output: alertas sobre o que pode ter ficado debaixo do radar

Ambos os outputs aparecem em colunas separadas no dashboard — o analista vê simultaneamente o que confirma/nega a tese e o que pode ter passado despercebido.

> **Por que não está na Fase 1:** transcritos de empresas brasileiras não têm fonte pública estruturada e consistente. O módulo exige ingestão de PDFs dos sites de RI, o que ultrapassa o escopo do prazo atual. A arquitetura está definida para implementação futura.

---

## Pré-requisitos

```bash
python >= 3.10
apache-airflow >= 2.8
postgresql >= 14
dbt-core >= 1.7
```

```bash
pip install -r requirements.txt
```

---

## Variáveis de Ambiente

```bash
cp .env.example .env
```

| Variável | Descrição |
|----------|-----------|
| `LLM_API_KEY` | Chave da API do modelo de linguagem |
| `LLM_PROVIDER` | Provedor: `anthropic` ou `openai` |
| `POSTGRES_URL` | Connection string do PostgreSQL |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Caminho para o JSON da service account |
| `GOOGLE_DRIVE_FOLDER_ID` | ID da pasta no Google Drive |

---

## Como Executar

```bash
# 1. Iniciar o Airflow
airflow standalone

# 2. Ativar a DAG no painel (localhost:8080)
#    DAG: monday_briefing

# 3. Ou rodar o pipeline manualmente
python data-pipeline/extractors/macro_bcb.py
python data-pipeline/extractors/market_yfinance.py
python data-pipeline/extractors/fundamentals_cvm.py
python data-pipeline/loaders/postgres_loader.py

# 4. Rodar transformações dbt
cd dbt && dbt run && dbt test

# 5. Subir o dashboard
streamlit run dashboard/app.py
```

---

## Status

- [ ] Fase 1 — Extração macro (BCB)
- [ ] Fase 1 — Extração micro (yfinance + CVM)
- [ ] Fase 1 — Carga no PostgreSQL
- [ ] Fase 1 — Transformação dbt (staging → marts)
- [ ] Fase 1 — Síntese LLM pela tese
- [ ] Fase 1 — Dashboard interativo (Streamlit)
- [ ] Fase 2 — Pipeline recorrente com histórico (Airflow + Parquet)
- [ ] Fase 2 — Tratamento de erros e logging
- [ ] Fase 3 — RAG / Memória institucional (opcional)
- [ ] Roadmap — Agentes de transcrição de earnings calls

---

*PoC desenvolvida para o Case DS&AI — Charles River Capital, março/2026.*
