"""Módulo de Visualizações Analíticas Financeiras (B3) com Plotly.

Projeto Avaliativo Final de BI (Módulo 2) - Linha 2: Performance de Mercado
Orientador: Prof. Sávio Ricardo Garcia
Responsável Técnica: Andressa Alves de Souza

Este módulo fornece funções puras e desacopladas para gerar os 5 elementos
visuais interativos exigidos, sem acoplamento com o Streamlit.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ============================================================================
# CONSTANTES DE DESIGN CORPORATIVO & PALETAS
# ============================================================================

THEME_TEMPLATE: str = "plotly_white"

SECTOR_COLORS: Dict[str, str] = {
    "Petróleo, Gás & Energia": "#00875A",          # Verde Petróleo/Esmeralda
    "Bens de Capital & Indústria": "#0052CC",       # Azul Corporativo
    "Materiais Básicos & Siderurgia": "#FF8B00",   # Âmbar Industrial
    "Materiais Básicos & Siderurgia/Papel": "#FF8B00",
    "Financeiro, Consumo & Locação": "#6554C0",     # Violeta Executivo
}

BENCHMARK_COLORS: Dict[str, str] = {
    "PETR4.SA": "#00A86B",  # Verde Esmeralda (Líder em Retorno e Sharpe)
    "PRIO3.SA": "#2A60E4",  # Azul Royal (Segundo colocado em Retorno)
    "BBDC4.SA": "#D9383A",  # Vermelho Alerta (Menor performance acumulada)
    "EGIE3.SA": "#008080",  # Azul Petróleo/Teal (Mais resiliente / Menor Drawdown)
}

DEFAULT_PALETTE: List[str] = [
    "#4A5568", "#718096", "#A0AEC0", "#2B6CB0",
    "#C53030", "#DD6B20", "#319795", "#805AD5",
]


# ============================================================================
# FUNÇÕES DE VISUALIZAÇÃO PURAS (CRITÉRIO 8)
# ============================================================================

def plot_base_100(
    df: pd.DataFrame,
    selected_tickers: Optional[List[str]] = None,
) -> go.Figure:
    """Gera gráfico comparativo de séries temporais normalizadas em Base 100.

    Permite a comparação da evolução patrimonial relativa ancorada em 100.0 no
    primeiro pregão de 2021, destacando ativos extremos e suporte de capital.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame estruturado contendo 'date', 'ticker', 'base_100'.
    selected_tickers : Optional[List[str]], optional
        Lista restrita de papéis para renderizar. Se None, plota todos do DataFrame.

    Returns
    -------
    go.Figure
        Figura Plotly configurada com curvas interativas e linha guia em 100.0.
    """
    data = df.copy()
    if selected_tickers is not None:
        data = data[data["ticker"].isin(selected_tickers)]

    fig = go.Figure()

    # Ordenação dos ativos para consistência visual
    tickers_present = sorted(data["ticker"].unique())

    for idx, ticker in enumerate(tickers_present):
        subset = data[data["ticker"] == ticker].sort_values("date")
        if subset.empty:
            continue

        # Definição de cores analíticas (Destaques da EDA vs. Paleta Neutra)
        if ticker in BENCHMARK_COLORS:
            line_color = BENCHMARK_COLORS[ticker]
            line_width = 2.8
        else:
            line_color = DEFAULT_PALETTE[idx % len(DEFAULT_PALETTE)]
            line_width = 1.5

        fig.add_trace(
            go.Scatter(
                x=subset["date"],
                y=subset["base_100"],
                mode="lines",
                name=ticker,
                line=dict(color=line_color, width=line_width),
                hovertemplate=(
                    f"<b>{ticker}</b><br>"
                    "Data: %{x|%d/%m/%Y}<br>"
                    "Base 100: <b>%{y:.2f} pts</b>"
                    "<extra></extra>"
                ),
            )
        )

    # Linha guia horizontal de Preservação de Capital (Nível 100.0)
    fig.add_hline(
        y=100.0,
        line_dash="dash",
        line_color="#E53E3E",
        line_width=1.8,
        annotation_text="Preservação de Capital (100.0 pts)",
        annotation_position="bottom right",
        annotation_font=dict(size=11, color="#C53030", family="Arial"),
    )

    fig.update_layout(
        template=THEME_TEMPLATE,
        title=dict(
            text="<b>Performance Relativa Normalizada (Base 100) — Triênio 2021-2023</b>",
            x=0.02,
            font=dict(size=16, color="#1A202C"),
        ),
        xaxis=dict(
            title="Data do Pregão",
            gridcolor="#EDF2F7",
            showline=True,
            linecolor="#CBD5E0",
            rangeselector=dict(
                buttons=list([
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="1A", step="year", stepmode="backward"),
                    dict(step="all", label="Tudo"),
                ])
            ),
        ),
        yaxis=dict(
            title="Índice Base 100 (pts)",
            gridcolor="#EDF2F7",
            showline=True,
            linecolor="#CBD5E0",
            ticksuffix=" pts",
        ),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0.0,
            font=dict(size=10),
        ),
        margin=dict(l=40, r=40, t=80, b=40),
    )
    return fig


def plot_risk_return(df: pd.DataFrame) -> go.Figure:
    """Gera matriz de dispersão Risco (Volatilidade Anualizada) vs. Retorno Acumulado.

    Calcula a volatilidade anualizada considerando 252 pregões úteis e agrega
    o retorno total e volume financeiro médio por papel e setor econômico.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame contendo 'ticker', 'setor', 'ret_diario', 'volume' e 'adj_close'.

    Returns
    -------
    go.Figure
        Gráfico de dispersão com bolhas dimensionadas por volume diário em R$.
    """
    summary_list = []

    for ticker, group in df.groupby("ticker"):
        sorted_group = group.sort_values("date")
        p_inicial = sorted_group["adj_close"].iloc[0]
        p_final = sorted_group["adj_close"].iloc[-1]
        ret_acumulado = ((p_final / p_inicial) - 1.0) * 100.0

        # Volatilidade Anualizada (% a.a. = sigma * sqrt(252) * 100)
        vol_anualizada = float(sorted_group["ret_diario"].std() * math.sqrt(252) * 100.0)
        vol_medio_diario = float(sorted_group["volume"].mean())
        setor = sorted_group["setor"].iloc[0]

        summary_list.append(
            {
                "ticker": ticker,
                "setor": setor,
                "ret_acumulado": ret_acumulado,
                "vol_anualizada": vol_anualizada,
                "volume_medio": vol_medio_diario,
            }
        )

    summary_df = pd.DataFrame(summary_list)

    fig = go.Figure()

    # Renderiza por setor para construir legenda corporativa limpa
    for setor, group in summary_df.groupby("setor"):
        marker_color = SECTOR_COLORS.get(setor, "#4A5568")

        # Escala segura de dimensão do marker
        max_vol = summary_df["volume_medio"].max()
        marker_sizes = 18 + (group["volume_medio"] / (max_vol if max_vol > 0 else 1.0)) * 32

        fig.add_trace(
            go.Scatter(
                x=group["vol_anualizada"],
                y=group["ret_acumulado"],
                mode="markers+text",
                name=setor,
                text=group["ticker"],
                textposition="top center",
                textfont=dict(size=11, family="Arial Black", color="#2D3748"),
                marker=dict(
                    size=marker_sizes,
                    color=marker_color,
                    opacity=0.85,
                    line=dict(width=1.5, color="#1A202C"),
                ),
                customdata=np.stack(
                    (group["volume_medio"], group["setor"]), axis=-1
                ),
                hovertemplate=(
                    "<b>Ativo: %{text}</b><br>"
                    "Setor: %{customdata[1]}<br>"
                    "Retorno Acumulado: <b>%{y:.2f}%</b><br>"
                    "Volatilidade: <b>%{x:.2f}% a.a.</b><br>"
                    "Volume Médio: <b>R$ %{customdata[0]:,.2f}</b>"
                    "<extra></extra>"
                ),
            )
        )

    # Linha de referência horizontal no ponto de equilíbrio (0.0% de Retorno)
    fig.add_hline(
        y=0.0,
        line_dash="dot",
        line_color="#A0AEC0",
        line_width=1.2,
    )

    fig.update_layout(
        template=THEME_TEMPLATE,
        title=dict(
            text="<b>Matriz Risco x Retorno — Eficiência e Volatilidade Anualizada</b>",
            x=0.02,
            font=dict(size=16, color="#1A202C"),
        ),
        xaxis=dict(
            title="Volatilidade Histórica Anualizada (σ x √252) [% a.a.]",
            ticksuffix="%",
            gridcolor="#EDF2F7",
            showline=True,
            linecolor="#CBD5E0",
        ),
        yaxis=dict(
            title="Retorno Acumulado no Período (%)",
            ticksuffix="%",
            gridcolor="#EDF2F7",
            showline=True,
            linecolor="#CBD5E0",
        ),
        legend=dict(
            title="Setor Econômico",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0.0,
            font=dict(size=10),
        ),
        margin=dict(l=40, r=40, t=80, b=40),
    )
    return fig


def plot_daily_returns_distribution(
    df: pd.DataFrame,
    selected_ticker: Optional[str] = None,
) -> go.Figure:
    """Gera painel vertical de distribuição dos retornos diários (Boxplot + Histograma).

    Permite analisar assimetria, curtose e risco de cauda (fat tails) na série diária.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame contendo 'date', 'ticker', 'ret_diario'.
    selected_ticker : Optional[str], optional
        Ticker para foco. Se None, considera a agregação da carteira completa.

    Returns
    -------
    go.Figure
        Painel vertical acoplado com Boxplot marginal superior e Histograma inferior.
    """
    if selected_ticker:
        data = df[df["ticker"] == selected_ticker].copy()
        titulo_ativo = f"Ativo {selected_ticker}"
        plot_color = BENCHMARK_COLORS.get(selected_ticker, "#2B6CB0")
    else:
        data = df.copy()
        titulo_ativo = "Consolidado da Carteira (12 Ativos)"
        plot_color = "#3182CE"

    # Remove primeiro pregão com retorno zero caso presente
    data = data.dropna(subset=["ret_diario"])

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.25, 0.75],
    )

    # Subplot Superior: Boxplot horizontal
    fig.add_trace(
        go.Box(
            x=data["ret_diario"],
            name="Dispersão",
            orientation="h",
            marker=dict(color=plot_color, size=4, opacity=0.6),
            line=dict(color="#1A202C", width=1.5),
            boxmean=True,
            hovertemplate="Retorno Diário: %{x:.2%}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    # Subplot Inferior: Histograma de Frequência
    fig.add_trace(
        go.Histogram(
            x=data["ret_diario"],
            name="Frequência",
            nbinsx=60,
            marker=dict(
                color=plot_color,
                opacity=0.75,
                line=dict(color="#FFFFFF", width=1.0),
            ),
            hovertemplate=(
                "Intervalo: %{x:.2%}<br>"
                "Sessões: <b>%{y} pregões</b>"
                "<extra></extra>"
            ),
        ),
        row=2,
        col=1,
    )

    # Marcador vertical no centro neutro (0.00%)
    fig.add_vline(
        x=0.0,
        line_dash="dash",
        line_color="#E53E3E",
        line_width=1.5,
    )

    fig.update_layout(
        template=THEME_TEMPLATE,
        title=dict(
            text=f"<b>Distribuição Estatística dos Retornos Diários — {titulo_ativo}</b>",
            x=0.02,
            font=dict(size=16, color="#1A202C"),
        ),
        showlegend=False,
        bargap=0.05,
        margin=dict(l=40, r=40, t=70, b=40),
    )

    fig.update_xaxes(
        tickformat=".1%",
        title_text="Retorno Percentual Diário (%)",
        gridcolor="#EDF2F7",
        row=2,
        col=1,
    )
    fig.update_yaxes(title_text="Frequência (Dias)", gridcolor="#EDF2F7", row=2, col=1)
    fig.update_yaxes(showticklabels=False, row=1, col=1)

    return fig


def plot_drawdown_matrix(
    df: pd.DataFrame,
    selected_ticker: Optional[str] = None,
) -> go.Figure:
    """Gera visualização de rebaixamento percentual contínuo a partir do pico histórico.

    Identifica a extensão de perda acumulada (Drawdown <= 0.0%) e os fundos de estresse.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame contendo 'date', 'ticker', 'drawdown'.
    selected_ticker : Optional[str], optional
        Ticker específico para visualização em área. Se None, compara múltiplos papéis.

    Returns
    -------
    go.Figure
        Gráfico de área sombreada ou linhas com preenchimento abaixo de zero.
    """
    fig = go.Figure()

    if selected_ticker:
        subset = df[df["ticker"] == selected_ticker].sort_values("date")
        fill_color = "rgba(229, 62, 62, 0.25)"
        line_color = "#E53E3E"

        fig.add_trace(
            go.Scatter(
                x=subset["date"],
                y=subset["drawdown"],
                mode="lines",
                name=f"Drawdown {selected_ticker}",
                line=dict(color=line_color, width=1.8),
                fill="tozeroy",
                fillcolor=fill_color,
                hovertemplate=(
                    f"<b>{selected_ticker}</b><br>"
                    "Data: %{x|%d/%m/%Y}<br>"
                    "Drawdown: <b>%{y:.2%}</b>"
                    "<extra></extra>"
                ),
            )
        )
        titulo = f"<b>Curva Contínua de Rebaixamento Máximo (Drawdown) — {selected_ticker}</b>"
    else:
        for idx, ticker in enumerate(sorted(df["ticker"].unique())):
            subset = df[df["ticker"] == ticker].sort_values("date")
            line_color = BENCHMARK_COLORS.get(
                ticker, DEFAULT_PALETTE[idx % len(DEFAULT_PALETTE)]
            )

            fig.add_trace(
                go.Scatter(
                    x=subset["date"],
                    y=subset["drawdown"],
                    mode="lines",
                    name=ticker,
                    line=dict(width=1.5, color=line_color),
                    hovertemplate=(
                        f"<b>{ticker}</b><br>"
                        "Data: %{x|%d/%m/%Y}<br>"
                        "Drawdown: <b>%{y:.2%}</b>"
                        "<extra></extra>"
                    ),
                )
            )
        titulo = "<b>Evolução Comparativa de Drawdown dos Ativos da B3 (2021-2023)</b>"

    fig.update_layout(
        template=THEME_TEMPLATE,
        title=dict(text=titulo, x=0.02, font=dict(size=16, color="#1A202C")),
        xaxis=dict(
            title="Data do Pregão",
            gridcolor="#EDF2F7",
            showline=True,
            linecolor="#CBD5E0",
        ),
        yaxis=dict(
            title="Queda a partir do Topo Acumulado (%)",
            tickformat=".0%",
            gridcolor="#EDF2F7",
            showline=True,
            linecolor="#CBD5E0",
            range=[float(df["drawdown"].min() * 1.1), 0.02],
        ),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0.0,
            font=dict(size=10),
        ),
        margin=dict(l=40, r=40, t=80, b=40),
    )
    return fig


def plot_technical_trend(df: pd.DataFrame, ticker: str) -> go.Figure:
    """Gera gráfico multilinha de rastreamento técnico com Médias Móveis e Volume.

    Integra Cotação de Fechamento Ajustada, Médias Móveis Simples (SMA 21 e SMA 50),
    painel secundário com Volume Financeiro diário e range slider para inspeção.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame contendo 'date', 'ticker', 'adj_close', 'sma_21', 'sma_50', 'volume'.
    ticker : str
        Símbolo oficial do ativo analisado.

    Returns
    -------
    go.Figure
        Figura com 2 subplots verticais acoplados com slider de zoom temporal.
    """
    subset = df[df["ticker"] == ticker].sort_values("date").copy()

    if subset.empty:
        raise ValueError(f"Ativo {ticker} não encontrado na base de dados.")

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.72, 0.28],
    )

    # 1. Linha Principal: Fechamento Ajustado
    fig.add_trace(
        go.Scatter(
            x=subset["date"],
            y=subset["adj_close"],
            mode="lines",
            name="Fechamento Ajustado",
            line=dict(color="#1A202C", width=2.2),
            hovertemplate="Fechamento: <b>R$ %{y:.2f}</b><extra></extra>",
        ),
        row=1,
        col=1,
    )

    # 2. SMA 21: Suporte dinâmico de curto prazo
    fig.add_trace(
        go.Scatter(
            x=subset["date"],
            y=subset["sma_21"],
            mode="lines",
            name="SMA 21 (Curto Prazo)",
            line=dict(color="#ED8936", width=1.6, dash="dash"),
            hovertemplate="SMA 21: <b>R$ %{y:.2f}</b><extra></extra>",
        ),
        row=1,
        col=1,
    )

    # 3. SMA 50: Tendência primária de médio prazo
    fig.add_trace(
        go.Scatter(
            x=subset["date"],
            y=subset["sma_50"],
            mode="lines",
            name="SMA 50 (Médio Prazo)",
            line=dict(color="#38A169", width=1.6, dash="dot"),
            hovertemplate="SMA 50: <b>R$ %{y:.2f}</b><extra></extra>",
        ),
        row=1,
        col=1,
    )

    # 4. Volume Financeiro diário (Subplot inferior)
    fig.add_trace(
        go.Bar(
            x=subset["date"],
            y=subset["volume"],
            name="Volume Financeiro",
            marker=dict(color="#A0AEC0", opacity=0.7),
            hovertemplate="Volume: <b>R$ %{y:,.2f}</b><extra></extra>",
        ),
        row=2,
        col=1,
    )

    fig.update_layout(
        template=THEME_TEMPLATE,
        title=dict(
            text=f"<b>Rastreamento Técnico e Médias Móveis — {ticker}</b>",
            x=0.02,
            font=dict(size=16, color="#1A202C"),
        ),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0.0,
            font=dict(size=10),
        ),
        margin=dict(l=40, r=40, t=80, b=40),
        xaxis2=dict(
            rangeslider=dict(visible=True, thickness=0.06),
            type="date",
            title="Data do Pregão",
            gridcolor="#EDF2F7",
        ),
    )

    fig.update_yaxes(
        title_text="Cotação (R$)",
        tickprefix="R$ ",
        gridcolor="#EDF2F7",
        row=1,
        col=1,
    )
    fig.update_yaxes(
        title_text="Volume (R$)",
        tickformat="~s",
        tickprefix="R$ ",
        gridcolor="#EDF2F7",
        row=2,
        col=1,
    )

    return fig


# ============================================================================
# BLOCO DE VALIDAÇÃO E AUDITORIA AUTÔNOMA
# ============================================================================

if __name__ == "__main__":
    print("-" * 75)
    print("INICIALIZANDO AUDITORIA TÉCNICA DO MÓDULO: src/visualizations.py")
    print("-" * 75)

    # Resolução estrita por caminho relativo via pathlib.Path (Critério 7)
    base_dir = Path(__file__).resolve().parent.parent
    data_path = base_dir / "data" / "processed" / "b3_stocks_processed.csv"

    if not data_path.exists():
        raise FileNotFoundError(
            f"Arquivo processed não localizado em: {data_path}.\n"
            "Execute previamente o pipeline de ETL em src/etl.py."
        )

    print(f"[OK] Base de dados identificada: {data_path}")
    df_test = pd.read_csv(data_path)
    df_test["date"] = pd.to_datetime(df_test["date"])

    print(f"[INFO] Registros lidos: {len(df_test):,} linhas | Ativos: {df_test['ticker'].nunique()}")

    # Validação 1: Base 100
    fig1 = plot_base_100(df_test)
    assert len(fig1.data) >= 12, "Erro: Quantidade insuficiente de séries na Base 100."
    print("  ✓ Gráfico 1 (plot_base_100): Compilado com sucesso.")

    # Validação 2: Risco x Retorno
    fig2 = plot_risk_return(df_test)
    assert len(fig2.data) >= 4, "Erro: Quantidade insuficiente de setores no Risco x Retorno."
    print("  ✓ Gráfico 2 (plot_risk_return): Compilado com sucesso.")

    # Validação 3: Distribuição dos Retornos Diários
    fig3 = plot_daily_returns_distribution(df_test, selected_ticker="PETR4.SA")
    assert len(fig3.data) == 2, "Erro: Subplots de boxplot e histograma inconsistentes."
    print("  ✓ Gráfico 3 (plot_daily_returns_distribution): Compilado com sucesso.")

    # Validação 4: Drawdown Matrix
    fig4 = plot_drawdown_matrix(df_test, selected_ticker="EGIE3.SA")
    assert len(fig4.data) >= 1, "Erro: Gráfico de Drawdown não compilou os dados."
    print("  ✓ Gráfico 4 (plot_drawdown_matrix): Compilado com sucesso.")

    # Validação 5: Tendência Técnica com SMA 21/50 e Volume
    fig5 = plot_technical_trend(df_test, ticker="PETR4.SA")
    assert len(fig5.data) == 4, "Erro: Devem existir 4 traces (Preço, SMA21, SMA50, Volume)."
    print("  ✓ Gráfico 5 (plot_technical_trend): Compilado com sucesso.")

    print("-" * 75)
    print("AUDITORIA CONCLUÍDA: Todos os 5 elementos visuais foram validados!")
    print("-" * 75)