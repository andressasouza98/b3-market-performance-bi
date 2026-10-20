"""
Módulo de Ingestão, Saneamento e Engenharia de Features Financeiras (B3).
Projeto Avaliativo Final de BI - Linha 2 (Módulo 2).
"""

from pathlib import Path
import logging
from typing import Dict, List
import numpy as np
import pandas as pd
import yfinance as yf

# Configuração de Logging Estruturado
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Diretórios Relativos Resilientes via pathlib (Item 4.3 do Edital)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"

# Dicionário Setorial dos 12 Ativos Estratégicos da B3
TICKER_SECTORS: Dict[str, str] = {
    # Bens de Capital & Indústria (EMBR3 atualizado para o novo ticker EMBJ3)
    "WEGE3.SA": "Bens de Capital & Indústria",
    "EMBJ3.SA": "Bens de Capital & Indústria",
    # Materiais Básicos & Siderurgia/Papel
    "VALE3.SA": "Materiais Básicos & Siderurgia/Papel",
    "GGBR4.SA": "Materiais Básicos & Siderurgia/Papel",
    "KLBN11.SA": "Materiais Básicos & Siderurgia/Papel",
    # Petróleo, Gás & Energia
    "PETR4.SA": "Petróleo, Gás & Energia",
    "PRIO3.SA": "Petróleo, Gás & Energia",
    "EGIE3.SA": "Petróleo, Gás & Energia",
    # Financeiro, Consumo & Locação
    "ITUB4.SA": "Financeiro, Consumo & Locação",
    "BBDC4.SA": "Financeiro, Consumo & Locação",
    "ABEV3.SA": "Financeiro, Consumo & Locação",
    "RENT3.SA": "Financeiro, Consumo & Locação",
}

START_DATE = "2021-01-01"
END_DATE = "2023-12-31"


def extrair_cotacoes_b3(
    tickers: List[str], start_date: str, end_date: str
) -> pd.DataFrame:
    """
    Descarrega cotações diárias brutas da B3 via yfinance com tratamento de multi-index.
    """
    logger.info("Iniciando extração via yfinance para %d ativos...", len(tickers))
    df_raw = yf.download(
        tickers=tickers,
        start=start_date,
        end=end_date,
        interval="1d",
        group_by="column",
        auto_adjust=False,
        threads=True,
    )

    if df_raw.empty:
        raise ValueError("A extração retornou um DataFrame vazio. Verifique a conexão.")

    # Converte de MultiIndex em colunas para formato tabular longo (Long Format)
    records = []
    # Tratamento caso retorne MultiIndex ou DataFrame simples
    if isinstance(df_raw.columns, pd.MultiIndex):
        # Nível 0 geralmente é a métrica ('Adj Close', 'Close', etc.) e Nível 1 o Ticker
        # Invertemos para iterar ticker a ticker com facilidade
        df_stacked = df_raw.stack(level=1, future_stack=True).reset_index()
        df_stacked.rename(
            columns={
                "Date": "date",
                "Ticker": "ticker",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Adj Close": "adj_close",
                "Volume": "volume",
            },
            inplace=True,
        )
        records = df_stacked
    else:
        # Fallback de segurança se apenas um ticker for consultado
        df_raw = df_raw.reset_index()
        df_raw.columns = [col.lower() for col in df_raw.columns]
        df_raw["ticker"] = tickers[0]
        records = df_raw

    logger.info("Extração bruta concluída: %d registos obtidos.", len(records))
    return records


def sanear_dados(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica padronização de tipos primitivos, descarte de duplicados e saneamento de nulos.
    """
    logger.info("Iniciando limpeza, tipagem e saneamento de dados...")
    df_clean = df.copy()

    # Normalização de nomes de colunas
    df_clean.columns = [str(col).strip().lower().replace(" ", "_") for col in df_clean.columns]

    # Validação e ordenação temporal obrigatória
    df_clean["date"] = pd.to_datetime(df_clean["date"]).dt.tz_localize(None)
    df_clean = df_clean.sort_values(by=["ticker", "date"]).reset_index(drop=True)

    # Eliminação de duplicados por par chave (ticker, date)
    registos_iniciais = len(df_clean)
    df_clean = df_clean.drop_duplicates(subset=["ticker", "date"], keep="last")
    duplicados_removidos = registos_iniciais - len(df_clean)
    if duplicados_removidos > 0:
        logger.warning("Foram removidos %d registos duplicados.", duplicados_removidos)

    # Tratamento rigoroso de nulos através de interpolação temporal por ativo (ffill / bfill)
    colunas_precos = ["open", "high", "low", "adj_close", "volume"]
    for col in colunas_precos:
        if col in df_clean.columns:
            df_clean[col] = df_clean.groupby("ticker")[col].transform(
                lambda s: s.ffill().bfill()
            )

    # Remoção residual caso algum ativo inteiro não possua cotação
    df_clean = df_clean.dropna(subset=["adj_close", "ticker", "date"]).reset_index(drop=True)

    # Conversão de tipos de dados conforme especificação
    tipo_conversoes = {
        "open": np.float64,
        "high": np.float64,
        "low": np.float64,
        "adj_close": np.float64,
        "volume": np.float64,
    }
    for col, dtype in tipo_conversoes.items():
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(dtype)

    # Atribuição da coluna categórica do Setor Económico
    df_clean["setor"] = df_clean["ticker"].map(TICKER_SECTORS).fillna("Outros")

    logger.info("Base saneada com sucesso: %d registos preservados.", len(df_clean))
    return df_clean


def calcular_metricas_analiticas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula as variáveis analíticas obrigatórias de séries temporais de forma vetorizada:
    - ret_diario: Variação percentual diária do preço de fecho ajustado.
    - base_100: Retorno normalizado iniciando em 100 no 1º pregão útil.
    - sma_21: Média Móvel Simples de 21 dias (curto prazo).
    - sma_50: Média Móvel Simples de 50 dias (médio prazo).
    - peak: Preço máximo acumulado até a data corrente.
    - drawdown: Rebaixamento percentual a partir do pico histórico.
    """
    logger.info("Calculando métricas analíticas financeiras vetorizadas...")
    dfs_processados = []

    for ticker, group in df.groupby("ticker", group_keys=False):
        grp = group.sort_values(by="date").copy()

        # 1. Retorno Diário Percentual
        grp["ret_diario"] = grp["adj_close"].pct_change().fillna(0.0).astype(np.float64)

        # 2. Desempenho Relativo Normalizado (Base 100)
        preco_inicial = grp["adj_close"].iloc[0]
        grp["base_100"] = ((grp["adj_close"] / preco_inicial) * 100.0).astype(np.float64)

        # 3. Médias Móveis Simples (SMA 21 e SMA 50)
        # min_periods=1 assegura série contínua sem quebras ou nulos artificiais iniciais
        grp["sma_21"] = grp["adj_close"].rolling(window=21, min_periods=1).mean().astype(np.float64)
        grp["sma_50"] = grp["adj_close"].rolling(window=50, min_periods=1).mean().astype(np.float64)

        # 4. Pico Histórico e Drawdown
        grp["peak"] = grp["adj_close"].cummax().astype(np.float64)
        grp["drawdown"] = ((grp["adj_close"] - grp["peak"]) / grp["peak"]).astype(np.float64)

        dfs_processados.append(grp)

    df_final = pd.concat(dfs_processados, ignore_index=True)
    df_final = df_final.sort_values(by=["ticker", "date"]).reset_index(drop=True)

    # Reorganização padronizada das variáveis oficiais
    colunas_ordenadas = [
        "date",
        "ticker",
        "setor",
        "open",
        "high",
        "low",
        "adj_close",
        "volume",
        "ret_diario",
        "base_100",
        "sma_21",
        "sma_50",
        "peak",
        "drawdown",
    ]
    df_final = df_final[[col for col in colunas_ordenadas if col in df_final.columns]]

    logger.info("Cálculos concluídos com sucesso.")
    return df_final


def executar_pipeline() -> Path:
    """
    Função orquestradora completa do pipeline de ETL.
    """
    logger.info("=== INÍCIO DO PIPELINE DE ENGENHARIA DE DADOS B3 ===")

    # Garantir existência física dos diretórios relativos
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Extração
    tickers = list(TICKER_SECTORS.keys())
    df_bruto = extrair_cotacoes_b3(tickers, START_DATE, END_DATE)

    # Salva cópia de auditoria em raw
    raw_path = DATA_RAW_DIR / "b3_stocks_raw.csv"
    df_bruto.to_csv(raw_path, index=False)
    logger.info("Snapshot bruto salvo em: %s", raw_path.relative_to(BASE_DIR))

    # 2. Saneamento e Limpeza
    df_saneado = sanear_dados(df_bruto)

    # 3. Engenharia de Variáveis Analíticas
    df_final = calcular_metricas_analiticas(df_saneado)

    # 4. Persistência da Base Processada Oficial
    processed_path = DATA_PROCESSED_DIR / "b3_stocks_processed.csv"
    df_final.to_csv(processed_path, index=False, float_format="%.6f")
    logger.info("Base processada salva com sucesso em: %s", processed_path.relative_to(BASE_DIR))

    # Relatório de Diagnóstico de Qualidade
    logger.info("Diagnóstico de Nulos na Base Final:\n%s", df_final.isna().sum().to_string())
    logger.info("Resumo por Ativo:\n%s", df_final.groupby("ticker")["date"].count().to_string())
    logger.info("=== PIPELINE EXECUTADO COM ÊXITO ===")

    return processed_path


if __name__ == "__main__":
    executar_pipeline()