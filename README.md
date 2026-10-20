# [BI-M2] Performance de Mercado de Ações & Séries Temporais (B3)

> **Status do Projeto:** 🟡 Em Desenvolvimento Ativo (Sprint de Engenharia e Visualização de Dados).

---

## Sumário Executivo do Projeto

1. [Título e Resumo Executivo](#1-título-e-resumo-executivo)
2. [Contexto de Negócio e Pergunta Orientadora](#2-contexto-de-negócio-e-pergunta-orientadora)
3. [Fonte de Dados e Licença](#3-fonte-de-dados-e-licença)
4. [Pipeline de Engenharia de Dados (ETL)](#4-pipeline-de-engenharia-de-dados-etl)
5. [Dicionário de Dados](#5-dicionário-de-dados)
6. [Tecnologias e Bibliotecas](#6-tecnologias-e-bibliotecas)
7. [Principais Resultados e Evidências Numéricas](#7-principais-resultados-e-evidências-numéricas)
8. [Discussão e Limitações da Análise](#8-discussão-e-limitações-da-análise)
9. [Aplicação Profissional e Decisões de Negócio](#9-aplicação-profissional-e-decisões-de-negócio)
10. [Demonstração do Data App (Streamlit Cloud)](#10-demonstração-do-data-app-streamlit-cloud)
11. [Como Executar Localmente](#11-como-executar-localmente)
12. [Estrutura de Pastas](#12-estrutura-de-pastas)
13. [Gestão Ágil e Links do Projeto](#13-gestão-ágil-e-links-do-projeto)
14. [Autoria e Créditos](#14-autoria-e-créditos)

---

### 1. Título e Resumo Executivo

*Em desenvolvimento na Sprint 1.*

### 2. Contexto de Negócio e Pergunta Orientadora

Análise de performance, risco, retorno acumulado e séries temporais de 12 ativos da B3 (triênio 2021-2023).

### 3. Fonte de Dados e Licença

* Dados históricos de cotações da B3 extraídos via API pública do Yahoo Finance (`yfinance`).
* Recorte temporal: 01/01/2021 a 31/12/2023.

### 4. Pipeline de Engenharia de Dados (ETL)

*Em desenvolvimento (Card 2).*

### 5. Dicionário de Dados

A base tratada final (`data/processed/b3_stocks_processed.csv`) consolida 745 pregões diários para cada um dos 12 ativos da B3 no triénio 2021–2023, estruturada com 14 variáveis sem valores nulos:

| Nome da Coluna Padronizada | Coluna Técnica no CSV | Tipo Primitivo | Descrição do Significado Financeiro | Regra de Cálculo / Fórmula |
| :--- | :--- | :--- | :--- | :--- |
| **Data do Pregão** | `date` | `datetime64[ns]` | Data oficial da sessão de negociação na B3 (sem fuso horário). | Extraído do índice temporal da B3 e formatado como `YYYY-MM-DD`. |
| **Código do Ativo** | `ticker` | `string` / `object` | Símbolo de negociação da ação na B3 com sufixo `.SA`. | Identificador oficial do papel (ex.: `WEGE3.SA`, `EMBJ3.SA`). |
| **Setor Económico** | `setor` | `string` / `object` | Segmento macroeconómico oficial em que a companhia opera. | Mapeamento determinístico dos 4 setores estratégicos. |
| **Abertura** | `open` | `float64` | Primeiro preço cotado no leilão de abertura da sessão (R$). | Cotação bruta saneada contra nulos via propagação temporal. |
| **Máxima** | `high` | `float64` | Preço mais elevado atingido durante o pregão (R$). | Cotação máxima diária registada pela B3. |
| **Mínima** | `low` | `float64` | Preço mais baixo negociado durante o pregão (R$). | Cotação mínima diária registada pela B3. |
| **Fecho Ajustado** | `adj_close` | `float64` | Preço de encerramento ajustado por proventos (dividendos, JCP, desdobramentos). | Cotação de liquidação ajustada via `yfinance`. |
| **Volume Financeiro** | `volume` | `float64` | Montante total transacionado na sessão em moeda corrente. | Volume financeiro diário oficial da B3. |
| **Retorno Diário** | `ret_diario` | `float64` | Variação percentual do fecho ajustado entre pregões consecutivos. | $\frac{P_t - P_{t-1}}{P_{t-1}}$ via `.pct_change()`, 1º pregão preenchido com `0.0`. |
| **Base 100** | `base_100` | `float64` | Desempenho relativo normalizado a partir de 100 no 1º pregão de 2021. | $\left(\frac{P_t}{P_0}\right) \times 100$, onde $P_0$ é o fecho ajustado inicial. |
| **Média Móvel 21D** | `sma_21` | `float64` | Média móvel simples de curto prazo (21 pregões úteis / ~1 mês). | $\frac{1}{21}\sum_{i=0}^{20} P_{t-i}$ via `.rolling(21, min_periods=1).mean()`. |
| **Média Móvel 50D** | `sma_50` | `float64` | Média móvel simples de médio prazo (50 pregões úteis / ~1 trimestre). | $\frac{1}{50}\sum_{i=0}^{49} P_{t-i}$ via `.rolling(50, min_periods=1).mean()`. |
| **Pico Histórico** | `peak` | `float64` | Maior cotação ajustada alcançada pelo ativo desde o início da série. | $\max(P_0, P_1, \dots, P_t)$ via `.cummax()`. |
| **Rebaixamento (Drawdown)** | `drawdown` | `float64` | Perda percentual acumulada face à máxima histórica anterior. | $\frac{P_t - \text{Peak}_t}{\text{Peak}_t}$ (estritamente $\le 0.0$). |

### 6. Tecnologias e Bibliotecas

* **Python 3.12**
* **Streamlit** (Camada de aplicação e interface interativa)
* **Pandas & NumPy** (Manipulação, modelagem estatística e cálculo de retornos)
* **Plotly Express & Graph Objects** (Visualizações analíticas interativas)
* **SQLAlchemy & psycopg2-binary** (Persistência e conectividade relacional)
* **yfinance** (Ingestão de dados de mercado)

## 7. Principais Resultados e Evidências Numéricas

A tabela abaixo consolida os achados quantitativos da Análise Exploratória de Dados (EDA) conduzida na janela trienal de 01/01/2021 a 31/12/2023 sobre os 12 ativos da carteira B3:

| Ticker | Setor Econômico | Retorno Acumulado (%) | Volatilidade Anualizada (% a.a.) | Índice Sharpe Empírico | Max Drawdown (%) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **PETR4.SA** | Petróleo, Gás & Energia | +228.69% | 39.42% | 5.80 | -39.10% |
| **PRIO3.SA** | Petróleo, Gás & Energia | +208.32% | 46.78% | 4.45 | -34.32% |
| **EMBJ3.SA** | Bens de Capital & Indústria | +167.50% | 46.82% | 3.58 | -58.27% |
| **GGBR4.SA** | Materiais Básicos & Siderurgia/Papel | +30.79% | 35.56% | 0.87 | -33.93% |
| **EGIE3.SA** | Petróleo, Gás & Energia | +25.35% | 18.76% | 1.35 | -17.65% |
| **ITUB4.SA** | Financeiro, Consumo & Locação | +24.02% | 28.83% | 0.83 | -35.87% |
| **VALE3.SA** | Materiais Básicos & Siderurgia/Papel | +18.11% | 33.90% | 0.53 | -41.34% |
| **WEGE3.SA** | Bens de Capital & Indústria | +3.51% | 32.83% | 0.11 | -49.51% |
| **ABEV3.SA** | Financeiro, Consumo & Locação | +2.57% | 25.46% | 0.10 | -31.42% |
| **RENT3.SA** | Financeiro, Consumo & Locação | -0.25% | 36.89% | -0.01 | -38.40% |
| **KLBN11.SA** | Materiais Básicos & Siderurgia/Papel | -0.80% | 26.62% | -0.03 | -39.30% |
| **BBDC4.SA** | Financeiro, Consumo & Locação | -6.93% | 31.38% | -0.22 | -46.05% |

### Síntese dos 4 KPIs Estratégicos da Carteira (Critério 10)

* **Retorno Médio da Carteira:** **+58.24%** no triênio analisado.
* **Ativo Destaque da Carteira:** **PETR4.SA** (**+228.69%**), impulsionado pelo ciclo global de alta de commodities e forte distribuição de proventos.
* **Ativo de Menor Desempenho:** **BBDC4.SA** (**-6.93%**), impactado pelo ciclo de alta de juros e compressão de margens de crédito.
* **Ativo Mais Resiliente (Menor Risco):** **EGIE3.SA** (Max Drawdown de **-17.65%** e menor volatilidade anualizada com **18.76% a.a.**), refletindo o perfil defensivo do segmento de utilidades públicas.

---

## 8. Discussão e Limitações da Análise

> **Rigor Metodológico e Limitações Contextuais (Itens 4.5 e 5.2 do Edital):**  
> Os dados compreendem a série temporal diária de 01/01/2021 a 31/12/2023. O período foi marcado pelo ciclo macroeconômico de aperto monetário no Brasil (elevação da Selic de 2,00% para 13,75% a.a.) e choques geopolíticos internacionais na cadeia de suprimentos e energia.  
> As correlações observadas e as performances passadas dos ativos **não implicam causalidade mecânica nem garantem rentabilidade futura**. As conclusões têm caráter exclusivamente analítico e educacional, não constituindo recomendação de alocação ou investimento em valores mobiliários.

### 9. Aplicação Profissional e Decisões de Negócio

*Em desenvolvimento.*

### 10. Demonstração do Data App (Streamlit Cloud)

*Deploy em configuração.*

### 11. Como Executar Localmente

```bash
# Clone o repositório
git clone [https://github.com/SEU_USUARIO/b3-market-performance-bi.git](https://github.com/SEU_USUARIO/b3-market-performance-bi.git)
cd b3-market-performance-bi

# Crie e ative o ambiente virtual
py -3.12 -m venv .venv
source .venv/Scripts/activate

# Instale as dependências
pip install -r requirements.txt

# Execute a aplicação Streamlit
streamlit run app.py
```

### 12. Estrutura de Pastas

```text
b3-market-performance-bi/
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
├── data/
│   ├── processed/
│   │   └── .gitkeep
│   └── raw/
│       └── .gitkeep
├── notebooks/
│   └── .gitkeep
├── src/
│   └── .gitkeep
├── .gitignore
├── app.py
├── README.md
└── requirements.txt
```

### 13. Gestão Ágil e Links do Projeto

Quadro Kanban no Trello: [Link público a ser inserido]

Aplicação em Produção (Streamlit Cloud): [Link a ser inserido]

Vídeo Pitch de Apresentação: [Link a ser inserido]

### 14. Autoria e Créditos

Estudante: Andressa Alves de Souza

Orientação: Prof. Sávio Ricardo Garcia

Instituição: SENAI SC / LAB365
