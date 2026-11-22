

-- CAMADA REFINED — MART VENDAS DIÁRIAS (mart_vendas_diarias)
-- TABELA: mart_vendas_diarias
-- DESCRIÇÃO: Tabela analítica diária para alimentação de dashboards de faturamento

CREATE OR REPLACE TABLE `veloja-ecommerce-medalhao.refined.mart_vendas_diarias` AS
WITH pedidos_diarios AS (
  -- Agrega métricas no nível de pedido para evitar duplicações
  SELECT
    data_pedido_date AS data_pedido,
    COUNT(DISTINCT order_id) AS pedidos,
    COUNT(DISTINCT customer_id) AS clientes_unicos,
    CAST(ROUND(SUM(valor_receita_liquida), 2) AS NUMERIC) AS receita_liquida
  FROM `veloja-ecommerce-medalhao.refined.fact_pedidos`
  WHERE flag_pedido_valido = TRUE
  GROUP BY data_pedido_date
),

itens_diarios AS (
  -- Agrega quantidade de peças físicas válidas faturadas e expedidas por dia
  SELECT
    DATE(data_pedido) AS data_pedido,
    SUM(quantidade) AS itens_vendidos
  FROM `veloja-ecommerce-medalhao.refined.fact_itens_pedido`
  WHERE flag_item_valido = TRUE
  GROUP BY DATE(data_pedido)
)

SELECT
  p.data_pedido,
  p.pedidos,
  p.clientes_unicos,
  p.receita_liquida,
  CAST(ROUND(SAFE_DIVIDE(p.receita_liquida, p.pedidos), 2) AS NUMERIC) AS ticket_medio,
  COALESCE(i.itens_vendidos, 0) AS itens_vendidos,
  CURRENT_TIMESTAMP() AS data_processamento
FROM pedidos_diarios p
LEFT JOIN itens_diarios i
  ON p.data_pedido = i.data_pedido
ORDER BY p.data_pedido;
