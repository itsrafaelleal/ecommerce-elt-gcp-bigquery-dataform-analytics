-- CAMADA REFINED — MART METAS VS REALIZADO (mart_metas_vs_realizado)
-- TABELA: mart_metas_vs_realizado
-- DESCRIÇÃO: Compara desempenho diário e acumulado mensal com as metas Top-Down, faixas esperadas estatísticas e status de semáforo em 4 níveis (VERDE_ESCURO, VERDE_CLARO, AMARELO, VERMELHO)

CREATE OR REPLACE TABLE `veloja-ecommerce-medalhao.refined.mart_metas_vs_realizado` AS
WITH vendas_dia AS (
  SELECT
    data_pedido AS data_referencia,
    pedidos AS pedidos_realizados,
    clientes_unicos,
    receita_liquida AS receita_realizada,
    ticket_medio AS ticket_realizado,
    itens_vendidos
  FROM `veloja-ecommerce-medalhao.refined.mart_vendas_diarias`
),

desconto_dia AS (
  SELECT
    data_pedido_date AS data_referencia,
    SUM(valor_itens_bruto) AS valor_bruto_dia,
    SUM(valor_desconto) AS valor_desconto_dia,
    CAST(ROUND(SAFE_DIVIDE(SUM(valor_desconto), SUM(valor_itens_bruto)) * 100, 2) AS NUMERIC) AS desconto_pct_realizado
  FROM `veloja-ecommerce-medalhao.refined.fact_pedidos`
  WHERE flag_pedido_valido = TRUE
  GROUP BY data_pedido_date
),

margem_dia AS (
  SELECT
    DATE(data_pedido) AS data_referencia,
    SUM(receita_item) AS receita_itens_dia,
    SUM(margem_item) AS margem_bruta_dia,
    CAST(ROUND(SAFE_DIVIDE(SUM(margem_item), SUM(receita_item)) * 100, 2) AS NUMERIC) AS margem_pct_realizada
  FROM `veloja-ecommerce-medalhao.refined.fact_itens_pedido`
  WHERE flag_item_valido = TRUE
  GROUP BY DATE(data_pedido)
),

estatistica_dow AS (
  SELECT
    FORMAT_DATE('%Y-%m', data_pedido) AS ano_mes,
    EXTRACT(DAYOFWEEK FROM data_pedido) AS num_dia_semana,
    CAST(ROUND(AVG(receita_liquida), 2) AS NUMERIC) AS media_historica_dow,
    CAST(ROUND(COALESCE(STDDEV(receita_liquida), 0), 2) AS NUMERIC) AS desvio_padrao_dow
  FROM `veloja-ecommerce-medalhao.refined.mart_vendas_diarias`
  GROUP BY 1, 2
),

consolidado AS (
  SELECT
    dm.data_referencia,
    dm.ano_mes,
    dm.num_dia_semana,
    dm.nome_dia_semana,

    -- Realizado Diário
    COALESCE(v.receita_realizada, 0.00) AS receita_realizada,
    COALESCE(v.pedidos_realizados, 0) AS pedidos_realizados,
    COALESCE(v.ticket_realizado, 0.00) AS ticket_realizado,
    COALESCE(v.itens_vendidos, 0) AS itens_vendidos,
    COALESCE(mg.margem_bruta_dia, 0.00) AS margem_bruta_realizada,
    COALESCE(mg.margem_pct_realizada, 0.00) AS margem_pct_realizada,
    COALESCE(dc.desconto_pct_realizado, 0.00) AS desconto_pct_realizado,

    -- Metas Diárias e Mensais
    dm.meta_diaria_receita,
    dm.meta_mensal_receita,
    dm.meta_diaria_pedidos,
    dm.meta_mensal_pedidos,
    dm.meta_ticket_medio,
    dm.meta_margem_pct,
    dm.teto_desconto_pct,
    dm.meta_roas,

    -- Faixa Esperada Estatística (Controle de Normalidade: Meta ± 1 Desvio-Padrão)
    CAST(ROUND(GREATEST(0, dm.meta_diaria_receita - est.desvio_padrao_dow), 2) AS NUMERIC) AS faixa_esperada_min,
    CAST(ROUND(dm.meta_diaria_receita + est.desvio_padrao_dow, 2) AS NUMERIC) AS faixa_esperada_max,

    -- % Atingimento Diário
    CAST(ROUND(SAFE_DIVIDE(COALESCE(v.receita_realizada, 0), dm.meta_diaria_receita) * 100, 2) AS NUMERIC) AS atingimento_receita_pct,
    CAST(ROUND(SAFE_DIVIDE(COALESCE(v.pedidos_realizados, 0), dm.meta_diaria_pedidos) * 100, 2) AS NUMERIC) AS atingimento_pedidos_pct,
    CAST(ROUND(SAFE_DIVIDE(COALESCE(v.ticket_realizado, 0), dm.meta_ticket_medio) * 100, 2) AS NUMERIC) AS atingimento_ticket_pct,

    -- Acumulado no Mês (MTD - Month-to-Date) para cálculo de Pace
    SUM(COALESCE(v.receita_realizada, 0)) OVER (PARTITION BY dm.ano_mes ORDER BY dm.data_referencia) AS receita_acumulada_mes,
    SUM(dm.meta_diaria_receita) OVER (PARTITION BY dm.ano_mes ORDER BY dm.data_referencia) AS meta_acumulada_mes,

    dm.limiar_verde_pct,
    dm.limiar_amarelo_pct,
    dm.origem_meta

  FROM `veloja-ecommerce-medalhao.refined.dim_metas` dm
  LEFT JOIN vendas_dia v
    ON dm.data_referencia = v.data_referencia
  LEFT JOIN desconto_dia dc
    ON dm.data_referencia = dc.data_referencia
  LEFT JOIN margem_dia mg
    ON dm.data_referencia = mg.data_referencia
  LEFT JOIN estatistica_dow est
    ON dm.ano_mes = est.ano_mes
   AND dm.num_dia_semana = est.num_dia_semana
)

SELECT
  c.*,
  CAST(ROUND(SAFE_DIVIDE(c.receita_acumulada_mes, c.meta_acumulada_mes) * 100, 2) AS NUMERIC) AS pace_atingimento_mes_pct,

  -- Status de Semáforo (4 Níveis: >= 100% VERDE_ESCURO, 95% a 99,99% VERDE_CLARO, 80% a 94,99% AMARELO, < 80% VERMELHO)
  CASE
    WHEN c.atingimento_receita_pct >= 100.0 THEN 'VERDE_ESCURO'
    WHEN c.atingimento_receita_pct >= 95.0  THEN 'VERDE_CLARO'
    WHEN c.atingimento_receita_pct >= 80.0  THEN 'AMARELO'
    ELSE 'VERMELHO'
  END AS status_receita,

  CASE
    WHEN c.atingimento_pedidos_pct >= 100.0 THEN 'VERDE_ESCURO'
    WHEN c.atingimento_pedidos_pct >= 95.0  THEN 'VERDE_CLARO'
    WHEN c.atingimento_pedidos_pct >= 80.0  THEN 'AMARELO'
    ELSE 'VERMELHO'
  END AS status_pedidos,

  CASE
    WHEN c.atingimento_ticket_pct >= 100.0 THEN 'VERDE_ESCURO'
    WHEN c.atingimento_ticket_pct >= 95.0  THEN 'VERDE_CLARO'
    WHEN c.atingimento_ticket_pct >= 80.0  THEN 'AMARELO'
    ELSE 'VERMELHO'
  END AS status_ticket,

  CASE
    WHEN SAFE_DIVIDE(c.margem_pct_realizada, c.meta_margem_pct) * 100 >= 100.0 THEN 'VERDE_ESCURO'
    WHEN SAFE_DIVIDE(c.margem_pct_realizada, c.meta_margem_pct) * 100 >= 95.0  THEN 'VERDE_CLARO'
    WHEN SAFE_DIVIDE(c.margem_pct_realizada, c.meta_margem_pct) * 100 >= 80.0  THEN 'AMARELO'
    ELSE 'VERMELHO'
  END AS status_margem,

  -- Status de Semáforo para Desconto % (MENOR É MELHOR: lógica invertida em 4 níveis!)
  CASE
    WHEN SAFE_DIVIDE(c.desconto_pct_realizado, c.teto_desconto_pct) * 100 <= 95.0  THEN 'VERDE_ESCURO'
    WHEN SAFE_DIVIDE(c.desconto_pct_realizado, c.teto_desconto_pct) * 100 <= 100.0 THEN 'VERDE_CLARO'
    WHEN SAFE_DIVIDE(c.desconto_pct_realizado, c.teto_desconto_pct) * 100 <= 120.0 THEN 'AMARELO'
    ELSE 'VERMELHO'
  END AS status_desconto,

  CURRENT_TIMESTAMP() AS data_processamento

FROM consolidado c
ORDER BY c.data_referencia;
