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

*A ser documentado pós-saneamento dos dados.*

### 6. Tecnologias e Bibliotecas

* **Python 3.12**
* **Streamlit** (Camada de aplicação e interface interativa)
* **Pandas & NumPy** (Manipulação, modelagem estatística e cálculo de retornos)
* **Plotly Express & Graph Objects** (Visualizações analíticas interativas)
* **SQLAlchemy & psycopg2-binary** (Persistência e conectividade relacional)
* **yfinance** (Ingestão de dados de mercado)

### 7. Principais Resultados e Evidências Numéricas

*Em desenvolvimento (Card 3 e 4).*

### 8. Discussão e Limitações da Análise

*Em desenvolvimento.*

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
