
-- CAMADA TRUSTED — ITENS_PEDIDO


CREATE OR REPLACE TABLE `veloja-ecommerce-medalhao.trusted.itens_pedido` AS

-- 1. Limpeza 
WITH limpeza_padronizacao AS (
  SELECT
    TRIM(order_item_id) AS order_item_id,
    TRIM(order_id) AS order_id,
    TRIM(product_id) AS product_id,
    TRIM(quantidade) AS quantidade,
    REGEXP_REPLACE( REPLACE(TRIM(preco_unitario), '\u00A0', ''), r'[^0-9,.]', '' ) AS preco_unitario,
    REGEXP_REPLACE( REPLACE(TRIM(desconto_item), '\u00A0', ''), r'[^0-9,.]', '' ) AS desconto_item,

    -- Padroniza status
    CASE 
      WHEN status_item IS NULL OR TRIM(status_item) = '' OR UPPER(TRIM(status_item)) = 'NULL' THEN 'nao_informado'
      ELSE LOWER(TRIM(status_item))
    END AS status_item,

    CURRENT_TIMESTAMP() AS data_processamento

  FROM `veloja-ecommerce-medalhao.raw.itens_pedido`
),

-- 2. Conversão e tipagem
tipificacao AS (
  SELECT
    order_item_id,
    order_id,
    product_id,

    -- INT64
    SAFE_CAST(quantidade AS INT64) AS quantidade,

    -- NUMERIC
    SAFE_CAST(REPLACE(preco_unitario, ',', '.') AS NUMERIC) AS preco_unitario,

    COALESCE(
      SAFE_CAST(REPLACE(desconto_item, ',', '.') AS NUMERIC),
      0.00
    ) AS desconto_item,
    status_item,
    data_processamento

  FROM limpeza_padronizacao
),

-- 3. Deduplicação
deduplicacao AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY order_item_id
      ORDER BY status_item DESC NULLS LAST
    ) AS rnk
  FROM tipificacao
)
SELECT
  order_item_id,
  order_id,
  product_id,
  quantidade,
  preco_unitario,
  desconto_item,
  status_item,
  data_processamento
FROM deduplicacao
WHERE rnk = 1;
