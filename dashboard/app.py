"""
Aplicação Principal do Dashboard Executivo Veloja E-Commerce (Produção BigQuery)
Framework: Streamlit + Apache ECharts (streamlit-echarts)
"""

import streamlit as st
import pandas as pd
from streamlit_echarts import st_echarts

from src.data_loader import (
    load_pedidos_fato,
    load_produtos_itens,
    load_performance_campanhas,
    load_pagamentos_resumo,
    load_metas_vs_realizado,
)
from src.charts import (
    chart_evolucao_vendas_com_meta,
    chart_mensal_realizado_vs_meta,
    chart_margem_desconto_metas,
    chart_roas_campanhas_com_meta,
    chart_share_origem,
    chart_metodos_pagamento,
    chart_top_categorias,
    chart_campanhas_roi,
)

# ==============================================================================
# CONFIGURAÇÃO DE PÁGINA (WIDE LAYOUT, SEM EMOJIS DECORATIVOS)
# ==============================================================================
st.set_page_config(
    page_title="Veloja Analytics | Dashboard & Metas",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS para cartões com Semáforo de 4 Níveis
st.markdown("""
<style>
    .kpi-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 15px 18px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
        margin-bottom: 10px;
    }
    .kpi-card.verde-escuro { border-left: 5px solid #059669; }
    .kpi-card.verde-claro  { border-left: 5px solid #6EE7B7; }
    .kpi-card.amarelo      { border-left: 5px solid #F59E0B; }
    .kpi-card.vermelho     { border-left: 5px solid #EF4444; }

    .kpi-label {
        color: #94A3B8;
        font-size: 0.84rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 1.55rem;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .kpi-value.verde-escuro { color: #059669; }
    .kpi-value.verde-claro  { color: #6EE7B7; }
    .kpi-value.amarelo      { color: #F59E0B; }
    .kpi-value.vermelho     { color: #EF4444; }

    .kpi-meta {
        font-size: 0.80rem;
        color: #CBD5E1;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .badge-rag {
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.74rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 5px;
    }
    .badge-rag.verde-escuro { background: rgba(5, 150, 105, 0.22); color: #10B981; border: 1px solid #059669; }
    .badge-rag.verde-claro  { background: rgba(110, 231, 183, 0.16); color: #6EE7B7; border: 1px solid #6EE7B7; }
    .badge-rag.amarelo      { background: rgba(245, 158, 11, 0.18); color: #FBBF24; border: 1px solid #F59E0B; }
    .badge-rag.vermelho     { background: rgba(239, 68, 68, 0.18); color: #F87171; border: 1px solid #EF4444; }

    .rag-dot {
        width: 9px;
        height: 9px;
        border-radius: 50%;
        display: inline-block;
    }
    .rag-dot.verde-escuro { background-color: #059669; }
    .rag-dot.verde-claro  { background-color: #6EE7B7; }
    .rag-dot.amarelo      { background-color: #F59E0B; }
    .rag-dot.vermelho     { background-color: #EF4444; }

    .section-header {
        font-size: 1.12rem;
        font-weight: 600;
        color: #F8FAFC;
        margin-top: 0.9rem;
        margin-bottom: 0.5rem;
    }
    /* Navegação horizontal com aparência de abas corporativas */
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        display: flex;
        flex-direction: row;
        gap: 8px;
        border-bottom: 1px solid #334155;
        padding-bottom: 8px;
        margin-bottom: 12px;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 6px;
        padding: 8px 16px;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)


def fmt_brl(val: float) -> str:
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def render_kpi_semaforo(label: str, valor_fmt: str, meta_fmt: str, pct_ating: float, invertido: bool = False):
    """
    Renderiza cartão de KPI com cor do número, borda e indicador de Semáforo de 4 níveis:
    - >= 100%: Verde Escuro (#059669)
    - 95% a 99,9%: Verde Claro (#6EE7B7)
    - 80% a 94,9%: Amarelo (#F59E0B)
    - < 80%: Vermelho (#EF4444)
    """
    if not invertido:
        if pct_ating >= 100.0:
            classe, texto_status = "verde-escuro", f"{pct_ating:.1f}% da meta"
        elif pct_ating >= 95.0:
            classe, texto_status = "verde-claro", f"{pct_ating:.1f}% da meta"
        elif pct_ating >= 80.0:
            classe, texto_status = "amarelo", f"{pct_ating:.1f}% da meta"
        else:
            classe, texto_status = "vermelho", f"{pct_ating:.1f}% da meta"
    else:
        if pct_ating <= 95.0:
            classe, texto_status = "verde-escuro", f"{pct_ating:.1f}% do teto"
        elif pct_ating <= 100.0:
            classe, texto_status = "verde-claro", f"{pct_ating:.1f}% do teto"
        elif pct_ating <= 120.0:
            classe, texto_status = "amarelo", f"{pct_ating:.1f}% do teto"
        else:
            classe, texto_status = "vermelho", f"{pct_ating:.1f}% do teto"

    st.markdown(f"""
    <div class="kpi-card {classe}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value {classe}">{valor_fmt}</div>
        <div class="kpi-meta">
            <span>Meta: <b>{meta_fmt}</b></span>
            <span class="badge-rag {classe}"><span class="rag-dot {classe}"></span>{texto_status}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# CARREGAMENTO DOS DADOS DO BIGQUERY (EM CACHE)
# ==============================================================================
df_metas_raw = load_metas_vs_realizado()
df_pedidos_raw = load_pedidos_fato()
df_produtos_itens_raw = load_produtos_itens()
df_campanhas = load_performance_campanhas()
df_pagamentos_raw = load_pagamentos_resumo()


# ==============================================================================
# BARRA LATERAL (FILTROS GLOBAIS EM MEMÓRIA)
# ==============================================================================
with st.sidebar:
    st.title("Veloja Analytics")
    st.caption("Painel Executivo de Vendas e Metas")
    st.markdown("---")

    st.subheader("Filtros Globais")

    if not df_metas_raw.empty and "data_referencia_dt" in df_metas_raw.columns:
        min_date = df_metas_raw["data_referencia_dt"].min().date()
        max_date = df_metas_raw["data_referencia_dt"].max().date()
        data_range = st.date_input(
            "Período de Análise (2025)",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
    else:
        data_range = None

    meses_disp = ["Todos"] + sorted(df_metas_raw["ano_mes"].dropna().unique().tolist()) if not df_metas_raw.empty else ["Todos"]
    filtro_mes = st.selectbox("Mês de Referência", options=meses_disp)

    origens_disp = ["Todos"]
    if not df_pedidos_raw.empty and "origem_pedido" in df_pedidos_raw.columns:
        origens_disp += sorted(df_pedidos_raw["origem_pedido"].dropna().unique().tolist())
    filtro_origem = st.selectbox("Canal de Origem", options=origens_disp)

    st.markdown("---")
    st.markdown("""
    **Legenda do Semáforo (RAG):**
    <div style="font-size:0.84rem; line-height:1.85; margin-top:4px;">
        <div><span class="rag-dot verde-escuro"></span> <b>Verde Escuro:</b> &ge; 100% da meta</div>
        <div><span class="rag-dot verde-claro"></span> <b>Verde Claro:</b> 95% a 99,9% da meta</div>
        <div><span class="rag-dot amarelo"></span> <b>Amarelo:</b> 80% a 94,9% da meta</div>
        <div><span class="rag-dot vermelho"></span> <b>Vermelho:</b> &lt; 80% da meta</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    if st.button("Limpar Cache do BigQuery", use_container_width=True):
        st.cache_data.clear()
        st.success("Cache renovado.")
        st.rerun()


# ==============================================================================
# APLICAÇÃO DOS FILTROS GLOBAIS (INCLUINDO CANAL DE ORIGEM COM META PROPORCIONAL)
# ==============================================================================
df_metas = df_metas_raw.copy()
df_pedidos = df_pedidos_raw.copy()
df_produtos_itens = df_produtos_itens_raw.copy()
df_pagamentos = df_pagamentos_raw.copy()

# Calcula o share histórico do canal selecionado para proporcionalizar a meta de volume
df_todos_validos = df_pedidos_raw[df_pedidos_raw["flag_pedido_valido"] == True]
receita_empresa_total = float(df_todos_validos["valor_receita_liquida"].sum()) if not df_todos_validos.empty else 1.0
pedidos_empresa_total = max(1, len(df_todos_validos))

if filtro_origem != "Todos":
    df_canal_val = df_todos_validos[df_todos_validos["origem_pedido"] == filtro_origem]
    share_receita_canal = float(df_canal_val["valor_receita_liquida"].sum()) / receita_empresa_total if receita_empresa_total > 0 else 1.0
    share_pedidos_canal = len(df_canal_val) / pedidos_empresa_total

    # Filtra os DataFrames pelo canal selecionado
    df_pedidos = df_pedidos[df_pedidos["origem_pedido"] == filtro_origem]
    df_produtos_itens = df_produtos_itens[df_produtos_itens["origem_pedido"] == filtro_origem]
    df_pagamentos = df_pagamentos[df_pagamentos["origem_pedido"] == filtro_origem]

    # Recalcula realizado diário do canal selecionado e ajusta a meta diária proporcionalmente ao share do canal
    df_ped_val_canal = df_pedidos[df_pedidos["flag_pedido_valido"] == True]
    real_canal_dia = df_ped_val_canal.groupby("data_pedido_date").agg(
        rec_canal=("valor_receita_liquida", "sum"),
        ped_canal=("order_id", "count"),
        bruto_canal=("valor_itens_bruto", "sum"),
        desc_canal=("valor_desconto", "sum"),
    ).reset_index()

    it_val_canal = df_produtos_itens[df_produtos_itens["flag_item_valido"] == True]
    marg_canal_dia = it_val_canal.groupby("data_pedido_date").agg(
        rec_it_canal=("receita_item", "sum"),
        marg_it_canal=("margem_item", "sum"),
    ).reset_index()

    df_metas = df_metas.merge(real_canal_dia, left_on="data_referencia", right_on="data_pedido_date", how="left")
    df_metas = df_metas.merge(marg_canal_dia, left_on="data_referencia", right_on="data_pedido_date", how="left")

    df_metas["receita_realizada"] = df_metas["rec_canal"].fillna(0.0)
    df_metas["pedidos_realizados"] = df_metas["ped_canal"].fillna(0).astype(int)
    df_metas["ticket_realizado"] = (df_metas["receita_realizada"] / df_metas["pedidos_realizados"].clip(lower=1)).round(2)
    df_metas["desconto_pct_realizado"] = (df_metas["desc_canal"].fillna(0.0) / df_metas["bruto_canal"].clip(lower=1.0) * 100.0).round(2)
    df_metas["margem_bruta_realizada"] = df_metas["marg_it_canal"].fillna(0.0)
    df_metas["margem_pct_realizada"] = (df_metas["marg_it_canal"].fillna(0.0) / df_metas["rec_it_canal"].clip(lower=1.0) * 100.0).round(2)

    df_metas["meta_diaria_receita"] = (df_metas["meta_diaria_receita"] * share_receita_canal).round(2)
    df_metas["meta_diaria_pedidos"] = (df_metas["meta_diaria_pedidos"] * share_pedidos_canal).round(0).clip(lower=1).astype(int)
    df_metas["faixa_esperada_min"] = (df_metas["faixa_esperada_min"] * share_receita_canal).round(2)
    df_metas["faixa_esperada_max"] = (df_metas["faixa_esperada_max"] * share_receita_canal).round(2)
    df_metas["atingimento_receita_pct"] = (df_metas["receita_realizada"] / df_metas["meta_diaria_receita"].clip(lower=1.0) * 100.0).round(2)

    def _calc_status_4(pct_series):
        return pd.Series(
            ["VERDE_ESCURO" if p >= 100.0 else ("VERDE_CLARO" if p >= 95.0 else ("AMARELO" if p >= 80.0 else "VERMELHO")) for p in pct_series],
            index=pct_series.index
        )

    df_metas["status_receita"] = _calc_status_4(df_metas["atingimento_receita_pct"])

# Filtro de Período (Datas)
if data_range and len(data_range) == 2:
    d_ini, d_fim = pd.to_datetime(data_range[0]), pd.to_datetime(data_range[1])
    df_metas = df_metas[(df_metas["data_referencia_dt"] >= d_ini) & (df_metas["data_referencia_dt"] <= d_fim)]
    df_pedidos = df_pedidos[(df_pedidos["data_pedido_dt"] >= d_ini) & (df_pedidos["data_pedido_dt"] <= d_fim)]
    df_produtos_itens = df_produtos_itens[(df_produtos_itens["data_pedido_dt"] >= d_ini) & (df_produtos_itens["data_pedido_dt"] <= d_fim)]
    df_pagamentos = df_pagamentos[(df_pagamentos["data_pedido_dt"] >= d_ini) & (df_pagamentos["data_pedido_dt"] <= d_fim)]

# Filtro de Mês
if filtro_mes != "Todos":
    df_metas = df_metas[df_metas["ano_mes"] == filtro_mes]
    df_pedidos = df_pedidos[df_pedidos["data_pedido_dt"].dt.strftime("%Y-%m") == filtro_mes]
    df_produtos_itens = df_produtos_itens[df_produtos_itens["data_pedido_dt"].dt.strftime("%Y-%m") == filtro_mes]
    df_pagamentos = df_pagamentos[df_pagamentos["data_pedido_dt"].dt.strftime("%Y-%m") == filtro_mes]

df_validos = df_pedidos[df_pedidos["flag_pedido_valido"] == True] if "flag_pedido_valido" in df_pedidos.columns else df_pedidos


# ==============================================================================
# CABEÇALHO PRINCIPAL
# ==============================================================================
col_title, col_badge = st.columns([0.78, 0.22])

with col_title:
    st.markdown("### Painel Executivo Veloja — Realizado vs. Metas (Orçamento Top-Down)")
    origem_texto = df_metas["origem_meta"].iloc[0] if not df_metas.empty and "origem_meta" in df_metas.columns else "Orcamento Anual 2025 Top-Down (FP&A)"
    sufixo_canal = f" | Canal: {filtro_origem.upper()}" if filtro_origem != "Todos" else " | Visão Consolidada Empresa"
    st.caption(f"Governança de Metas: **{origem_texto}**{sufixo_canal}")

with col_badge:
    ultima_att = (
        df_pedidos_raw["ultima_atualizacao_gold"].iloc[0]
        if not df_pedidos_raw.empty and "ultima_atualizacao_gold" in df_pedidos_raw.columns
        else "N/D"
    )
    st.markdown(
        f"""
        <div style="background-color:#1E293B; border:1px solid #334155; border-radius:8px; padding:10px 14px; text-align:right;">
            <div style="color:#94A3B8; font-size:0.76rem; font-weight:600; text-transform:uppercase; letter-spacing:0.03em;">Última atualização</div>
            <div style="color:#F8FAFC; font-size:0.95rem; font-weight:700; margin-top:2px;">{ultima_att}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==============================================================================
# NAVEGAÇÃO EM 4 VISÕES ANALÍTICAS (RENDERIZAÇÃO ATIVA PARA SUPORTE TOTAL AO ECHARTS)
# ==============================================================================
aba_ativa = st.radio(
    "Navegação",
    options=[
        "1. Visão Executiva & Metas de Receita",
        "2. Produtos, Margem & Teto de Desconto",
        "3. Campanhas & Meta de ROAS",
        "4. Catálogo de Dados & Guia dos Gráficos",
    ],
    horizontal=True,
    label_visibility="collapsed",
)

rec_real = float(df_metas["receita_realizada"].sum()) if not df_metas.empty else 0.0
rec_meta = float(df_metas["meta_diaria_receita"].sum()) if not df_metas.empty else 1.0
rec_pct = (rec_real / rec_meta * 100.0) if rec_meta > 0 else 0.0

ped_real = int(df_metas["pedidos_realizados"].sum()) if not df_metas.empty else 0
ped_meta = int(df_metas["meta_diaria_pedidos"].sum()) if not df_metas.empty else 1
ped_pct = (ped_real / ped_meta * 100.0) if ped_meta > 0 else 0.0

tkt_real = (rec_real / ped_real) if ped_real > 0 else 0.0
tkt_meta = float(df_metas["meta_ticket_medio"].mean()) if not df_metas.empty else 1870.0
tkt_pct = (tkt_real / tkt_meta * 100.0) if tkt_meta > 0 else 0.0

total_dias = max(1, len(df_metas))
dias_verdes = int((df_metas["status_receita"].isin(["VERDE_ESCURO", "VERDE_CLARO"])).sum()) if not df_metas.empty else 0
pct_dias_meta = (dias_verdes / total_dias) * 100.0


# ==============================================================================
# VISÃO 1: VISÃO EXECUTIVA DE VENDAS & METAS
# ==============================================================================
if aba_ativa == "1. Visão Executiva & Metas de Receita":
    st.markdown("<div class='section-header'>Desempenho Acumulado no Período vs. Orçamento Top-Down</div>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_semaforo("Receita Líquida", fmt_brl(rec_real), fmt_brl(rec_meta), rec_pct)
    with c2:
        render_kpi_semaforo("Pedidos Válidos", f"{ped_real:,}".replace(",", "."), f"{ped_meta:,}".replace(",", "."), ped_pct)
    with c3:
        render_kpi_semaforo("Ticket Médio (AOV)", fmt_brl(tkt_real), fmt_brl(tkt_meta), tkt_pct)
    with c4:
        render_kpi_semaforo("Dias Acima de 95% da Meta", f"{dias_verdes}/{total_dias} dias", f"{total_dias} dias", pct_dias_meta)

    st.markdown("<div class='section-header'>Faturamento Mensal: Realizado (Cor = Semáforo) vs. Marcador de Meta Mensal</div>", unsafe_allow_html=True)
    opts_mes = chart_mensal_realizado_vs_meta(df_metas)
    if opts_mes:
        st_echarts(options=opts_mes, height="350px", width="100%", key="echarts_aba1_mensal")

    st.markdown("<div class='section-header'>Evolução Diária: Realizado vs. Linha de Meta Diária Sazonal e Faixa Esperada (-1 DP)</div>", unsafe_allow_html=True)
    opts_dia = chart_evolucao_vendas_com_meta(df_metas)
    if opts_dia:
        st_echarts(options=opts_dia, height="380px", width="100%", key="echarts_aba1_diario")

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("<div class='section-header'>Share por Canal de Origem</div>", unsafe_allow_html=True)
        opts_origem = chart_share_origem(df_validos)
        if opts_origem:
            st_echarts(options=opts_origem, height="330px", width="100%", key="echarts_aba1_origem")
    with col_g2:
        st.markdown("<div class='section-header'>Formas de Pagamento Aprovadas</div>", unsafe_allow_html=True)
        opts_pag = chart_metodos_pagamento(df_pagamentos)
        if opts_pag:
            st_echarts(options=opts_pag, height="330px", width="100%", key="echarts_aba1_pagamentos")


# ==============================================================================
# VISÃO 2: PRODUTOS, MARGEM & TETO DE DESCONTO
# ==============================================================================
elif aba_ativa == "2. Produtos, Margem & Teto de Desconto":
    st.markdown("<div class='section-header'>Eficiência Comercial: Meta de Margem e Teto de Desconto (Lógica Invertida)</div>", unsafe_allow_html=True)

    margem_bruta_total = float(df_metas["margem_bruta_realizada"].sum()) if not df_metas.empty else 0.0
    margem_pct_media = float(df_metas["margem_pct_realizada"].mean()) if not df_metas.empty else 0.0
    meta_margem_alvo = float(df_metas["meta_margem_pct"].mean()) if not df_metas.empty else 36.5
    ating_margem_pct = (margem_pct_media / meta_margem_alvo * 100.0) if meta_margem_alvo > 0 else 0.0

    desc_pct_medio = float(df_metas["desconto_pct_realizado"].mean()) if not df_metas.empty else 0.0
    teto_desc_alvo = float(df_metas["teto_desconto_pct"].mean()) if not df_metas.empty else 4.65
    ating_desc_pct = (desc_pct_medio / teto_desc_alvo * 100.0) if teto_desc_alvo > 0 else 0.0

    meta_margem_reais = rec_meta * (meta_margem_alvo / 100.0)
    ating_margem_reais = (margem_bruta_total / meta_margem_reais * 100.0) if meta_margem_reais > 0 else 0.0

    cp1, cp2, cp3 = st.columns(3)
    with cp1:
        render_kpi_semaforo("Margem de Contribuição (R$)", fmt_brl(margem_bruta_total), fmt_brl(meta_margem_reais), ating_margem_reais)
    with cp2:
        render_kpi_semaforo("Margem Percentual Média", f"{margem_pct_media:.2f}%", f"{meta_margem_alvo:.2f}%", ating_margem_pct)
    with cp3:
        render_kpi_semaforo("Taxa de Desconto Média (Teto)", f"{desc_pct_medio:.2f}%", f"Máx {teto_desc_alvo:.2f}%", ating_desc_pct, invertido=True)

    st.markdown("<div class='section-header'>Evolução Mensal de Margem (%) e Desconto (%) com Linhas Marcadoras de Meta/Teto</div>", unsafe_allow_html=True)
    opts_md = chart_margem_desconto_metas(df_metas)
    if opts_md:
        st_echarts(options=opts_md, height="360px", width="100%", key="echarts_aba2_margem_desconto")

    df_itens_validos = df_produtos_itens[df_produtos_itens["flag_item_valido"] == True] if "flag_item_valido" in df_produtos_itens.columns else df_produtos_itens
    st.markdown("<div class='section-header'>Top Categorias por Receita Líquida</div>", unsafe_allow_html=True)
    opts_cat = chart_top_categorias(df_itens_validos)
    if opts_cat:
        st_echarts(options=opts_cat, height="340px", width="100%", key="echarts_aba2_categorias")


# ==============================================================================
# VISÃO 3: CAMPANHAS & META DE ROAS
# ==============================================================================
elif aba_ativa == "3. Campanhas & Meta de ROAS":
    st.markdown("<div class='section-header'>Performance de Mídia e Retorno sobre Investimento (ROAS vs. Meta)</div>", unsafe_allow_html=True)

    custo_mkt = float(df_campanhas["custo_total"].sum()) if not df_campanhas.empty else 0.0
    rec_mkt = float(df_campanhas["receita_atribuida"].sum()) if not df_campanhas.empty else 0.0
    roas_real = (rec_mkt / custo_mkt) if custo_mkt > 0 else 0.0
    meta_roas_alvo = float(df_metas["meta_roas"].mean()) if not df_metas.empty else 208.0
    ating_roas = (roas_real / meta_roas_alvo * 100.0) if meta_roas_alvo > 0 else 0.0

    pedidos_mkt = int(df_campanhas["pedidos_atribuidos"].sum()) if not df_campanhas.empty else 0

    cm1, cm2, cm3 = st.columns(3)
    with cm1:
        render_kpi_semaforo("ROAS Consolidado (Retorno/Custo)", f"{roas_real:.1f}x", f"{meta_roas_alvo:.1f}x", ating_roas)
    with cm2:
        render_kpi_semaforo("Receita Atribuída (Janela 14d)", fmt_brl(rec_mkt), fmt_brl(custo_mkt * meta_roas_alvo), ating_roas)
    with cm3:
        render_kpi_semaforo("Pedidos Convertidos por Mídia", f"{pedidos_mkt:,}".replace(",", "."), "24.000", (pedidos_mkt / 24000) * 100.0)

    col_m_left, col_m_right = st.columns(2)
    with col_m_left:
        st.markdown("<div class='section-header'>ROAS por Campanha com Linha Marcadora de Meta</div>", unsafe_allow_html=True)
        opts_roas = chart_roas_campanhas_com_meta(df_campanhas, meta_roas=meta_roas_alvo)
        if opts_roas:
            st_echarts(options=opts_roas, height="360px", width="100%", key="echarts_aba3_roas")
    with col_m_right:
        st.markdown("<div class='section-header'>Custo Investido vs. Receita Convertida</div>", unsafe_allow_html=True)
        opts_roi = chart_campanhas_roi(df_campanhas)
        if opts_roi:
            st_echarts(options=opts_roi, height="360px", width="100%", key="echarts_aba3_roi")


# ==============================================================================
# VISÃO 4: CATÁLOGO DE DADOS & GUIA DOS GRÁFICOS
# ==============================================================================
elif aba_ativa == "4. Catálogo de Dados & Guia dos Gráficos":
    st.markdown("<div class='section-header'>Guia de Leitura Executiva, Regras de Metas e Glossário de Indicadores</div>", unsafe_allow_html=True)
    st.caption("Entenda como interpretar cada gráfico, como as metas comerciais são distribuídas ao longo do ano e o que cada indicador representa para o negócio.")

    st.markdown("""
    ### 1. Como funcionam as Metas nos Gráficos

    #### A. Por que a Meta Mensal e a Meta Diária sobem e descem ao longo do tempo?
    No varejo, o volume de vendas muda bastante conforme a época do ano e o dia da semana. Para que a cobrança de resultados seja justa com a realidade comercial da **Veloja**, a meta anual não é dividida em partes iguais:

    1. **Meta Mensal (acompanha o calendário do varejo):**
       - Cada mês tem um objetivo próprio definido pelo Planejamento Financeiro:
       - **Fevereiro (R$ 4,35 mi):** Meta mais baixa do ano por ter apenas 28 dias e o feriado de Carnaval.
       - **Maio (R$ 6,30 mi):** Meta mais alta no primeiro semestre por conta das vendas de **Dia das Mães**.
       - **Novembro (R$ 9,45 mi) e Dezembro (R$ 8,50 mi):** Maiores metas do ano, impulsionadas pela **Black Friday** e pelo **Natal**.
       - É por isso que o **Marcador de Meta Mensal** muda de altura de um mês para o outro no gráfico de barras.

    2. **Meta Diária (acompanha o ritmo de compras da semana):**
       - Dentro de cada mês, o comportamento do consumidor varia conforme o dia da semana:
       - **Segunda e Terça-feira:** Concentram o maior volume de pedidos da semana e, por isso, têm uma meta diária mais alta.
       - **Sábado e Domingo:** Têm movimento naturalmente menor no site e no aplicativo, recebendo uma meta diária mais baixa.
       - Somando as metas de todos os dias do mês, o valor fecha exatamente com a **Meta Mensal** planejada.

    ---

    #### B. O que é o "Piso Faixa Esperada (-1 DP)" no gráfico de evolução diária?
    * As vendas de um dia nunca são idênticas às do dia anterior — pequenas variações para cima ou para baixo fazem parte da rotina comercial.
    * A linha pontilhada amarela (**Piso da Faixa Esperada**) mostra até onde uma oscilação diária é considerada **normal** com base no histórico daquele dia da semana:
      - **Acima da linha tracejada azul (Meta Diária):** O dia bateu ou superou a meta.
      - **Entre a linha pontilhada amarela e a linha azul:** O dia ficou ligeiramente abaixo da meta, mas dentro da variação normal de vendas.
      - **Abaixo da linha pontilhada amarela:** A queda foi maior do que o comportamento normal da operação e merece atenção da equipe comercial.

    ---

    ### 2. Como ler as Cores do Semáforo
    """)

    df_rag_doc = pd.DataFrame([
        {
            "Cor do Semáforo": "Verde Escuro",
            "Indicadores de Resultado (Receita, Pedidos, Ticket, Margem, ROAS)": "100% ou mais da meta atingida (Meta batida ou superada)",
            "Indicador de Desconto (Taxa de Desconto %)": "Até 95% do limite máximo (Desconto sob controle, protegendo o lucro)",
            "O que fazer": "Resultado saudável; manter a estratégia atual."
        },
        {
            "Cor do Semáforo": "Verde Claro",
            "Indicadores de Resultado (Receita, Pedidos, Ticket, Margem, ROAS)": "Entre 95,0% e 99,9% da meta (Muito próximo do objetivo)",
            "Indicador de Desconto (Taxa de Desconto %)": "Entre 95,1% e 100,0% do limite máximo (Dentro do limite planejado)",
            "O que fazer": "Desempenho entregue dentro da margem de tolerância da operação."
        },
        {
            "Cor do Semáforo": "Amarelo",
            "Indicadores de Resultado (Receita, Pedidos, Ticket, Margem, ROAS)": "Entre 80,0% e 94,9% da meta (Sinal de atenção)",
            "Indicador de Desconto (Taxa de Desconto %)": "Entre 100,1% e 120,0% do limite máximo (Desconto acima do planejado)",
            "O que fazer": "Acompanhar de perto as campanhas, conversão de vendas ou uso de cupons."
        },
        {
            "Cor do Semáforo": "Vermelho",
            "Indicadores de Resultado (Receita, Pedidos, Ticket, Margem, ROAS)": "Abaixo de 80,0% da meta (Resultado crítico)",
            "Indicador de Desconto (Taxa de Desconto %)": "Acima de 120,0% do limite máximo (Excesso de desconto reduzindo o lucro)",
            "O que fazer": "Ação imediata: revisar preços, estoque, meios de pagamento ou campanhas."
        },
    ])
    st.dataframe(df_rag_doc, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### 3. Glossário dos Indicadores de Negócio")

    df_kpis_doc = pd.DataFrame([
        {
            "Visão do Painel": "1. Visão Executiva",
            "Indicador": "Receita Líquida",
            "Como é calculado": "Valor total dos itens vendidos menos os descontos aplicados (considerando apenas pedidos pagos e aprovados)",
            "Objetivo": "Quanto maior, melhor",
            "Para que serve": "Mostra o dinheiro efetivamente faturado pela empresa, já descontando promoções e excluindo pedidos cancelados ou devolvidos."
        },
        {
            "Visão do Painel": "1. Visão Executiva",
            "Indicador": "Pedidos Válidos",
            "Como é calculado": "Total de pedidos com pagamento aprovado (exclui cancelados, devolvidos e falhas de pagamento)",
            "Objetivo": "Quanto maior, melhor",
            "Para que serve": "Mede o volume real de compras concluídas com sucesso pelos clientes."
        },
        {
            "Visão do Painel": "1. Visão Executiva",
            "Indicador": "Ticket Médio (AOV)",
            "Como é calculado": "Receita Líquida dividida pelo número de Pedidos Válidos",
            "Objetivo": "Quanto maior, melhor",
            "Para que serve": "Mostra o valor médio que cada cliente gasta por compra. Ajuda a entender se a empresa está vendendo cestas mais caras ou mais baratas."
        },
        {
            "Visão do Painel": "2. Produtos & Margem",
            "Indicador": "Margem de Contribuição (R$ e %)",
            "Como é calculado": "Receita Líquida menos o custo de compra/fabricação dos produtos vendidos",
            "Objetivo": "Quanto maior, melhor",
            "Para que serve": "Indica quanto sobra de lucro bruto das vendas após pagar o custo da mercadoria."
        },
        {
            "Visão do Painel": "2. Produtos & Margem",
            "Indicador": "Taxa de Desconto Média (%)",
            "Como é calculado": "Total de descontos concedidos dividido pelo valor bruto de tabela dos produtos",
            "Objetivo": "Quanto menor, melhor",
            "Para que serve": "Controla o percentual de preço aberto em promoções e cupons para evitar que descontos excessivos corroam a margem de lucro."
        },
        {
            "Visão do Painel": "3. Campanhas & ROAS",
            "Indicador": "ROAS Consolidado (Retorno/Custo)",
            "Como é calculado": "Receita gerada pelas campanhas (em até 14 dias após o clique) dividida pelo valor gasto em anúncios",
            "Objetivo": "Quanto maior, melhor",
            "Para que serve": "Mostra quantos reais voltaram em vendas para cada R$ 1,00 investido em divulgação e marketing."
        },
    ])
    st.dataframe(df_kpis_doc, use_container_width=True, hide_index=True)


