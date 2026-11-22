
-- CAMADA TRUSTED — PEDIDOS

CREATE OR REPLACE TABLE `veloja-ecommerce-medalhao.trusted.pedidos` AS

-- 1. Limpeza inicial e padronização textual
WITH limpeza_padronizacao AS (
  SELECT
    TRIM(order_id) AS order_id,
    TRIM(customer_id) AS customer_id,
    TRIM(data_pedido) AS data_pedido,
    
    -- Padroniza status
    CASE
      WHEN status_pedido IS NULL OR TRIM(status_pedido) = '' THEN 'nao_informado'
      ELSE REPLACE(TRIM(LOWER(status_pedido)), ' ', '_')
    END AS status_pedido,

    -- Padroniza canais
    CASE 
      WHEN origem_pedido IS NULL OR TRIM(origem_pedido) = '' THEN 'nao_informado'
      ELSE LOWER(TRIM(origem_pedido))
    END AS origem_pedido,

    -- Padroniza cupom
    CASE 
      WHEN cupom IS NULL OR TRIM(cupom) = '' OR UPPER(TRIM(cupom)) = 'NULL' THEN NULL
      ELSE UPPER(TRIM(cupom))
    END AS cupom,

    REGEXP_REPLACE(REPLACE(TRIM(frete), '\u00A0', ''),r'[^0-9,.]','') AS frete,
    TRIM(cidade_entrega) AS cidade_entrega,
    UPPER(TRIM(estado_entrega)) AS estado_entrega,
    TRIM(observacao) AS observacao,
    CURRENT_TIMESTAMP() AS data_processamento

  FROM `veloja-ecommerce-medalhao.raw.pedidos`
),

-- 2. Conversão e tipagem dos dados
tipificacao AS (
  SELECT
    order_id,
    customer_id,

    -- TIMESTAMP
    COALESCE(
      SAFE.PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', data_pedido),
      SAFE.PARSE_TIMESTAMP('%d/%m/%Y %H:%M', data_pedido),
      SAFE.PARSE_TIMESTAMP('%Y/%m/%d %H:%M', data_pedido),
      SAFE.PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S', data_pedido),
      SAFE.PARSE_TIMESTAMP('%Y-%m-%d', data_pedido)
    ) AS data_pedido,

    status_pedido,
    origem_pedido,
    cupom,

    -- NUMERIC
    COALESCE(
      SAFE_CAST(REPLACE(frete, ',', '.') AS NUMERIC),
      0.00
    ) AS frete,

    cidade_entrega,
    estado_entrega,
    observacao,
    data_processamento

  FROM limpeza_padronizacao
),

-- 3. Deduplicação
deduplicacao AS (
  SELECT*,
    ROW_NUMBER() OVER (
      PARTITION BY order_id
      ORDER BY 
        CASE WHEN LOWER(observacao) LIKE '%duplicidade%' THEN 2 ELSE 1 END,
        data_pedido DESC NULLS LAST
    ) AS rnk
  FROM tipificacao
)


SELECT
  order_id,
  customer_id,
  data_pedido,
  status_pedido,
  origem_pedido,
  cupom,
  frete,
  cidade_entrega,
  estado_entrega,
  observacao,
  data_processamento
FROM deduplicacao
WHERE rnk = 1;
