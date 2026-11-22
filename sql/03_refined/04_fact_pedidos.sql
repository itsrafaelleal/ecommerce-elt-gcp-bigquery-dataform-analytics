
-- CAMADA REFINED — FATO PEDIDOS (fact_pedidos)
-- TABELA: fact_pedidos
-- DESCRIÇÃO: Fato consolidada no nível de pedido, agregando valores brutos, descontos, receita líquida, pagamentos aprovados e flag de pedido válido

CREATE OR REPLACE TABLE `veloja-ecommerce-medalhao.refined.fact_pedidos` AS

-- Cabeçalho dos pedidos da camada Trusted
WITH pedidos AS (
  SELECT
    order_id,
    customer_id,
    data_pedido,
    DATE(data_pedido) AS data_pedido_date,
    status_pedido,
    origem_pedido,
    cupom,
    frete
  FROM `veloja-ecommerce-medalhao.trusted.pedidos`
),

-- itens por pedido
itens_agregados AS (
  SELECT
    order_id,
    SUM(quantidade * preco_unitario) AS valor_itens_bruto,
    SUM(desconto_item) AS valor_desconto,
    SUM((quantidade * preco_unitario) - desconto_item) AS valor_receita_liquida
  FROM `veloja-ecommerce-medalhao.trusted.itens_pedido`
  GROUP BY order_id
),

-- pagamentos aprovados por pedido
pagamentos_agregados AS (
  SELECT
    order_id,
    SUM(CASE WHEN status_pagamento = 'aprovado' THEN valor_pago ELSE 0 END) AS valor_pago_aprovado
  FROM `veloja-ecommerce-medalhao.trusted.pagamentos`
  GROUP BY order_id
),

-- Consolidação dimensional
pedidos_consolidados AS (
  SELECT
    p.order_id,
    p.customer_id,
    p.data_pedido,
    p.data_pedido_date,
    p.status_pedido,
    p.origem_pedido,
    p.cupom,
    p.frete,
    
    -- Valores dos itens com tratamento de nulos
    COALESCE(i.valor_itens_bruto, 0.00) AS valor_itens_bruto,
    COALESCE(i.valor_desconto, 0.00) AS valor_desconto,
    COALESCE(i.valor_receita_liquida, 0.00) AS valor_receita_liquida,

    -- Valor financeiro de liquidação aprovada
    COALESCE(pg.valor_pago_aprovado, 0.00) AS valor_pago_aprovado,

    -- Regra de Negócio: Este pedido conta como venda aprovada/faturada
    CASE
      WHEN p.status_pedido NOT IN ('cancelado', 'devolvido', 'falha_pagamento')
       AND COALESCE(pg.valor_pago_aprovado, 0.00) > 0
      THEN TRUE
      ELSE FALSE
    END AS flag_pedido_valido,

    CURRENT_TIMESTAMP() AS data_processamento

  FROM pedidos p
  LEFT JOIN itens_agregados i
    ON p.order_id = i.order_id
  LEFT JOIN pagamentos_agregados pg
    ON p.order_id = pg.order_id
)

SELECT
  order_id,
  customer_id,
  data_pedido,
  data_pedido_date,
  status_pedido,
  origem_pedido,
  cupom,
  frete,
  valor_itens_bruto,
  valor_desconto,
  valor_receita_liquida,
  valor_pago_aprovado,
  flag_pedido_valido,
  data_processamento
FROM pedidos_consolidados;
