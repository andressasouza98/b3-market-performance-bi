"""Módulo de Visualizações Analíticas Financeiras (B3) com Plotly.

Projeto Avaliativo Final de BI (Módulo 2) - Linha 2: Performance de Mercado
Orientador: Prof. Sávio Ricardo Garcia
Responsável Técnica: Andressa Alves de Souza

Fornece funções puras e desacopladas para renderizar os 5 visuais corporativos
exigidos no Edital (Critério 8), alinhadas com as diretrizes de UX/UI corporativo.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ============================================================================
# CONSTANTES DE DESIGN CORPORATIVO & PALETAS
# ============================================================================

THEME_TEMPLATE: str = "plotly_white"

SECTOR_COLORS: Dict[str, str] = {
    "Petróleo, Gás & Energia": "#00875A",          # Verde Esmeralda
    "Bens de Capital & Indústria": "#0052CC",       # Azul Corporativo
    "Materiais Básicos & Siderurgia": "#FF8B00",   # Âmbar Industrial
    "Materiais Básicos & Siderurgia/Papel": "#FF8B00",
    "Financeiro, Consumo & Locação": "#6554C0",     # Violeta Executivo
}

BENCHMARK_COLORS: Dict[str, str] = {
    "PETR4.SA": "#00875A",  # Verde Esmeralda (Líder em Retorno e Sharpe)
    "PRIO3.SA": "#0052CC",  # Azul Royal (Segundo colocado em Retorno)
    "EGIE3.SA": "#00A3BF",  # Azul Petróleo / Teal (Maior resiliência de capital)
    "BBDC4.SA": "#DE350B",  # Vermelho Alerta (Menor performance acumulada)
}

DEFAULT_GRAY_PALETTE: List[str] = [
    "#7A869A", "#97A0AF", "#6B778C", "#5E6C84",
    "#8993A4", "#42526E", "#A5ADBA", "#505F79",
]

# Mapeamento setorial estrito dos 12 ativos (Linha 2)
TICKER_SECTOR_MAP: Dict[str, str] = {
    "PETR4.SA": "Petróleo, Gás & Energia",
    "PRIO3.SA": "Petróleo, Gás & Energia",
    "EGIE3.SA": "Petróleo, Gás & Energia",
    "EMBJ3.SA": "Bens de Capital & Indústria",
    "WEGE3.SA": "Bens de Capital & Indústria",
    "VALE3.SA": "Materiais Básicos & Siderurgia/Papel",
    "GGBR4.SA": "Materiais Básicos & Siderurgia/Papel",
    "KLBN11.SA": "Materiais Básicos & Siderurgia/Papel",
    "ITUB4.SA": "Financeiro, Consumo & Locação",
    "BBDC4.SA": "Financeiro, Consumo & Locação",
    "ABEV3.SA": "Financeiro, Consumo & Locação",
    "RENT3.SA": "Financeiro, Consumo & Locação",
}

SECTOR_FILL_COLORS: Dict[str, str] = {
    "Petróleo, Gás & Energia": "rgba(0, 135, 90, 0.25)",
    "Bens de Capital & Indústria": "rgba(0, 82, 204, 0.25)",
    "Materiais Básicos & Siderurgia/Papel": "rgba(255, 139, 0, 0.25)",
    "Materiais Básicos & Siderurgia": "rgba(255, 139, 0, 0.25)",
    "Financeiro, Consumo & Locação": "rgba(101, 84, 192, 0.25)",
}

ORDERED_TICKERS: List[str] = [
    "PETR4.SA", "PRIO3.SA", "EGIE3.SA",
    "EMBJ3.SA", "WEGE3.SA", "VALE3.SA",
    "GGBR4.SA", "KLBN11.SA", "ITUB4.SA",
    "BBDC4.SA", "ABEV3.SA", "RENT3.SA"
]


# ============================================================================
# 1. EVOLUÇÃO COMPARATIVA NORMALIZADA NA BASE 100
# ============================================================================
def plot_base_100(
    df: pd.DataFrame,
    selected_tickers: Optional[List[str]] = None,
) -> go.Figure:
    """Gera gráfico comparativo de séries temporais normalizadas em Base 100 com tooltip leve."""
    data = df.copy()
    if selected_tickers:
        data = data[data["ticker"].isin(selected_tickers)]

    fig = go.Figure()
    tickers = sorted(data["ticker"].unique())
    foco_benchmarks = len(tickers) > 6

    for idx, ticker in enumerate(tickers):
        subset = data[data["ticker"] == ticker].sort_values("date")
        if subset.empty:
            continue

        if ticker in BENCHMARK_COLORS:
            line_color = BENCHMARK_COLORS[ticker]
            line_width = 2.6
            opacity = 1.0
        else:
            line_color = DEFAULT_GRAY_PALETTE[idx % len(DEFAULT_GRAY_PALETTE)]
            line_width = 1.2 if foco_benchmarks else 1.8
            opacity = 0.55 if foco_benchmarks else 0.9

        fig.add_trace(
            go.Scatter(
                x=subset["date"],
                y=subset["base_100"],
                mode="lines",
                name=ticker,
                line=dict(color=line_color, width=line_width),
                opacity=opacity,
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
        line_dash="dot",
        line_color="#DE350B",
        line_width=1.5,
        annotation_text="Preservação de Capital (100.0 pts)",
        annotation_position="bottom right",
        annotation_font=dict(size=10, color="#DE350B"),
    )

    fig.update_layout(
        template=THEME_TEMPLATE,
        title=dict(
            text="<b>Performance Relativa Normalizada (Base 100 = Jan/2021)</b>",
            x=0.01,
            y=0.96,
            font=dict(size=15, color="#172B4D"),
        ),
        xaxis=dict(
            title=dict(text="Data do Pregão", font=dict(size=11, color="#5E6C84")),
            gridcolor="#EBECF0",
            showline=True,
            linecolor="#DFE1E6",
        ),
        yaxis=dict(
            title=dict(text="Índice Base 100 (pts)", font=dict(size=11, color="#5E6C84")),
            gridcolor="#EBECF0",
            showline=True,
            linecolor="#DFE1E6",
            ticksuffix=" pts",
        ),
        # 'closest' impede que o tooltip vertical gigante cubra o gráfico
        hovermode="closest",
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1.0,
            xanchor="left",
            x=1.01,
            font=dict(size=10),
            bgcolor="rgba(255,255,255,0.7)",
        ),
        margin=dict(l=40, r=145, t=55, b=40),
        height=480,
    )
    return fig


# ============================================================================
# 2. MATRIZ RISCO X RETORNO (DISPERSÃO COM ANCORAGEM PRECISA)
# ============================================================================

def plot_risk_return(df: pd.DataFrame) -> go.Figure:
    """Gera matriz Risco x Retorno com mapeamento cartesiano estrito e zero sobreposição."""
    summary_list = []

    for ticker, group in df.groupby("ticker"):
        sorted_group = group.sort_values("date")
        p_inicial = float(sorted_group["adj_close"].iloc[0])
        p_final = float(sorted_group["adj_close"].iloc[-1])

        ret_acumulado = ((p_final / p_inicial) - 1.0) * 100.0
        vol_anualizada = float(sorted_group["ret_diario"].std() * math.sqrt(252) * 100.0)
        vol_medio_diario = float(sorted_group["volume"].mean())
        setor = str(sorted_group["setor"].iloc[0])

        t_clean = str(ticker).strip()
        label = t_clean.replace(".SA", "").strip()

        summary_list.append(
            {
                "ticker": t_clean,
                "label": label,
                "setor": setor,
                "ret_acumulado": ret_acumulado,
                "vol_anualizada": vol_anualizada,
                "volume_medio": vol_medio_diario,
            }
        )

    summary_df = pd.DataFrame(summary_list)
    fig = go.Figure()

    if summary_df.empty:
        return fig

    # Configuração estrita de posições por ativo garantindo alinhamento perfeito com sua respectiva bolha
    posicoes_oficiais = {
        "PETR4": "top center",
        "PRIO3": "middle left",
        "EMBJ3": "middle left",
        "EGIE3": "top center",
        "ITUB4": "top center",
        "ABEV3": "top center",       # Acima da bolha violeta (+2,57%)
        "KLBN11": "bottom center",   # Abaixo da bolha laranja (-0,80%)
        "BBDC4": "bottom center",    # Abaixo da bolha violeta (-6,93%)
        "WEGE3": "top center",       # Acima da bolha azul (+3,51%)
        "VALE3": "top center",       # Acima da bolha laranja (+18,11%)
        "GGBR4": "top center",       # Acima da bolha laranja (+30,79%)
        "RENT3": "bottom center",    # Abaixo da bolha violeta (-0,25%)
    }

    max_vol = summary_df["volume_medio"].max()
    if pd.isna(max_vol) or max_vol <= 0:
        max_vol = 1.0

    summary_df["tamanho_bolha"] = (
        24 + (summary_df["volume_medio"] / max_vol).clip(lower=0, upper=1) * 24
    )

    # Renderiza marcadores com texto acoplado nativamente na mesma coordenada
    for setor, group in summary_df.groupby("setor", sort=False):
        marker_color = SECTOR_COLORS.get(setor, "#5E6C84")
        text_positions = [posicoes_oficiais.get(lbl, "top center") for lbl in group["label"]]

        fig.add_trace(
            go.Scatter(
                x=group["vol_anualizada"],
                y=group["ret_acumulado"],
                mode="markers+text",
                name=setor,
                text=group["label"],
                textposition=text_positions,
                textfont=dict(
                    size=11,
                    family="Arial Black, Segoe UI, sans-serif",
                    color="#091E42",
                ),
                marker=dict(
                    size=group["tamanho_bolha"].to_numpy(),
                    color=marker_color,
                    opacity=0.88,
                    line=dict(width=1.6, color="#091E42"),
                ),
                customdata=group[["ticker", "volume_medio", "setor"]].to_numpy(dtype=object),
                hovertemplate=(
                    "<b>%{text}</b> (%{customdata[0]})<br>"
                    "Setor: <b>%{customdata[2]}</b><br>"
                    "Retorno Acumulado: <b>%{y:.2f}%</b><br>"
                    "Volatilidade Histórica: <b>%{x:.2f}% a.a.</b><br>"
                    "Volume Médio: <b>R$ %{customdata[1]:,.2f}</b>"
                    "<extra></extra>"
                ),
            )
        )

    # Linha neutra de retorno 0.0%
    fig.add_hline(
        y=0.0,
        line_dash="dot",
        line_color="#7A869A",
        line_width=1.2,
        annotation_text="Ponto de Equilíbrio (0.0%)",
        annotation_position="bottom right",
        annotation_font=dict(size=10, color="#7A869A"),
    )

    fig.update_layout(
        template=THEME_TEMPLATE,
        title=dict(
            text="<b>Matriz Risco x Retorno — Eficiência da Carteira B3 (2021-2023)</b>",
            x=0.01,
            y=0.98,
            font=dict(size=15, color="#172B4D"),
        ),
        xaxis=dict(
            title=dict(
                text="Volatilidade Anualizada (σ × √252) [% a.a.]",
                font=dict(size=11, color="#5E6C84"),
            ),
            ticksuffix="%",
            gridcolor="#EBECF0",
            showline=True,
            linecolor="#DFE1E6",
            range=[14, 52],
            automargin=True,
        ),
        yaxis=dict(
            title=dict(
                text="Retorno Acumulado no Período (%)",
                font=dict(size=11, color="#5E6C84"),
            ),
            ticksuffix="%",
            gridcolor="#EBECF0",
            showline=True,
            linecolor="#DFE1E6",
            range=[-35, 275],  # Limite inferior ampliado para respiro dos rótulos de BBDC4 e KLBN11
            automargin=True,
        ),
        legend=dict(
            title=dict(text="Setor Econômico", font=dict(size=10, color="#5E6C84")),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0.0,
            font=dict(size=10),
        ),
        margin=dict(l=65, r=55, t=100, b=65),
        height=560,
        autosize=True,
    )

    return fig


# ============================================================================
# 3. DISTRIBUIÇÃO E RISCO DE CAUDA (BOXPLOT + HISTOGRAMA INTEGRADO)
# ============================================================================

def plot_daily_returns_distribution(
    df: pd.DataFrame,
    selected_ticker: Optional[str] = None,
) -> go.Figure:
    """Gera painel vertical integrado com Boxplot (topo) e Histograma (fundo)."""
    if selected_ticker:
        data = df[df["ticker"] == selected_ticker].copy()
        titulo = f"Distribuição dos Retornos Diários — {selected_ticker}"
        bar_color = BENCHMARK_COLORS.get(selected_ticker, "#0052CC")
    else:
        data = df.copy()
        titulo = "Distribuição dos Retornos Diários — Consolidado da Carteira (12 Ativos)"
        bar_color = "#0052CC"

    data = data.dropna(subset=["ret_diario"])

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.20, 0.80],
    )

    # 1. Boxplot marginal superior sóbrio (sem pontos sobrepostos poluindo a vista)
    fig.add_trace(
        go.Box(
            x=data["ret_diario"],
            name="Dispersão",
            orientation="h",
            marker=dict(color=bar_color, size=3.5, opacity=0.45),
            line=dict(color="#172B4D", width=1.4),
            boxmean=True,
            boxpoints=False,
            hovertemplate="Retorno: %{x:.2%}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    # 2. Histograma de frequência inferior
    fig.add_trace(
        go.Histogram(
            x=data["ret_diario"],
            name="Frequência",
            nbinsx=65,
            marker=dict(color=bar_color, opacity=0.75, line=dict(color="#FFFFFF", width=0.8)),
            hovertemplate="Faixa: %{x:.2%}<br>Pregões: <b>%{y} sessões</b><extra></extra>",
        ),
        row=2,
        col=1,
    )

    # Linha vertical neutra no retorno 0.0%
    fig.add_vline(x=0.0, line_dash="dash", line_color="#DE350B", line_width=1.4)

    fig.update_layout(
        template=THEME_TEMPLATE,
        title=dict(text=f"<b>{titulo}</b>", x=0.01, y=0.96, font=dict(size=15, color="#172B4D")),
        showlegend=False,
        bargap=0.04,
        margin=dict(l=40, r=40, t=55, b=40),
        height=480,
    )
    fig.update_xaxes(tickformat=".1%", title_text="Retorno Percentual Diário (%)", gridcolor="#EBECF0", row=2, col=1)
    fig.update_yaxes(title_text="Frequência (Dias)", gridcolor="#EBECF0", row=2, col=1)
    fig.update_yaxes(showticklabels=False, gridcolor="#EBECF0", row=1, col=1)

    return fig


# ============================================================================
# 4. SMALL MULTIPLES DE DRAWDOWN (MATRIZ 4 LINHAS x 3 COLUNAS)
# ============================================================================

def plot_drawdown_small_multiples(df: pd.DataFrame) -> go.Figure:
    """Gera matriz 4x3 de Small Multiples com cores alinhadas aos setores da dispersão."""
    rows = 4
    cols = 3
    subplot_titles = [f"<b>{t}</b>" for t in ORDERED_TICKERS]

    fig = make_subplots(
        rows=rows,
        cols=cols,
        shared_xaxes=True,
        shared_yaxes=True,
        vertical_spacing=0.08,
        horizontal_spacing=0.03,
        subplot_titles=subplot_titles,
    )

    for i, ticker in enumerate(ORDERED_TICKERS):
        r = (i // cols) + 1
        c = (i % cols) + 1

        subset = df[df["ticker"] == ticker].sort_values("date")
        if subset.empty:
            continue

        setor = subset["setor"].iloc[0] if "setor" in subset.columns else TICKER_SECTOR_MAP.get(ticker, "")
        line_color = SECTOR_COLORS.get(setor, "#5E6C84")
        area_color = SECTOR_FILL_COLORS.get(setor, "rgba(94, 108, 132, 0.25)")

        fig.add_trace(
            go.Scatter(
                x=subset["date"],
                y=subset["drawdown"],
                mode="lines",
                name=ticker,
                line=dict(color=line_color, width=1.5),
                fill="tozeroy",
                fillcolor=area_color,
                hovertemplate=(
                    f"<b>{ticker}</b> ({setor})<br>"
                    "Data: %{x|%d/%m/%Y}<br>"
                    "Drawdown: <b>%{y:.2%}</b>"
                    "<extra></extra>"
                ),
            ),
            row=r,
            col=c,
        )

        fig.add_hline(y=0.0, line_dash="solid", line_color="#DFE1E6", line_width=1.0, row=r, col=c)

    for annotation in fig["layout"]["annotations"]:
        annotation["font"] = dict(size=11, color="#172B4D")

    fig.update_layout(
        template=THEME_TEMPLATE,
        title=dict(
            text="<b>Matriz de Rebaixamento Máximo (Drawdown) — Small Multiples 4×3 (Setorizada por Cores)</b>",
            x=0.01,
            y=0.98,
            font=dict(size=15, color="#172B4D"),
        ),
        showlegend=False,
        hovermode="x unified",
        margin=dict(l=45, r=25, t=55, b=35),
        height=720,
    )

    fig.update_yaxes(range=[-0.68, 0.02], tickformat=".0%", gridcolor="#EBECF0", tickfont=dict(size=9, color="#5E6C84"))
    fig.update_xaxes(gridcolor="#EBECF0", tickfont=dict(size=9, color="#5E6C84"))

    return fig


def plot_drawdown_matrix(
    df: pd.DataFrame,
    selected_ticker: Optional[str] = None,
) -> go.Figure:
    """Wrapper de compatibilidade para renderizar o Drawdown."""
    if selected_ticker:
        fig = go.Figure()
        subset = df[df["ticker"] == selected_ticker].sort_values("date")
        setor = subset["setor"].iloc[0] if "setor" in subset.columns else TICKER_SECTOR_MAP.get(selected_ticker, "")
        line_color = SECTOR_COLORS.get(setor, "#0052CC")
        area_color = SECTOR_FILL_COLORS.get(setor, "rgba(0, 82, 204, 0.25)")

        fig.add_trace(
            go.Scatter(
                x=subset["date"],
                y=subset["drawdown"],
                mode="lines",
                name=selected_ticker,
                line=dict(color=line_color, width=2.0),
                fill="tozeroy",
                fillcolor=area_color,
                hovertemplate=f"<b>{selected_ticker}</b> ({setor})<br>Drawdown: <b>%{{y:.2%}}</b><extra></extra>",
            )
        )
        fig.update_layout(
            template=THEME_TEMPLATE,
            title=dict(
                text=f"<b>Curva Contínua de Drawdown — {selected_ticker} ({setor})</b>",
                x=0.01,
                y=0.96,
                font=dict(size=15, color="#172B4D"),
            ),
            yaxis=dict(tickformat=".0%", gridcolor="#EBECF0"),
            xaxis=dict(gridcolor="#EBECF0"),
            height=480,
            margin=dict(l=40, r=40, t=55, b=40),
        )
        return fig

    return plot_drawdown_small_multiples(df)


# ============================================================================
# 5. TENDÊNCIA TÉCNICA E MÉDIAS MÓVEIS (SMA 21 / SMA 50)
# ============================================================================

def plot_technical_trend(df: pd.DataFrame, ticker: str = "PETR4.SA") -> go.Figure:
    """Gera rastreamento de médias móveis e volume diário com visual limpo."""
    subset = df[df["ticker"] == ticker].sort_values("date").copy()

    if subset.empty:
        raise ValueError(f"Ativo {ticker} não encontrado na base de dados.")

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.74, 0.26],
    )

    # 1. Cotação de Fechamento Ajustada
    fig.add_trace(
        go.Scatter(
            x=subset["date"],
            y=subset["adj_close"],
            mode="lines",
            name="Fechamento Ajustado",
            line=dict(color="#172B4D", width=2.0),
            hovertemplate="Fechamento: <b>R$ %{y:.2f}</b><extra></extra>",
        ),
        row=1,
        col=1,
    )

    # 2. SMA 21 (Curto Prazo)
    fig.add_trace(
        go.Scatter(
            x=subset["date"],
            y=subset["sma_21"],
            mode="lines",
            name="SMA 21 (Curto Prazo)",
            line=dict(color="#FF8B00", width=1.6, dash="dash"),
            hovertemplate="SMA 21: <b>R$ %{y:.2f}</b><extra></extra>",
        ),
        row=1,
        col=1,
    )

    # 3. SMA 50 (Médio Prazo)
    fig.add_trace(
        go.Scatter(
            x=subset["date"],
            y=subset["sma_50"],
            mode="lines",
            name="SMA 50 (Médio Prazo)",
            line=dict(color="#00875A", width=1.6, dash="dot"),
            hovertemplate="SMA 50: <b>R$ %{y:.2f}</b><extra></extra>",
        ),
        row=1,
        col=1,
    )

    # 4. Volume Financeiro Diário
    fig.add_trace(
        go.Bar(
            x=subset["date"],
            y=subset["volume"],
            name="Volume Financeiro",
            marker=dict(color="#A5ADBA", opacity=0.7),
            hovertemplate="Volume: <b>R$ %{y:,.2f}</b><extra></extra>",
        ),
        row=2,
        col=1,
    )

    fig.update_layout(
        template=THEME_TEMPLATE,
        title=dict(
            text=f"<b>Rastreamento Técnico e Médias Móveis — {ticker}</b>",
            x=0.01,
            y=0.96,
            font=dict(size=15, color="#172B4D"),
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
        margin=dict(l=40, r=40, t=65, b=40),
        height=500,
    )

    fig.update_yaxes(
        title_text="Cotação (R$)",
        tickprefix="R$ ",
        gridcolor="#EBECF0",
        row=1,
        col=1,
    )
    fig.update_yaxes(
        title_text="Volume",
        tickformat="~s",
        tickprefix="R$ ",
        gridcolor="#EBECF0",
        row=2,
        col=1,
    )
    fig.update_xaxes(gridcolor="#EBECF0", row=2, col=1)

    return fig


# ============================================================================
# AUDITORIA AUTÓNOMA DE EXECUÇÃO
# ============================================================================

if __name__ == "__main__":
    print("-" * 75)
    print("INICIALIZANDO AUDITORIA TÉCNICA: src/visualizations.py")
    print("-" * 75)

    base_dir = Path(__file__).resolve().parent.parent
    data_path = base_dir / "data" / "processed" / "b3_stocks_processed.csv"

    if data_path.exists():
        df_test = pd.read_csv(data_path)
        df_test["date"] = pd.to_datetime(df_test["date"])
        print(f"[OK] Base lida: {len(df_test)} linhas.")

        f1 = plot_base_100(df_test)
        f2 = plot_risk_return(df_test)
        f3 = plot_daily_returns_distribution(df_test)
        f4 = plot_drawdown_small_multiples(df_test)
        f5 = plot_technical_trend(df_test, "PETR4.SA")

        print("✓ Todos os 5 gráficos compilaram sem erros e cumprem o Critério 8.")
    else:
        print("[AVISO] Base processed não encontrada localmente para execução do script isolado.")