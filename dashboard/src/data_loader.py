"""
Módulo de Carregamento de Dados (Data Loader) — Produção BigQuery com Snapshot Persistente em Parquet
Responsável pela conexão com o Google BigQuery, aplicação de cache em memória (ttl=3600)
e persistência/fallback automático em arquivos Parquet locais (dashboard/data_cache/*.parquet).
Se o projeto do GCP for desligado ou estiver inacessível, o dashboard continua 100% operacional
lendo o último snapshot real salvo em Parquet.
"""

import os
from pathlib import Path
import pandas as pd
import streamlit as st

PROJECT_ID = "veloja-ecommerce-medalhao"
LOCATION = "southamerica-east1"
CACHE_DIR = Path(__file__).resolve().parent.parent / "data_cache"


def get_bigquery_client():
    """
    Retorna o cliente autenticado do Google BigQuery ou None caso o GCP esteja offline/desconectado.
    """
    try:
        from google.cloud import bigquery
        from google.oauth2 import service_account

        secrets_paths = [
            os.path.expanduser("~/.streamlit/secrets.toml"),
            os.path.join(os.getcwd(), ".streamlit/secrets.toml"),
            os.path.join(os.getcwd(), "dashboard/.streamlit/secrets.toml"),
        ]
        if any(os.path.exists(p) for p in secrets_paths):
            try:
                if "gcp_service_account" in st.secrets:
                    creds_info = dict(st.secrets["gcp_service_account"])
                    credentials = service_account.Credentials.from_service_account_info(creds_info)
                    return bigquery.Client(project=PROJECT_ID, credentials=credentials, location=LOCATION)
            except Exception:
                pass

        return bigquery.Client(project=PROJECT_ID, location=LOCATION)
    except Exception:
        return None


def _query_or_parquet(query: str, parquet_name: str, date_col_str: str = None, date_col_dt: str = None) -> pd.DataFrame:
    """
    Tenta executar a consulta no BigQuery e atualizar o snapshot Parquet local.
    Caso o BigQuery esteja desligado ou sem credencial ativa, lê diretamente o Parquet local.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    parquet_path = CACHE_DIR / parquet_name

    client = get_bigquery_client()
    if client is not None:
        try:
            df = client.query(query).to_dataframe()
            if date_col_str and date_col_dt:
                df[date_col_dt] = pd.to_datetime(df[date_col_str])
            df.to_parquet(parquet_path, index=False, compression="snappy")
            return df
        except Exception:
            pass

    if parquet_path.exists():
        df = pd.read_parquet(parquet_path)
        if date_col_str and date_col_dt and date_col_dt not in df.columns:
            df[date_col_dt] = pd.to_datetime(df[date_col_str])
        return df

    st.error(f"Não foi possível conectar ao BigQuery e o arquivo {parquet_name} não foi encontrado em {CACHE_DIR}.")
    st.stop()


# ==============================================================================
# CARREGAMENTO DE DADOS COM CACHE (TTL: 1 HORA) + FALLBACK PARQUET
# ==============================================================================

@st.cache_data(ttl=3600, show_spinner="Carregando vendas diárias...")
def load_vendas_diarias() -> pd.DataFrame:
    """Carrega dados diários consolidados de faturamento (mart_vendas_diarias)."""
    query = f"""
    SELECT
        CAST(data_pedido AS STRING) AS data_pedido,
        pedidos,
        clientes_unicos,
        CAST(receita_liquida AS FLOAT64) AS receita_liquida,
        CAST(ticket_medio AS FLOAT64) AS ticket_medio,
        itens_vendidos
    FROM `{PROJECT_ID}.refined.mart_vendas_diarias`
    ORDER BY data_pedido ASC
    """
    return _query_or_parquet(query, "mart_vendas_diarias.parquet", "data_pedido", "data_pedido_dt")


@st.cache_data(ttl=3600, show_spinner="Carregando pedidos da Camada Refined...")
def load_pedidos_fato() -> pd.DataFrame:
    """Carrega cabeçalho de pedidos da Camada Refined (fact_pedidos)."""
    query = f"""
    SELECT
        order_id,
        customer_id,
        CAST(data_pedido_date AS STRING) AS data_pedido_date,
        status_pedido,
        origem_pedido,
        CAST(valor_itens_bruto AS FLOAT64) AS valor_itens_bruto,
        CAST(valor_desconto AS FLOAT64) AS valor_desconto,
        CAST(valor_receita_liquida AS FLOAT64) AS valor_receita_liquida,
        CAST(valor_pago_aprovado AS FLOAT64) AS valor_pago_aprovado,
        flag_pedido_valido,
        FORMAT_TIMESTAMP('%d/%m/%Y %H:%M:%S', MAX(data_processamento) OVER (), 'America/Sao_Paulo') AS ultima_atualizacao_gold
    FROM `{PROJECT_ID}.refined.fact_pedidos`
    """
    return _query_or_parquet(query, "fact_pedidos.parquet", "data_pedido_date", "data_pedido_dt")


@st.cache_data(ttl=3600, show_spinner="Carregando produtos e rentabilidade...")
def load_produtos_itens() -> pd.DataFrame:
    """Carrega dados agregados por data, canal de origem, produto e categoria."""
    query = f"""
    SELECT
        CAST(DATE(i.data_pedido) AS STRING) AS data_pedido_date,
        COALESCE(fp.origem_pedido, 'nao_informado') AS origem_pedido,
        i.product_id,
        p.nome_produto,
        p.categoria,
        CAST(p.preco_tabela AS FLOAT64) AS preco_tabela,
        CAST(p.custo_unitario AS FLOAT64) AS custo_unitario,
        CAST(p.margem_unitaria AS FLOAT64) AS margem_unitaria,
        SUM(i.quantidade) AS quantidade,
        CAST(SUM(i.receita_item) AS FLOAT64) AS receita_item,
        CAST(SUM(i.custo_item) AS FLOAT64) AS custo_item,
        CAST(SUM(i.margem_item) AS FLOAT64) AS margem_item,
        i.flag_item_valido
    FROM `{PROJECT_ID}.refined.fact_itens_pedido` i
    INNER JOIN `{PROJECT_ID}.refined.dim_produtos` p
        ON i.product_id = p.product_id
    LEFT JOIN `{PROJECT_ID}.refined.fact_pedidos` fp
        ON i.order_id = fp.order_id
    GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 13
    """
    return _query_or_parquet(query, "produtos_itens.parquet", "data_pedido_date", "data_pedido_dt")


@st.cache_data(ttl=3600, show_spinner="Carregando performance de marketing...")
def load_performance_campanhas() -> pd.DataFrame:
    """Carrega métricas de campanhas de marketing (mart_performance_campanhas)."""
    query = f"""
    SELECT
        campanha,
        canal,
        CAST(periodo_inicio AS STRING) AS periodo_inicio,
        CAST(periodo_fim AS STRING) AS periodo_fim,
        CAST(custo_total AS FLOAT64) AS custo_total,
        eventos,
        clientes_impactados,
        pedidos_atribuidos,
        CAST(receita_atribuida AS FLOAT64) AS receita_atribuida
    FROM `{PROJECT_ID}.refined.mart_performance_campanhas`
    ORDER BY receita_atribuida DESC, custo_total DESC
    """
    return _query_or_parquet(query, "mart_performance_campanhas.parquet")


@st.cache_data(ttl=3600, show_spinner="Carregando metas e atingimento (Orçamento Top-Down)...")
def load_metas_vs_realizado() -> pd.DataFrame:
    """Carrega dados diários e mensais de metas vs realizado (mart_metas_vs_realizado)."""
    query = f"""
    SELECT
        CAST(data_referencia AS STRING) AS data_referencia,
        ano_mes,
        num_dia_semana,
        nome_dia_semana,
        CAST(receita_realizada AS FLOAT64) AS receita_realizada,
        pedidos_realizados,
        CAST(ticket_realizado AS FLOAT64) AS ticket_realizado,
        itens_vendidos,
        CAST(margem_bruta_realizada AS FLOAT64) AS margem_bruta_realizada,
        CAST(margem_pct_realizada AS FLOAT64) AS margem_pct_realizada,
        CAST(desconto_pct_realizado AS FLOAT64) AS desconto_pct_realizado,
        CAST(meta_diaria_receita AS FLOAT64) AS meta_diaria_receita,
        CAST(meta_mensal_receita AS FLOAT64) AS meta_mensal_receita,
        meta_diaria_pedidos,
        meta_mensal_pedidos,
        CAST(meta_ticket_medio AS FLOAT64) AS meta_ticket_medio,
        CAST(meta_margem_pct AS FLOAT64) AS meta_margem_pct,
        CAST(teto_desconto_pct AS FLOAT64) AS teto_desconto_pct,
        CAST(meta_roas AS FLOAT64) AS meta_roas,
        CAST(faixa_esperada_min AS FLOAT64) AS faixa_esperada_min,
        CAST(faixa_esperada_max AS FLOAT64) AS faixa_esperada_max,
        CAST(atingimento_receita_pct AS FLOAT64) AS atingimento_receita_pct,
        CAST(atingimento_pedidos_pct AS FLOAT64) AS atingimento_pedidos_pct,
        CAST(atingimento_ticket_pct AS FLOAT64) AS atingimento_ticket_pct,
        CAST(receita_acumulada_mes AS FLOAT64) AS receita_acumulada_mes,
        CAST(meta_acumulada_mes AS FLOAT64) AS meta_acumulada_mes,
        CAST(pace_atingimento_mes_pct AS FLOAT64) AS pace_atingimento_mes_pct,
        status_receita,
        status_pedidos,
        status_ticket,
        status_margem,
        status_desconto,
        origem_meta
    FROM `{PROJECT_ID}.refined.mart_metas_vs_realizado`
    ORDER BY data_referencia ASC
    """
    return _query_or_parquet(query, "mart_metas_vs_realizado.parquet", "data_referencia", "data_referencia_dt")


@st.cache_data(ttl=3600, show_spinner="Carregando transações de pagamento...")
def load_pagamentos_resumo() -> pd.DataFrame:
    """Carrega resumo de transações por método de pagamento, data e canal de origem."""
    query = f"""
    SELECT
        CAST(p.data_pedido_date AS STRING) AS data_pedido_date,
        COALESCE(p.origem_pedido, 'nao_informado') AS origem_pedido,
        pg.metodo_pagamento,
        pg.status_pagamento,
        CAST(ROUND(SUM(pg.valor_pago), 2) AS FLOAT64) AS total_valor,
        COUNT(*) AS total_transacoes
    FROM `{PROJECT_ID}.trusted.pagamentos` pg
    LEFT JOIN `{PROJECT_ID}.refined.fact_pedidos` p
        ON pg.order_id = p.order_id
    GROUP BY 1, 2, 3, 4
    """
    return _query_or_parquet(query, "pagamentos_resumo.parquet", "data_pedido_date", "data_pedido_dt")
