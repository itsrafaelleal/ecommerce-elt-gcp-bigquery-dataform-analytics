
-- CAMADA REFINED — FATO ITENS PEDIDO (fact_itens_pedido)
-- TABELA: fact_itens_pedido
-- DESCRIÇÃO: Fato granular no nível de item vendido, calculando receita líquida, custo, margem de contribuição e flag de item válido

CREATE OR REPLACE TABLE `veloja-ecommerce-medalhao.refined.fact_itens_pedido` AS

WITH itens AS (
  SELECT
    order_item_id,
    order_id,
    product_id,
    quantidade,
    preco_unitario,
    desconto_item,
    status_item
  FROM `veloja-ecommerce-medalhao.trusted.itens_pedido`
),

pedidos AS (
  SELECT
    order_id,
    customer_id,
    data_pedido,
    status_pedido
  FROM `veloja-ecommerce-medalhao.trusted.pedidos`
),

produtos AS (
  SELECT
    product_id,
    custo_unitario
  FROM `veloja-ecommerce-medalhao.trusted.produtos`
),

itens_enriquecidos AS (
  SELECT
    i.order_item_id,
    i.order_id,
    p.customer_id,
    i.product_id,
    p.data_pedido,
    i.quantidade,
    i.preco_unitario,
    i.desconto_item,

    -- Receita líquida 
    (i.quantidade * i.preco_unitario) - i.desconto_item AS receita_item,

    -- Custo total 
    i.quantidade * COALESCE(pr.custo_unitario, 0) AS custo_item,

    -- Margem 
    ((i.quantidade * i.preco_unitario) - i.desconto_item) - (i.quantidade * COALESCE(pr.custo_unitario, 0)) AS margem_item,

    -- Flag de item válido 
    CASE
      WHEN i.quantidade > 0 
       AND i.status_item NOT IN ('cancelado', 'devolvido')
      THEN TRUE
      ELSE FALSE
    END AS flag_item_valido,

    CURRENT_TIMESTAMP() AS data_processamento

  FROM itens i
  LEFT JOIN pedidos p
    ON i.order_id = p.order_id
  LEFT JOIN produtos pr
    ON i.product_id = pr.product_id
)

SELECT
  order_item_id,
  order_id,
  customer_id,
  product_id,
  data_pedido,
  quantidade,
  preco_unitario,
  desconto_item,
  receita_item,
  custo_item,
  margem_item,
  flag_item_valido,
  data_processamento
FROM itens_enriquecidos;
