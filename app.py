"""B3 Performance Analytics | Inteligência de Mercado & Séries Temporais.

Projeto Avaliativo Final de BI (Módulo 2) - Linha 2: Performance de Mercado
Responsável Técnica: Andressa Alves de Souza
Orientador Acadêmico: Prof. Sávio Ricardo Garcia

Backend resiliente de ingestão de dados de mercado da B3 (triênio 2021-2023).
Implementa conexão relacional primária (SQLAlchemy/PostgreSQL via Supabase),
contingência graciosa para CSV local via pathlib, blindagem de secrets,
feedback de interface com st.spinner e cache corporativo otimizado (@st.cache_data).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple

import pandas as pd
import streamlit as st

# Importação do módulo modular de visualizações construído no Card 4
try:
    import src.visualizations as vz
except ModuleNotFoundError:
    # Suporte a diferentes resoluções de sys.path no deploy
    import visualizations as vz  # type: ignore


# ============================================================================
# 1. CONFIGURAÇÃO EXECUTIVA DA PÁGINA (ST.SET_PAGE_CONFIG)
# Obrigatório: Primeira instrução de layout Streamlit executada
# ============================================================================
st.set_page_config(
    page_title="B3 Performance Analytics | Inteligência de Mercado",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Configuração de telemetria e auditoria de log no console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("B3_Core_Backend")


# ============================================================================
# 2. CAMADA RESILIENTE DE INGESTÃO DE DADOS (SQL + FALLBACK CSV + CACHE)
# ============================================================================
@st.cache_data(ttl=3600, show_spinner=False)
def load_market_data() -> Tuple[pd.DataFrame, str]:
    """Carrega a base de dados de mercado aplicando conexão resiliente com fallback.

    Fluxo de Conexão:
    1. Primária: Tentativa de consulta SQL via st.connection("postgresql", type="sql").
       Se secrets.toml não existir ou a conexão falhar, aciona a contingência sem quebrar.
    2. Fallback: Leitura segura da base local tratada via pathlib.Path.
    """
    df: pd.DataFrame | None = None
    origem_conexao: str = ""

    # ------------------------------------------------------------------------
    # TENTATIVA 1: Ingestão Primária via Conexão SQL / PostgreSQL (Supabase)
    # Protegido contra StreamlitSecretNotFoundError e falhas de conexão
    # ------------------------------------------------------------------------
    try:
        # Verifica se o arquivo/dicionário de secrets existe e possui a seção de conexão
        has_postgres = False
        try:
            if hasattr(st, "secrets") and "connections" in st.secrets and "postgresql" in st.secrets["connections"]:
                has_postgres = True
        except Exception:
            # Captura StreamlitSecretNotFoundError caso .streamlit/secrets.toml não exista
            has_postgres = False

        if has_postgres:
            logger.info("Iniciando tentativa de conexão primária SQL via st.connection...")
            conn = st.connection("postgresql", type="sql")
            query = "SELECT * FROM b3_stocks_processed ORDER BY date ASC, ticker ASC;"
            df = conn.query(query, ttl=3600)

            if df is not None and not df.empty:
                origem_conexao = "PostgreSQL (Nuvem / Supabase)"
                logger.info("Ingestão remota concluída com sucesso via SQL (%d registros).", len(df))
        else:
            logger.info("Configuração 'connections.postgresql' não encontrada em st.secrets. Acionando base local...")

    except Exception as exc:
        logger.warning(
            "Falha ou ausência na conexão primária SQL Supabase (%s). Acionando protocolo de contingência...",
            exc,
        )
        df = None

    # ------------------------------------------------------------------------
    # TENTATIVA 2: Protocolo de Contingência Graciosa (Fallback para CSV Local)
    # ------------------------------------------------------------------------
    if df is None or df.empty:
        try:
            root_dir = Path(__file__).resolve().parent
            csv_path = root_dir / "data" / "processed" / "b3_stocks_processed.csv"

            if not csv_path.exists():
                raise FileNotFoundError(
                    f"Arquivo processed de contingência não localizado no caminho: {csv_path}"
                )

            logger.info("Carregando base de contingência local: %s", csv_path)
            df = pd.read_csv(csv_path)
            origem_conexao = "CSV Local de Contingência"
            logger.info("Ingestão de contingência local concluída (%d registros).", len(df))

        except Exception as err:
            logger.critical("Falha crítica irrecuperável na ingestão de dados: %s", err)
            st.error(
                "🚨 **Erro Crítico de Infraestrutura de Dados:**\n\n"
                "Não foi possível estabelecer conexão com o banco relacional nem carregar "
                "o repositório local de contingência. Verifique os logs do console."
            )
            st.stop()

    # ------------------------------------------------------------------------
    # SANEAMENTO E PADRONIZAÇÃO ESTRUTURAL PÓS-CARGA
    # ------------------------------------------------------------------------
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    df = df.sort_values(by=["date", "ticker"]).reset_index(drop=True)

    numeric_cols = [
        "open", "high", "low", "adj_close", "volume",
        "ret_diario", "base_100", "sma_21", "sma_50", "peak", "drawdown"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df, origem_conexao

# ============================================================================
# 3. EXECUÇÃO DA CARGA COM FEEDBACK VISUAL AO USUÁRIO (ST.SPINNER)
# ============================================================================
with st.spinner("Conectando ao repositório de dados de mercado..."):
    df_market, data_source = load_market_data()


# ============================================================================
# 4. BARRA LATERAL (SIDEBAR): CONTEXTO INSTITUCIONAL & EVIDÊNCIAS DE GOVERNANÇA
# ============================================================================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/bullish.png", width=72)
    st.markdown("## **B3 Market Intelligence**")
    st.markdown("---")

    # Metadados de Autoria e Governança do Edital
    st.markdown("### 🏛️ **Governança do Projeto**")
    st.markdown(
        """
        - **Responsável Técnica:**  
          `Andressa Alves de Souza`
        - **Orientação Pedagógica:**  
          `Prof. Sávio Ricardo Garcia`
        - **Linha Temática:**  
          `Linha 2 — Performance B3`
        - **Recorte Temporal:**  
          `01/01/2021 a 31/12/2023`
        - **Ativos Monitorados:**  
          `12 Ações em 4 Setores`
        """
    )
    st.markdown("---")

    # Status Dinâmico de Resiliência de Conexão
    st.markdown("### 🔌 **Status da Conexão**")
    if "PostgreSQL" in data_source:
        st.success(f"🟢 **Conectado:** {data_source}")
    else:
        st.info(f"🟡 **Ativo:** {data_source}")

    st.caption("Cache Corporativo: `@st.cache_data(ttl=3600)`")
    st.markdown("---")

    # Placeholder para os filtros dinâmicos da interface (Card 6)
    st.markdown("### ⚙️ **Filtros de Mercado**")
    st.info("Os filtros dinâmicos de ativos, datas e setores serão integrados no **Card 6**.")


# ============================================================================
# 5. CABEÇALHO EXECUTIVO & METADADOS DA APLICAÇÃO
# ============================================================================
col_header, col_badge = st.columns([0.78, 0.22])

with col_header:
    st.title("📈 B3 Performance Analytics | Inteligência de Mercado")
    st.markdown(
        "##### Plataforma Analítica de Performance de Ações, Volatilidade e Séries Temporais"
    )

with col_badge:
    st.markdown("<br>", unsafe_allow_html=True)
    st.metric(
        label="Status do Repositório",
        value="Base Consolidada",
        delta="3 Anos (8.940 pregões)",
        delta_color="normal",
    )

st.markdown("---")


# ============================================================================
# 6. ESTRUTURA BASE MODULAR & VISUALIZAÇÕES ANALÍTICAS
# ============================================================================
tab_base100, tab_risco, tab_distribuicao, tab_drawdown, tab_sma = st.tabs(
    [
        "📈 Performance (Base 100)",
        "⚖️ Risco x Retorno",
        "📊 Distribuição de Retornos",
        "📉 Drawdown Máximo (Small Multiples)",
        "🔍 Análise Técnica (Médias Móveis)",
    ]
)

with tab_base100:
    st.markdown("#### Evolução Comparativa Normalizada em Base 100")
    fig_base100 = vz.plot_base_100(df_market)
    st.plotly_chart(fig_base100, width="stretch")

with tab_risco:
    st.markdown("#### Matriz de Eficiência: Volatilidade Anualizada vs. Retorno Acumulado")
    fig_risco = vz.plot_risk_return(df_market)
    st.plotly_chart(fig_risco, width="stretch")

with tab_distribuicao:
    st.markdown("#### Dispersão, Assimetria e Frequência dos Retornos Diários")
    col_sel_ret, _ = st.columns([0.3, 0.7])
    with col_sel_ret:
        ativo_dist = st.selectbox(
            "Filtrar Ativo para Distribuição:",
            options=["Consolidado da Carteira"] + sorted(df_market["ticker"].unique().tolist()),
            index=0,
            key="sb_dist",
        )
    ticker_param = None if ativo_dist == "Consolidado da Carteira" else ativo_dist
    fig_dist = vz.plot_daily_returns_distribution(df_market, selected_ticker=ticker_param)
    st.plotly_chart(fig_dist, width="stretch")

with tab_drawdown:
    st.markdown("#### Painel Matricial de Drawdown Máximo — 12 Ativos (4 Linhas × 3 Colunas)")
    fig_dd = vz.plot_drawdown_small_multiples(df_market)
    st.plotly_chart(fig_dd, width="stretch")

with tab_sma:
    st.markdown("#### Rastreamento Técnico com SMA 21 e SMA 50")
    col_sel_sma, _ = st.columns([0.3, 0.7])
    with col_sel_sma:
        ativo_sma = st.selectbox(
            "Selecione o Ativo para Análise Técnica:",
            options=sorted(df_market["ticker"].unique().tolist()),
            index=df_market["ticker"].unique().tolist().index("PETR4.SA") if "PETR4.SA" in df_market["ticker"].values else 0,
            key="sb_sma",
        )
    fig_sma = vz.plot_technical_trend(df_market, ticker=ativo_sma)
    st.plotly_chart(fig_sma, width="stretch")

# ============================================================================
# 7. RODAPÉ DE CONFORMIDADE, LGPD & LIMITAÇÕES METODOLÓGICAS
# ============================================================================
st.markdown("---")
st.markdown(
    """
    <div style="background-color: #F8FAFC; border-left: 4px solid #3B82F6; padding: 12px 18px; border-radius: 4px;">
        <p style="margin: 0; font-size: 0.85rem; color: #475569; line-height: 1.4;">
            <strong>⚠️ Termo de Conformidade Analítica e Limitações Metodológicas (Item 4.5 e 5.2 do Edital):</strong><br>
            As análises apresentadas nesta aplicação têm finalidade estritamente acadêmica e de inteligência analítica,
            não configurando recomendação de alocação, assessoria ou solicitação de compra/venda de ativos mobiliários.
            O recorte amostral compreende os pregões de 2021 a 2023, sob dinâmica macroeconômica específica (ciclo de aperto
            monetário e valorização de commodities energéticas). Correlações estatísticas empíricas observadas não
            pressupõem causalidade determinística nem garantem rentabilidade futura.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)