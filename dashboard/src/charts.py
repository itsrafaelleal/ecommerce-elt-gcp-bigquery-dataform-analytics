"""
Módulo de Visualizações Gráficas (Apache ECharts)
Gera os dicionários 'options' para renderização via streamlit-echarts.
Inclui marcadores visuais de Meta e coloração pelo Semáforo de 4 níveis:
- >= 100%: Verde Escuro (#059669)
- 95% a 99,9%: Verde Claro (#6EE7B7)
- 80% a 94,9%: Amarelo (#F59E0B)
- < 80%: Vermelho (#EF4444)
Sem ícones ou emojis decorativos (apenas cores e marcadores de semáforo).
"""

from typing import Dict, Any
import pandas as pd


# Paleta Semântica de Semáforo (4 Níveis) e Identidade Corporativa
COLOR_DARK_GREEN = "#059669"     # >= 100% da meta (Verde Escuro)
COLOR_LIGHT_GREEN = "#6EE7B7"    # 95% a 99,9% da meta (Verde Claro)
COLOR_WARNING_AMBER = "#F59E0B"  # 80% a 94,9% da meta (Amarelo)
COLOR_DANGER_RED = "#EF4444"     # < 80% da meta (Vermelho)

COLOR_PRIMARY_BLUE = "#3B82F6"   # Séries neutras / volume
COLOR_TARGET_CYAN = "#38BDF8"    # Linha / Marcador de Meta
COLOR_MUTED_GRAY = "#64748B"     # Contexto / Custos / Não Informado
COLOR_PURPLE = "#8B5CF6"         # Secundário
GRID_LINE_COLOR = "#334155"      # Grid sutil para Dark Mode


def get_rag_color(pct: float, invertido: bool = False) -> str:
    """Retorna a cor hexadecimal do semáforo de 4 níveis."""
    if not invertido:
        if pct >= 100.0:
            return COLOR_DARK_GREEN
        elif pct >= 95.0:
            return COLOR_LIGHT_GREEN
        elif pct >= 80.0:
            return COLOR_WARNING_AMBER
        else:
            return COLOR_DANGER_RED
    else:
        if pct <= 95.0:
            return COLOR_DARK_GREEN
        elif pct <= 100.0:
            return COLOR_LIGHT_GREEN
        elif pct <= 120.0:
            return COLOR_WARNING_AMBER
        else:
            return COLOR_DANGER_RED


def chart_evolucao_vendas_com_meta(df_metas: pd.DataFrame) -> Dict[str, Any]:
    """
    Gráfico Diário: Receita Realizada vs. Meta Diária Sazonal + Faixa Esperada.
    Pontos diários coloridos pelos 4 níveis do semáforo.
    """
    if df_metas.empty:
        return {}

    df_s = df_metas.sort_values("data_referencia_dt")
    datas = df_s["data_referencia"].tolist()
    metas = df_s["meta_diaria_receita"].round(2).tolist()
    faixa_min = df_s["faixa_esperada_min"].round(2).tolist()

    pontos_realizados = []
    for _, row in df_s.iterrows():
        real = float(row["receita_realizada"])
        meta = float(row["meta_diaria_receita"])
        pct = (real / meta * 100.0) if meta > 0 else 0.0
        cor = get_rag_color(pct)
        pontos_realizados.append({
            "value": round(real, 2),
            "itemStyle": {"color": cor}
        })

    return {
        "backgroundColor": "transparent",
        "tooltip": {
            "trigger": "axis",
            "backgroundColor": "#1E293B",
            "borderColor": "#475569",
            "textStyle": {"color": "#F8FAFC"},
        },
        "legend": {
            "top": "0%",
            "textStyle": {"color": "#CBD5E1"},
            "data": ["Receita Realizada (R$)", "Meta Diária (R$)", "Piso Faixa Esperada (-1 DP)"]
        },
        "grid": {
            "top": "14%",
            "left": "4%",
            "right": "4%",
            "bottom": "18%",
            "containLabel": True
        },
        "xAxis": {
            "type": "category",
            "data": datas,
            "boundaryGap": False,
            "axisLine": {"lineStyle": {"color": "#64748B"}},
            "axisLabel": {"color": "#94A3B8"}
        },
        "yAxis": {
            "type": "value",
            "name": "Receita (R$)",
            "nameTextStyle": {"color": "#94A3B8"},
            "splitLine": {"lineStyle": {"color": GRID_LINE_COLOR, "type": "dashed"}},
            "axisLabel": {"color": "#94A3B8", "formatter": "R$ {value}"}
        },
        "dataZoom": [
            {"type": "inside", "start": 0, "end": 100},
            {
                "type": "slider",
                "start": 0,
                "end": 100,
                "height": 20,
                "bottom": "2%",
                "borderColor": "#334155",
                "fillerColor": "rgba(56, 189, 248, 0.2)",
                "textStyle": {"color": "#94A3B8"}
            }
        ],
        "series": [
            {
                "name": "Receita Realizada (R$)",
                "type": "line",
                "smooth": True,
                "showSymbol": True,
                "symbolSize": 6,
                "lineStyle": {"width": 2.5, "color": COLOR_PRIMARY_BLUE},
                "areaStyle": {
                    "color": {
                        "type": "linear",
                        "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [
                            {"offset": 0, "color": "rgba(59, 130, 246, 0.25)"},
                            {"offset": 1, "color": "rgba(59, 130, 246, 0.0)"}
                        ]
                    }
                },
                "data": pontos_realizados
            },
            {
                "name": "Meta Diária (R$)",
                "type": "line",
                "smooth": True,
                "showSymbol": False,
                "itemStyle": {"color": COLOR_TARGET_CYAN},
                "lineStyle": {"width": 2.5, "type": "dashed", "color": COLOR_TARGET_CYAN},
                "data": metas
            },
            {
                "name": "Piso Faixa Esperada (-1 DP)",
                "type": "line",
                "smooth": True,
                "showSymbol": False,
                "itemStyle": {"color": COLOR_WARNING_AMBER},
                "lineStyle": {"width": 1.5, "type": "dotted", "color": COLOR_WARNING_AMBER},
                "data": faixa_min
            }
        ]
    }


def chart_mensal_realizado_vs_meta(df_metas: pd.DataFrame) -> Dict[str, Any]:
    """
    Gráfico Mensal: Barras do Realizado Mensal coloridas pelos 4 níveis do Semáforo
    com marcador horizontal e linha tracejada da Meta Mensal.
    """
    if df_metas.empty:
        return {}

    m_agg = df_metas.groupby("ano_mes").agg({
        "receita_realizada": "sum",
        "meta_diaria_receita": "sum"
    }).reset_index().sort_values("ano_mes")

    meses = m_agg["ano_mes"].tolist()
    metas_mes = m_agg["meta_diaria_receita"].round(2).tolist()

    barras_realizadas = []
    for _, row in m_agg.iterrows():
        real = float(row["receita_realizada"])
        meta = float(row["meta_diaria_receita"])
        pct = (real / meta * 100.0) if meta > 0 else 0.0
        cor = get_rag_color(pct)

        barras_realizadas.append({
            "value": round(real, 2),
            "itemStyle": {"color": cor, "borderRadius": [5, 5, 0, 0]}
        })

    return {
        "backgroundColor": "transparent",
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"},
            "backgroundColor": "#1E293B",
            "borderColor": "#475569",
            "textStyle": {"color": "#F8FAFC"}
        },
        "legend": {
            "top": "0%",
            "textStyle": {"color": "#CBD5E1"},
            "data": ["Receita Realizada (Cor = Semáforo)", "Meta Mensal (Orçamento)"]
        },
        "grid": {
            "top": "14%",
            "left": "4%",
            "right": "4%",
            "bottom": "8%",
            "containLabel": True
        },
        "xAxis": {
            "type": "category",
            "data": meses,
            "axisLine": {"lineStyle": {"color": "#64748B"}},
            "axisLabel": {"color": "#F8FAFC", "fontWeight": "500"}
        },
        "yAxis": {
            "type": "value",
            "name": "Receita Mensal (R$)",
            "nameTextStyle": {"color": "#94A3B8"},
            "splitLine": {"lineStyle": {"color": GRID_LINE_COLOR, "type": "dashed"}},
            "axisLabel": {"color": "#94A3B8", "formatter": "R$ {value}"}
        },
        "series": [
            {
                "name": "Receita Realizada (Cor = Semáforo)",
                "type": "bar",
                "barMaxWidth": 38,
                "data": barras_realizadas
            },
            {
                "name": "Meta Mensal (Orçamento)",
                "type": "line",
                "symbol": "rect",
                "symbolSize": [28, 5],
                "itemStyle": {"color": "#F8FAFC"},
                "lineStyle": {"width": 2, "type": "dashed", "color": COLOR_TARGET_CYAN},
                "data": metas_mes
            }
        ]
    }


def chart_share_origem(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Gráfico de Rosca (Donut): Distribuição do faturamento por Canal de Origem.
    - 5 cores distintas mapeadas por canal (evitando que SITE e NAO_INFORMADO repitam cor).
    - Rótulo externo visível direto na fatia com Nome do Canal e Percentual ({b}: {d}%).
    """
    if df.empty or "origem_pedido" not in df.columns:
        return {}

    agrupado = df.groupby("origem_pedido")["valor_receita_liquida"].sum().reset_index()
    agrupado = agrupado.sort_values("valor_receita_liquida", ascending=False)

    # Mapa fixo de cores distintas por canal e nomes legíveis
    label_map = {
        "site": "Site",
        "app": "App",
        "marketplace": "Marketplace",
        "loja_fisica": "Loja Física",
        "nao_informado": "Não Informado",
    }
    color_map = {
        "site": "#3B82F6",           # Azul Royal
        "app": "#059669",            # Verde Esmeralda
        "marketplace": "#8B5CF6",    # Roxo
        "loja_fisica": "#F59E0B",    # Laranja / Âmbar
        "nao_informado": "#64748B",  # Cinza Ardósia (distinto do Azul do Site)
    }

    data_series = []
    for _, row in agrupado.iterrows():
        raw_key = str(row["origem_pedido"]).lower().strip()
        nome_exibicao = label_map.get(raw_key, raw_key.replace("_", " ").title())
        cor_fatia = color_map.get(raw_key, "#38BDF8")
        data_series.append({
            "name": nome_exibicao,
            "value": round(float(row["valor_receita_liquida"]), 2),
            "itemStyle": {"color": cor_fatia}
        })

    return {
        "backgroundColor": "transparent",
        "tooltip": {
            "trigger": "item",
            "backgroundColor": "#1E293B",
            "borderColor": "#475569",
            "textStyle": {"color": "#F8FAFC"},
            "formatter": "{b}: R$ {c} ({d}%)"
        },
        "legend": {
            "bottom": "0%",
            "left": "center",
            "textStyle": {"color": "#94A3B8"}
        },
        "series": [
            {
                "name": "Origem do Pedido",
                "type": "pie",
                "radius": ["40%", "66%"],
                "center": ["50%", "44%"],
                "avoidLabelOverlap": True,
                "itemStyle": {"borderRadius": 6, "borderColor": "#0F172A", "borderWidth": 2},
                "label": {
                    "show": True,
                    "position": "outside",
                    "formatter": "{b}: {d}%",
                    "color": "#F8FAFC",
                    "fontSize": 12,
                    "fontWeight": "600"
                },
                "labelLine": {
                    "show": True,
                    "length": 12,
                    "length2": 14,
                    "lineStyle": {"color": "#64748B", "width": 1.5}
                },
                "emphasis": {
                    "label": {"show": True, "fontSize": 14, "fontWeight": "bold", "color": "#FFFFFF"}
                },
                "data": data_series
            }
        ]
    }


def chart_margem_desconto_metas(df_metas: pd.DataFrame) -> Dict[str, Any]:
    """
    Gráfico Mensal de Eficiência Operacional:
    Evolução da Margem Bruta (%) e Taxa de Desconto (%) com linhas marcadoras de Meta e Teto.
    """
    if df_metas.empty:
        return {}

    m_agg = df_metas.groupby("ano_mes").agg({
        "margem_pct_realizada": "mean",
        "desconto_pct_realizado": "mean",
        "meta_margem_pct": "first",
        "teto_desconto_pct": "first"
    }).reset_index().sort_values("ano_mes")

    meses = m_agg["ano_mes"].tolist()
    margem_real = m_agg["margem_pct_realizada"].round(2).tolist()
    desconto_real = m_agg["desconto_pct_realizado"].round(2).tolist()
    meta_margem = m_agg["meta_margem_pct"].round(2).tolist()
    teto_desc = m_agg["teto_desconto_pct"].round(2).tolist()

    return {
        "backgroundColor": "transparent",
        "tooltip": {
            "trigger": "axis",
            "backgroundColor": "#1E293B",
            "borderColor": "#475569",
            "textStyle": {"color": "#F8FAFC"}
        },
        "legend": {
            "top": "0%",
            "textStyle": {"color": "#CBD5E1"},
            "data": ["Margem Realizada (%)", "Meta Margem (%)", "Desconto Realizado (%)", "Teto Desconto (%)"]
        },
        "grid": {
            "top": "16%",
            "left": "4%",
            "right": "4%",
            "bottom": "8%",
            "containLabel": True
        },
        "xAxis": {
            "type": "category",
            "data": meses,
            "axisLine": {"lineStyle": {"color": "#64748B"}},
            "axisLabel": {"color": "#94A3B8"}
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Margem (%)",
                "min": 30,
                "max": 42,
                "nameTextStyle": {"color": "#94A3B8"},
                "splitLine": {"lineStyle": {"color": GRID_LINE_COLOR, "type": "dashed"}},
                "axisLabel": {"color": "#94A3B8", "formatter": "{value}%"}
            },
            {
                "type": "value",
                "name": "Desconto (%)",
                "min": 0,
                "max": 10,
                "nameTextStyle": {"color": "#94A3B8"},
                "splitLine": {"show": False},
                "axisLabel": {"color": "#94A3B8", "formatter": "{value}%"}
            }
        ],
        "series": [
            {
                "name": "Margem Realizada (%)",
                "type": "line",
                "yAxisIndex": 0,
                "smooth": True,
                "symbolSize": 8,
                "itemStyle": {"color": COLOR_DARK_GREEN},
                "lineStyle": {"width": 3, "color": COLOR_DARK_GREEN},
                "data": margem_real
            },
            {
                "name": "Meta Margem (%)",
                "type": "line",
                "yAxisIndex": 0,
                "showSymbol": False,
                "itemStyle": {"color": COLOR_TARGET_CYAN},
                "lineStyle": {"width": 2, "type": "dashed", "color": COLOR_TARGET_CYAN},
                "data": meta_margem
            },
            {
                "name": "Desconto Realizado (%)",
                "type": "bar",
                "yAxisIndex": 1,
                "barMaxWidth": 24,
                "itemStyle": {"color": COLOR_WARNING_AMBER, "borderRadius": [4, 4, 0, 0]},
                "data": desconto_real
            },
            {
                "name": "Teto Desconto (%)",
                "type": "line",
                "yAxisIndex": 1,
                "showSymbol": False,
                "itemStyle": {"color": COLOR_DANGER_RED},
                "lineStyle": {"width": 2, "type": "dashed", "color": COLOR_DANGER_RED},
                "data": teto_desc
            }
        ]
    }


def chart_roas_campanhas_com_meta(df_campanhas: pd.DataFrame, meta_roas: float = 208.0) -> Dict[str, Any]:
    """
    Gráfico de ROAS por Campanha com Marcador Vertical de Meta (markLine)
    e barras coloridas pelos 4 níveis do semáforo.
    """
    if df_campanhas.empty:
        return {}

    agrupado = df_campanhas.groupby("campanha").agg({
        "custo_total": "sum",
        "receita_atribuida": "sum"
    }).reset_index()
    agrupado["roas"] = agrupado["receita_atribuida"] / agrupado["custo_total"].clip(lower=1.0)
    agrupado = agrupado.sort_values("roas", ascending=True)

    campanhas = [c.replace("_", " ").title() for c in agrupado["campanha"].tolist()]
    barras_roas = []
    for _, row in agrupado.iterrows():
        r = round(float(row["roas"]), 2)
        pct = (r / meta_roas * 100.0) if meta_roas > 0 else 0.0
        cor = get_rag_color(pct)
        barras_roas.append({
            "value": r,
            "itemStyle": {"color": cor, "borderRadius": [0, 5, 5, 0]}
        })

    return {
        "backgroundColor": "transparent",
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"},
            "backgroundColor": "#1E293B",
            "borderColor": "#475569",
            "textStyle": {"color": "#F8FAFC"}
        },
        "grid": {
            "top": "12%",
            "left": "3%",
            "right": "10%",
            "bottom": "8%",
            "containLabel": True
        },
        "xAxis": {
            "type": "value",
            "name": "ROAS (x)",
            "nameTextStyle": {"color": "#94A3B8"},
            "splitLine": {"lineStyle": {"color": GRID_LINE_COLOR, "type": "dashed"}},
            "axisLabel": {"color": "#94A3B8", "formatter": "{value}x"}
        },
        "yAxis": {
            "type": "category",
            "data": campanhas,
            "axisLine": {"lineStyle": {"color": "#64748B"}},
            "axisLabel": {"color": "#F8FAFC", "fontWeight": "500"}
        },
        "series": [
            {
                "name": "ROAS Realizado",
                "type": "bar",
                "data": barras_roas,
                "label": {
                    "show": True,
                    "position": "right",
                    "color": "#F8FAFC",
                    "formatter": "{c}x"
                },
                "markLine": {
                    "symbol": ["none", "none"],
                    "label": {
                        "show": True,
                        "position": "end",
                        "formatter": f"Meta: {meta_roas:.0f}x",
                        "color": COLOR_TARGET_CYAN,
                        "fontWeight": "bold"
                    },
                    "lineStyle": {
                        "color": COLOR_TARGET_CYAN,
                        "type": "dashed",
                        "width": 2.5
                    },
                    "data": [{"xAxis": meta_roas}]
                }
            }
        ]
    }


def chart_metodos_pagamento(df: pd.DataFrame) -> Dict[str, Any]:
    """Gráfico de Barras Horizontais: Faturamento aprovado por Método de Pagamento."""
    if df.empty:
        return {}

    df_aprov = df[df["status_pagamento"] == "aprovado"] if "status_pagamento" in df.columns else df
    agrupado = df_aprov.groupby("metodo_pagamento")["total_valor"].sum().reset_index()
    agrupado = agrupado.sort_values("total_valor", ascending=True)

    metodos = [m.replace("_", " ").title() for m in agrupado["metodo_pagamento"].tolist()]
    valores = agrupado["total_valor"].round(2).tolist()

    return {
        "backgroundColor": "transparent",
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"},
            "backgroundColor": "#1E293B",
            "borderColor": "#475569",
            "textStyle": {"color": "#F8FAFC"}
        },
        "grid": {"top": "8%", "left": "3%", "right": "10%", "bottom": "5%", "containLabel": True},
        "xAxis": {
            "type": "value",
            "axisLine": {"show": False},
            "splitLine": {"lineStyle": {"color": GRID_LINE_COLOR, "type": "dashed"}},
            "axisLabel": {"color": "#94A3B8", "formatter": "R$ {value}"}
        },
        "yAxis": {
            "type": "category",
            "data": metodos,
            "axisLine": {"lineStyle": {"color": "#64748B"}},
            "axisLabel": {"color": "#F8FAFC", "fontWeight": "500"}
        },
        "series": [
            {
                "name": "Total Aprovado",
                "type": "bar",
                "data": valores,
                "itemStyle": {"color": COLOR_PRIMARY_BLUE, "borderRadius": [0, 4, 4, 0]},
                "label": {"show": True, "position": "right", "color": "#94A3B8", "formatter": "R$ {c}"}
            }
        ]
    }


def chart_top_categorias(df: pd.DataFrame) -> Dict[str, Any]:
    """Gráfico de Barras Horizontais: Top Categorias por Receita Líquida."""
    if df.empty or "categoria" not in df.columns:
        return {}

    agrupado = df.groupby("categoria")["receita_item"].sum().reset_index()
    agrupado = agrupado.sort_values("receita_item", ascending=True).tail(8)

    categorias = [c.title() for c in agrupado["categoria"].tolist()]
    receitas = agrupado["receita_item"].round(2).tolist()

    return {
        "backgroundColor": "transparent",
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"},
            "backgroundColor": "#1E293B",
            "borderColor": "#475569",
            "textStyle": {"color": "#F8FAFC"}
        },
        "grid": {"top": "8%", "left": "3%", "right": "10%", "bottom": "5%", "containLabel": True},
        "xAxis": {
            "type": "value",
            "axisLine": {"show": False},
            "splitLine": {"lineStyle": {"color": GRID_LINE_COLOR, "type": "dashed"}},
            "axisLabel": {"color": "#94A3B8", "formatter": "R$ {value}"}
        },
        "yAxis": {
            "type": "category",
            "data": categorias,
            "axisLine": {"lineStyle": {"color": "#64748B"}},
            "axisLabel": {"color": "#F8FAFC"}
        },
        "series": [
            {
                "name": "Receita Líquida",
                "type": "bar",
                "data": receitas,
                "itemStyle": {"color": COLOR_DARK_GREEN, "borderRadius": [0, 4, 4, 0]},
                "label": {"show": True, "position": "right", "color": "#94A3B8", "formatter": "R$ {c}"}
            }
        ]
    }


def chart_campanhas_roi(df: pd.DataFrame) -> Dict[str, Any]:
    """Gráfico de Barras Agrupadas: Custo Investido vs Receita Atribuída por Campanha."""
    if df.empty or "campanha" not in df.columns:
        return {}

    agrupado = df.groupby("campanha").agg({
        "custo_total": "sum",
        "receita_atribuida": "sum"
    }).reset_index().sort_values("receita_atribuida", ascending=False)

    campanhas = [c.replace("_", " ").title() for c in agrupado["campanha"].tolist()]
    custos = agrupado["custo_total"].round(2).tolist()
    receitas = agrupado["receita_atribuida"].round(2).tolist()

    return {
        "backgroundColor": "transparent",
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"},
            "backgroundColor": "#1E293B",
            "borderColor": "#475569",
            "textStyle": {"color": "#F8FAFC"}
        },
        "legend": {"bottom": "0%", "textStyle": {"color": "#94A3B8"}},
        "grid": {"top": "10%", "left": "4%", "right": "4%", "bottom": "15%", "containLabel": True},
        "xAxis": {
            "type": "category",
            "data": campanhas,
            "axisLine": {"lineStyle": {"color": "#64748B"}},
            "axisLabel": {"color": "#94A3B8", "interval": 0, "rotate": 15}
        },
        "yAxis": {
            "type": "value",
            "name": "Valores (R$)",
            "nameTextStyle": {"color": "#94A3B8"},
            "splitLine": {"lineStyle": {"color": GRID_LINE_COLOR, "type": "dashed"}},
            "axisLabel": {"color": "#94A3B8"}
        },
        "series": [
            {
                "name": "Custo Investido (Mídia)",
                "type": "bar",
                "data": custos,
                "itemStyle": {"color": COLOR_MUTED_GRAY, "borderRadius": [4, 4, 0, 0]}
            },
            {
                "name": "Receita Atribuída (14d)",
                "type": "bar",
                "data": receitas,
                "itemStyle": {"color": COLOR_DARK_GREEN, "borderRadius": [4, 4, 0, 0]}
            }
        ]
    }
