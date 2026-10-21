"""Aplicação Corporativa de BI - Performance de Séries Temporais da B3 (2021-2023).

Projeto Avaliativo Final de BI (Módulo 2) - Linha 2
Orientador: Prof. Sávio Ricardo Garcia
Responsável Técnica: Andressa Alves de Souza

Camada de UX/UI Executiva:
- Padrão Z/F (Pirâmide Invertida) com 4 KPIs estratégicos superiores em st.metric.
- Sidebar reativa com st.session_state e botão de reset atômico.
- Organização temática em 4 abas (st.tabs) com Plotly.
- Resiliência de dados com fallback para CSV local e conformidade LGPD.
"""

from __future__ import annotations

import math
from datetime import date
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import streamlit as st

# Módulo de visualizações puras desacopladas (Critério 8)
from src.visualizations import (
    plot_base_100,
    plot_daily_returns_distribution,
    plot_drawdown_matrix,
    plot_risk_return,
    plot_technical_trend,
)

# ============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA (WIDE & CORPORATIVO)
# ============================================================================
st.set_page_config(
    page_title="B3 Market Performance | BI Executive Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# 2. CONSTANTES OFICIAIS & MAPEAMENTO SETORIAL (EDITAL ITEM 4.1.1)
# ============================================================================
SETORES_OFICIAIS: List[str] = [
    "Petróleo, Gás & Energia",
    "Bens de Capital & Indústria",
    "Materiais Básicos & Siderurgia",
    "Financeiro, Consumo & Locação",
]

MAPA_ATIVOS_SETOR: Dict[str, List[str]] = {
    "Petróleo, Gás & Energia": ["PETR4.SA", "PRIO3.SA", "EGIE3.SA"],
    "Bens de Capital & Indústria": ["WEGE3.SA", "EMBJ3.SA"],
    "Materiais Básicos & Siderurgia": ["VALE3.SA", "GGBR4.SA", "KLBN11.SA"],
    "Financeiro, Consumo & Locação": ["ITUB4.SA", "BBDC4.SA", "ABEV3.SA", "RENT3.SA"],
}

ALL_TICKERS: List[str] = [
    ticker for tickers in MAPA_ATIVOS_SETOR.values() for ticker in tickers
]

DATA_INICIAL_PADRAO = date(2021, 1, 4)
DATA_FINAL_PADRAO = date(2023, 12, 29)


# ============================================================================
# 3. CAMADA DE ACESSO A DADOS (CACHE & RESILIÊNCIA DE FALLBACK)
# ============================================================================
@st.cache_data(ttl=3600, show_spinner=False)
def load_market_data() -> pd.DataFrame:
    """Carrega dados da B3 via SQL (Supabase) com contingência silenciosa para CSV local."""
    df: pd.DataFrame | None = None

    # Tentativa primária: Conexão remota segura via secrets.toml (sem hardcoding)
    try:
        if "connections" in st.secrets and "postgresql" in st.secrets["connections"]:
            conn = st.connection("postgresql", type="sql")
            query = "SELECT * FROM b3_stocks_processed ORDER BY date ASC, ticker ASC;"
            df = conn.query(query)
    except Exception:
        df = None

    # Fallback transparente para o arquivo processado na camada Ouro
    if df is None or df.empty:
        base_dir = Path(__file__).resolve().parent
        csv_path = base_dir / "data" / "processed" / "b3_stocks_processed.csv"

        if not csv_path.exists():
            st.error(
                "🚨 **Falha Crítica de Infraestrutura:** A base tratada de mercado "
                "não foi encontrada em `data/processed/b3_stocks_processed.csv`."
            )
            st.stop()

        df = pd.read_csv(csv_path)

    # Coerção estrita de tipos
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)

    colunas_float = [
        "open", "high", "low", "adj_close", "volume",
        "ret_diario", "base_100", "sma_21", "sma_50", "peak", "drawdown",
    ]
    for col in colunas_float:
        if col in df.columns:
            df[col] = df[col].astype(np.float64)

    # Padronização de nomenclatura setorial
    df["setor"] = df["setor"].replace(
        {"Materiais Básicos & Siderurgia/Papel": "Materiais Básicos & Siderurgia"}
    )
    return df


# Ingestão de dados com feedback visual controlado
with st.spinner("Sincronizando dados corporativos da B3..."):
    df_raw = load_market_data()


# ============================================================================
# 4. GESTÃO DE ESTADO REATIVO (SESSION STATE & RESET)
# ============================================================================
def init_session_state() -> None:
    """Inicializa variáveis de controle de sessão com valores padrão."""
    if "selected_sectors" not in st.session_state:
        st.session_state.selected_sectors = list(SETORES_OFICIAIS)

    if "selected_tickers" not in st.session_state:
        st.session_state.selected_tickers = list(ALL_TICKERS)

    if "date_range" not in st.session_state:
        st.session_state.date_range = (DATA_INICIAL_PADRAO, DATA_FINAL_PADRAO)


def reset_filters() -> None:
    """Restaura instantaneamente o estado da aplicação para o padrão sem quebrar a execução."""
    st.session_state.selected_sectors = list(SETORES_OFICIAIS)
    st.session_state.selected_tickers = list(ALL_TICKERS)
    st.session_state.date_range = (DATA_INICIAL_PADRAO, DATA_FINAL_PADRAO)


init_session_state()


# ============================================================================
# 5. BARRA LATERAL REATIVA (ST.SIDEBAR)
# ============================================================================

with st.sidebar:
    st.markdown("## 🏛️ **B3 Performance**")
    st.markdown("### **Filtros Estratégicos**")
    st.caption("Ajuste a segmentação setorial, ativos e horizonte de análise:")

    # 1. Filtro de Setores Econômicos
    setores_input = st.multiselect(
        "Setores Econômicos:",
        options=SETORES_OFICIAIS,
        default=st.session_state.selected_sectors,
        key="selected_sectors",
        help="Filtra a base de ativos pelos 4 macro-setores oficiais do edital.",
    )

    # Resolução de ativos elegíveis em função dos setores selecionados
    tickers_elegiveis: List[str] = []
    for s in setores_input:
        tickers_elegiveis.extend(MAPA_ATIVOS_SETOR.get(s, []))

    # Saneamento para manter selecionados apenas tickers que pertencem aos setores ativos
    tickers_validos_selecionados = [
        t for t in st.session_state.selected_tickers if t in tickers_elegiveis
    ]
    if not tickers_validos_selecionados and tickers_elegiveis:
        tickers_validos_selecionados = list(tickers_elegiveis)

    # 2. Filtro Dinâmico de Ativos
    tickers_input = st.multiselect(
        "Ativos (Tickers B3):",
        options=tickers_elegiveis,
        default=tickers_validos_selecionados,
        key="selected_tickers",
        help="Selecione as ações individuais que compõem a análise.",
    )

    # 3. Seletor de Intervalo Temporal
    datas_input = st.date_input(
        "Janela de Negociação:",
        value=st.session_state.date_range,
        min_value=DATA_INICIAL_PADRAO,
        max_value=DATA_FINAL_PADRAO,
        key="date_range",
        help="Intervalo temporal para cálculo de retornos e métricas.",
    )

    st.markdown("---")

    # 4. Botão de Reset
    st.button(
        "🔄 Redefinir Todos os Filtros",
        on_click=reset_filters,
        use_container_width=True,
        help="Restaura os setores, ativos e o triênio completo original.",
    )

    st.markdown("---")
    st.markdown(
        "**Governança & Autoria:**\n"
        "- **Responsável:** Andressa Alves de Souza\n"
        "- **Orientação:** Prof. Sávio Ricardo Garcia\n"
        "- **Projeto:** BI Módulo 2 — Linha 2 (B3)"
    )


# ============================================================================
# 6. FILTRAGEM DOS DADOS & RECÁLCULO DINÂMICO DE BASE 100
# ============================================================================
# Validação do intervalo temporal fornecido
if isinstance(datas_input, (tuple, list)) and len(datas_input) == 2:
    start_dt, end_dt = datas_input
else:
    start_dt, end_dt = DATA_INICIAL_PADRAO, DATA_FINAL_PADRAO

start_ts = pd.to_datetime(start_dt)
end_ts = pd.to_datetime(end_dt)

# Aplicação dos filtros relacionais
df_filtrado = df_raw[
    (df_raw["setor"].isin(setores_input))
    & (df_raw["ticker"].isin(tickers_input))
    & (df_raw["date"] >= start_ts)
    & (df_raw["date"] <= end_ts)
].copy()

# Validação defensiva contra seleções vazias
if df_filtrado.empty:
    st.warning(
        "⚠️ **Nenhum registro localizado para o recorte selecionado.** "
        "Por favor, ajuste os filtros na barra lateral ou clique em 'Redefinir Todos os Filtros'."
    )
    st.stop()

# Recálculo dinâmico da Base 100 ancorada rigorosamente no primeiro pregão do recorte
def recalculate_base_100(df: pd.DataFrame) -> pd.DataFrame:
    """Recalcula a série Base 100 relativa à primeira sessão da janela filtrada."""
    dfs = []
    for _, grupo in df.groupby("ticker"):
        g = grupo.sort_values("date").copy()
        p0 = g["adj_close"].iloc[0]
        g["base_100"] = (g["adj_close"] / p0) * 100.0 if p0 > 0 else 100.0
        # Recálculo de peak e drawdown no horizonte visualizado
        g["peak"] = g["adj_close"].cummax()
        g["drawdown"] = (g["adj_close"] - g["peak"]) / g["peak"]
        dfs.append(g)
    return pd.concat(dfs, ignore_index=True)

df_filtrado = recalculate_base_100(df_filtrado)


# ============================================================================
# 7. FUNÇÃO DE CÁLCULO DOS 4 KPIS ESTRATÉGICOS (PIRÂMIDE INVERTIDA)
# ============================================================================
def compute_executive_kpis(df: pd.DataFrame) -> Dict[str, dict]:
    """Calcula os indicadores executivos para o painel superior."""
    kpi_records = []
    for ticker, g in df.groupby("ticker"):
        sorted_g = g.sort_values("date")
        p_ini = sorted_g["adj_close"].iloc[0]
        p_fim = sorted_g["adj_close"].iloc[-1]
        ret_acum = ((p_fim / p_ini) - 1.0) * 100.0 if p_ini > 0 else 0.0

        # Volatilidade anualizada: sigma * sqrt(252)
        std_ret = sorted_g["ret_diario"].std()
        vol_anual = float(std_ret * math.sqrt(252) * 100.0) if pd.notnull(std_ret) else 0.0
        max_dd = float(sorted_g["drawdown"].min() * 100.0)

        kpi_records.append({
            "ticker": ticker,
            "setor": sorted_g["setor"].iloc[0],
            "retorno": ret_acum,
            "volatilidade": vol_anual,
            "max_drawdown": max_dd,
        })

    kpi_df = pd.DataFrame(kpi_records)

    # 1. Retorno Médio da Carteira
    ret_medio = kpi_df["retorno"].mean()

    # 2. Ativo Destaque (Maior Retorno)
    top_ativo = kpi_df.sort_values("retorno", ascending=False).iloc[0]

    # 3. Menor Desempenho (Menor Retorno)
    bottom_ativo = kpi_df.sort_values("retorno", ascending=True).iloc[0]

    # 4. Ativo Mais Defensivo / Resiliente (Menor Queda Máxima / Drawdown mais próximo de 0)
    resiliente = kpi_df.sort_values("max_drawdown", ascending=False).iloc[0]

    return {
        "retorno_medio": ret_medio,
        "top_ativo": top_ativo,
        "bottom_ativo": bottom_ativo,
        "resiliente": resiliente,
    }

kpis = compute_executive_kpis(df_filtrado)


# ============================================================================
# 8. CABEÇALHO & PAINEL DE KPIS EXECUTIVOS SUPERIOR (CRITÉRIO 10)
# ============================================================================
st.title("🏛️ Performance de Mercado & Séries Temporais da B3")
st.markdown(
    "**Plataforma de Monitoramento Quantitativo e Séries Históricas de Ações (2021-2023)**  \n"
    "*Visualização executiva orientada a tomada de decisão estruturada pelo Padrão Z/F.*"
)

st.markdown("---")

# Renderização dos 4 Cards Superiores em st.columns(4)
col1, col2, col3, col4 = st.columns(4)

with col1:
    ret_medio_val = kpis["retorno_medio"]
    st.metric(
        label="Retorno Médio da Carteira",
        value=f"{ret_medio_val:+.2f}%",
        delta=f"{ret_medio_val:+.2f}% vs. Neutro (0.0%)",
        delta_color="normal",
        help="Média aritmética da rentabilidade acumulada de todos os papéis no período filtrado.",
    )

with col2:
    top = kpis["top_ativo"]
    st.metric(
        label=f"Ativo Destaque: {top['ticker']}",
        value=f"{top['retorno']:+.2f}%",
        delta=f"Setor: {top['setor']}",
        delta_color="off",
        help="Papel com maior ganho acumulado de capital dentro da janela temporal selecionada.",
    )

with col3:
    bottom = kpis["bottom_ativo"]
    st.metric(
        label=f"Menor Desempenho: {bottom['ticker']}",
        value=f"{bottom['retorno']:+.2f}%",
        delta=f"Setor: {bottom['setor']}",
        delta_color="off",
        help="Ativo que registrou a menor rentabilidade no horizonte analisado.",
    )

with col4:
    defensivo = kpis["resiliente"]
    st.metric(
        label=f"Mais Resiliente: {defensivo['ticker']}",
        value=f"{defensivo['max_drawdown']:.2f}%",
        delta=f"Volatilidade: {defensivo['volatilidade']:.2f}% a.a.",
        delta_color="inverse",
        help="Ativo com menor rebaixamento a partir da máxima histórica (menor vale de perda de capital).",
    )

st.markdown("---")


# ============================================================================
# 9. ORGANIZAÇÃO EM 4 ABAS TEMÁTICAS (ST.TABS - CRITÉRIOS 8 E 9)
# ============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Performance Relativa & Mercado",
    "⚖️ Matriz Risco x Retorno & Dispersão",
    "🛡️ Resiliência, Drawdown & Análise Técnica",
    "📑 Governança, Dicionário & Dados Brutos",
])

# ----------------------------------------------------------------------------
# ABA 1: PERFORMANCE RELATIVA & MERCADO (BASE 100)
# ----------------------------------------------------------------------------
with tab1:
    st.subheader("Evolução Comparativa Normalizada em Base 100")
    st.markdown(
        "A normalização em **Base 100** ancora a cotação de cada ativo em 100.0 pontos no primeiro pregão útil "
        "do intervalo, permitindo comparar de forma simétrica ativos com valores nominais distintos. "
        "A linha tracejada horizontal no nível 100.0 demarca o limiar de **preservação de capital**."
    )

    fig_base100 = plot_base_100(df_filtrado, selected_tickers=tickers_input)
    st.plotly_chart(fig_base100, use_container_width=True)

    with st.expander("📌 Leitura Estratégica & Contexto de Mercado"):
        st.markdown(
            "- **Setor Energético e Commodities:** Ativos atrelados a petróleo e combustíveis "
            "(como PETR4 e PRIO3) apresentaram forte descolamento altista devido ao ciclo global de alta da commodity "
            "e políticas operacionais robustas no triênio.\n"
            "- **Setores Cíclicos e Crédito:** Papéis vinculados a crédito bancário e varejo/locação "
            "enfrentaram compressão de margens decorrente da escalada da taxa básica de juros (Selic de 2% para 13,75% a.a.)."
        )

# ----------------------------------------------------------------------------
# ABA 2: MATRIZ RISCO X RETORNO & DISPERSÃO
# ----------------------------------------------------------------------------
with tab2:
    st.subheader("Matriz Risco x Retorno (Eficiência de Carteira)")
    st.markdown(
        "Avaliação do prêmio de retorno em relação à **Volatilidade Histórica Anualizada** "
        r"($\sigma \times \sqrt{252}$). O diâmetro de cada marcador reflete o **Volume Médio Diário Transacionado (R$)**."
    )

    fig_risco_retorno = plot_risk_return(df_filtrado)
    st.plotly_chart(fig_risco_retorno, use_container_width=True)

    st.markdown("---")
    st.subheader("Dispersão, Assimetria e Risco de Cauda dos Retornos Diários")
    st.markdown(
        "Inspecione a distribuição empírica dos retornos diários do ativo individual para diagnosticar "
        "eventos extremos de cauda (*fat tails* / leptocurtose) e assimetria estatística frente à curva gaussiana."
    )

    ativo_dist = st.selectbox(
        "Selecione o Ativo para Análise de Distribuição Diária:",
        options=sorted(df_filtrado["ticker"].unique()),
        key="sb_dist_retornos",
    )

    fig_dist = plot_daily_returns_distribution(df_filtrado, selected_ticker=ativo_dist)
    st.plotly_chart(fig_dist, use_container_width=True)

# ----------------------------------------------------------------------------
# ABA 3: RESILIÊNCIA, DRAWDOWN & ANÁLISE TÉCNICA
# ----------------------------------------------------------------------------
with tab3:
    st.subheader("Rebaixamento Máximo de Capital (Drawdown)")
    st.markdown(
        "O *Drawdown* mensura o percentual contínuo de perda acumulada a partir do topo histórico precedente "
        r"($\text{Drawdown}_t = (P_t - \text{Peak}_t)/\text{Peak}_t \le 0.0$). É a principal métrica para avaliar o risco de cauda e a preservação do investidor."
    )

    ativo_dd = st.selectbox(
        "Selecione o Ativo para Análise de Drawdown em Área (ou Geral):",
        options=["Todos os Ativos"] + sorted(df_filtrado["ticker"].unique()),
        key="sb_drawdown",
    )

    param_dd = None if ativo_dd == "Todos os Ativos" else ativo_dd
    fig_dd = plot_drawdown_matrix(df_filtrado, selected_ticker=param_dd)
    st.plotly_chart(fig_dd, use_container_width=True)

    st.markdown("---")
    st.subheader("Rastreamento Técnico: Médias Móveis (SMA 21 / SMA 50) e Volume")
    st.markdown(
        "Monitoramento do preço de fechamento ajustado sobreposto às médias móveis aritméticas "
        "de curto prazo (**SMA 21**) e médio prazo (**SMA 50**), acompanhadas pelo volume financeiro de liquidação."
    )

    ativo_trend = st.selectbox(
        "Selecione o Ativo para Inspeção Técnica:",
        options=sorted(df_filtrado["ticker"].unique()),
        key="sb_trend",
    )

    fig_trend = plot_technical_trend(df_filtrado, ticker=ativo_trend)
    st.plotly_chart(fig_trend, use_container_width=True)

# ----------------------------------------------------------------------------
# ABA 4: GOVERNANÇA, DICIONÁRIO & DADOS BRUTOS
# ----------------------------------------------------------------------------
with tab4:
    st.subheader("Dicionário Oficial de Dados (Metadados e Engenharia)")
    st.markdown(
        "Metadados e definições das 14 variáveis tratadas e modeladas no pipeline analítico:"
    )

    dicionario_dados = [
        {"Coluna": "date", "Tipo": "datetime64", "Descrição": "Data do pregão de negociação na B3 (formato YYYY-MM-DD)", "Fórmula": "Padronização temporal sem fuso"},
        {"Coluna": "ticker", "Tipo": "string", "Descrição": "Código oficial da ação negociada na B3 com sufixo .SA", "Fórmula": "Símbolo identificador"},
        {"Coluna": "setor", "Tipo": "string", "Descrição": "Macro-segmento econômico oficial de atuação", "Fórmula": "Mapeamento em 4 categorias"},
        {"Coluna": "open", "Tipo": "float64", "Descrição": "Preço de abertura do ativo no pregão (R$)", "Fórmula": "Cotação bruta saneada"},
        {"Coluna": "high", "Tipo": "float64", "Descrição": "Preço máximo registrado durante o pregão (R$)", "Fórmula": "Cotação máxima diária"},
        {"Coluna": "low", "Tipo": "float64", "Descrição": "Preço mínimo registrado durante o pregão (R$)", "Fórmula": "Cotação mínima diária"},
        {"Coluna": "adj_close", "Tipo": "float64", "Descrição": "Preço de fechamento ajustado por dividendos e JCP (R$)", "Fórmula": "Fechamento corporativo"},
        {"Coluna": "volume", "Tipo": "float64", "Descrição": "Volume financeiro transacionado na sessão (R$)", "Fórmula": "Liquidação financeira"},
        {"Coluna": "ret_diario", "Tipo": "float64", "Descrição": "Retorno percentual sobre o pregão imediatamente anterior", "Fórmula": "(P_t - P_{t-1}) / P_{t-1}"},
        {"Coluna": "base_100", "Tipo": "float64", "Descrição": "Índice de performance normalizada ancorado em 100", "Fórmula": "(P_t / P_0) * 100.0"},
        {"Coluna": "sma_21", "Tipo": "float64", "Descrição": "Média Móvel Simples de 21 pregões (curto prazo)", "Fórmula": "Rolling mean de 21 dias"},
        {"Coluna": "sma_50", "Tipo": "float64", "Descrição": "Média Móvel Simples de 50 pregões (médio prazo)", "Fórmula": "Rolling mean de 50 dias"},
        {"Coluna": "peak", "Tipo": "float64", "Descrição": "Preço máximo ajustado acumulado até o momento", "Fórmula": "cummax(adj_close)"},
        {"Coluna": "drawdown", "Tipo": "float64", "Descrição": "Percentual de queda a partir da máxima acumulada", "Fórmula": "(P_t - Peak_t) / Peak_t (<= 0.0)"},
    ]
    st.table(pd.DataFrame(dicionario_dados))

    st.markdown("---")
    st.subheader("Base de Dados Tabular Filtrada")
    st.markdown(
        f"Exibindo **{len(df_filtrado):,}** registros selecionados a partir dos filtros dinâmicos:"
    )

    st.dataframe(
        df_filtrado.sort_values(["ticker", "date"]),
        use_container_width=True,
        hide_index=True,
    )

    # Conversão para download em CSV
    csv_bytes = df_filtrado.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="📥 Exportar Dados Filtrados (CSV)",
        data=csv_bytes,
        file_name=f"b3_market_data_filtered_{start_dt}_{end_dt}.csv",
        mime="text/csv",
        use_container_width=True,
        help="Exporta o conjunto de dados filtrado em formato compatível com Excel e Power BI.",
    )


# ============================================================================
# 10. RODAPÉ DE GOVERNANÇA & LIMITAÇÕES DA ANÁLISE (CRITÉRIO 10)
# ============================================================================
st.markdown("---")
st.caption(
    "⚖️ **Aviso de Conformidade Metodológica & Limitações Analíticas (Itens 4.5 e 5.2 do Edital):** "
    "A presente amostra reflete o triênio 2021-2023, período marcado pelo choque macroeconômico de juros pós-pandemia "
    "(taxa Selic de 2,00% para 13,75% a.a.) e alta das commodities energéticas. As correlações empíricas observadas não "
    "implicam relação direta de causalidade mecânica nem constituem recomendação, consultoria ou indicação de alocação de investimentos."
)