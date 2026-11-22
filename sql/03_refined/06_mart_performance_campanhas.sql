
-- CAMADA REFINED — MART PERFORMANCE DE CAMPANHAS (mart_performance_campanhas)
-- TABELA: mart_performance_campanhas
-- DESCRIÇÃO: Consolida investimento de marketing e faturamento com atribuição de 14 dias

CREATE OR REPLACE TABLE `veloja-ecommerce-medalhao.refined.mart_performance_campanhas` AS
WITH eventos_agrupados AS (
  -- Agrega custos e eventos no nível da chave granular do mart (campanha, canal)
  SELECT
    campanha,
    canal,
    MIN(DATE(data_evento)) AS periodo_inicio,
    MAX(DATE(data_evento)) AS periodo_fim,
    CAST(ROUND(SUM(custo_campanha), 2) AS NUMERIC) AS custo_total,
    COUNT(event_id) AS eventos,
    COUNT(DISTINCT customer_id) AS clientes_impactados
  FROM `veloja-ecommerce-medalhao.trusted.eventos_marketing`
  GROUP BY campanha, canal
),

pedidos_validos AS (
  -- Apenas pedidos válidos que compõem faturamento oficial
  SELECT
    order_id,
    customer_id,
    data_pedido,
    valor_receita_liquida
  FROM `veloja-ecommerce-medalhao.refined.fact_pedidos`
  WHERE flag_pedido_valido = TRUE
),

atribuicoes_pedidos AS (
  -- Janela de Atribuição: pedido realizado pelo cliente até 14 dias após o evento
  SELECT
    e.campanha,
    e.canal,
    p.order_id,
    p.valor_receita_liquida
  FROM `veloja-ecommerce-medalhao.trusted.eventos_marketing` e
  INNER JOIN pedidos_validos p
    ON e.customer_id = p.customer_id
    AND p.data_pedido >= e.data_evento
    AND p.data_pedido <= TIMESTAMP_ADD(e.data_evento, INTERVAL 14 DAY)
  GROUP BY e.campanha, e.canal, p.order_id, p.valor_receita_liquida
),

atribuicoes_agrupadas AS (
  -- Consolida conversão atribuída por campanha e canal
  SELECT
    campanha,
    canal,
    COUNT(DISTINCT order_id) AS pedidos_atribuidos,
    CAST(ROUND(SUM(valor_receita_liquida), 2) AS NUMERIC) AS receita_atribuida
  FROM atribuicoes_pedidos
  GROUP BY campanha, canal
)

SELECT
  e.campanha,
  e.canal,
  e.periodo_inicio,
  e.periodo_fim,
  e.custo_total,
  e.eventos,
  e.clientes_impactados,
  COALESCE(a.pedidos_atribuidos, 0) AS pedidos_atribuidos,
  COALESCE(a.receita_atribuida, 0) AS receita_atribuida,
  CURRENT_TIMESTAMP() AS data_processamento
FROM eventos_agrupados e
LEFT JOIN atribuicoes_agrupadas a
  ON e.campanha = a.campanha
  AND e.canal = a.canal
ORDER BY e.campanha, e.canal;
