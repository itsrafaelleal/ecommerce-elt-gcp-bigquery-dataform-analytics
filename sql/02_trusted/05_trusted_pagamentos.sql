
-- CAMADA TRUSTED — PAGAMENTOS

CREATE OR REPLACE TABLE `veloja-ecommerce-medalhao.trusted.pagamentos` AS

-- 1. Limpeza
WITH limpeza_padronizacao AS (
  SELECT
    TRIM(payment_id) AS payment_id,
    TRIM(order_id) AS order_id,
    TRIM(data_pagamento) AS data_pagamento,

    -- Padroniza os métodos de pagamento conhecidos
    CASE 
      WHEN metodo_pagamento IS NULL OR TRIM(metodo_pagamento) = '' THEN 'nao_informado'
      WHEN UPPER(TRIM(metodo_pagamento)) IN ('CARTAO', 'CARTAO_CREDITO') THEN 'cartao_credito'
      WHEN UPPER(TRIM(metodo_pagamento)) = 'PIX' THEN 'pix'
      WHEN LOWER(TRIM(metodo_pagamento)) = 'boleto' THEN 'boleto'
      WHEN LOWER(TRIM(metodo_pagamento)) = 'wallet' THEN 'wallet'
      ELSE LOWER(TRIM(metodo_pagamento))
    END AS metodo_pagamento,

    -- Padroniza status do pagamento em minúsculo
    CASE 
      WHEN status_pagamento IS NULL OR TRIM(status_pagamento) = '' OR UPPER(TRIM(status_pagamento)) = 'NULL' THEN 'nao_informado'
      ELSE LOWER(TRIM(status_pagamento))
    END AS status_pagamento,

    REGEXP_REPLACE( REPLACE(TRIM(valor_pago), '\u00A0', ''), r'[^0-9,.]', '' ) AS valor_pago,
    TRIM(parcelas) AS parcelas,
    
    -- Padroniza adquirente
    CASE 
      WHEN adquirente IS NULL OR TRIM(adquirente) = '' OR UPPER(TRIM(adquirente)) = 'NULL' THEN 'nao_informado'
      ELSE TRIM(adquirente)
    END AS adquirente,

    -- Padroniza codigo_autorizacao
    CASE 
      WHEN codigo_autorizacao IS NULL OR TRIM(codigo_autorizacao) = '' OR UPPER(TRIM(codigo_autorizacao)) = 'NULL' THEN NULL
      ELSE UPPER(TRIM(codigo_autorizacao))
    END AS codigo_autorizacao,

    CURRENT_TIMESTAMP() AS data_processamento

  FROM `veloja-ecommerce-medalhao.raw.pagamentos`
),

-- 2. Conversão e tipagem
tipificacao AS (
  SELECT
    payment_id,
    order_id,

    -- TIMESTAMP:
    COALESCE(
      SAFE.PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', data_pagamento),
      SAFE.PARSE_TIMESTAMP('%d/%m/%Y %H:%M', data_pagamento),
      SAFE.PARSE_TIMESTAMP('%Y/%m/%d %H:%M', data_pagamento),
      SAFE.PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S', data_pagamento),
      SAFE.PARSE_TIMESTAMP('%Y-%m-%d', data_pagamento)
    ) AS data_pagamento,

    metodo_pagamento,
    status_pagamento,

    -- NUMERIC
    SAFE_CAST(REPLACE(valor_pago, ',', '.') AS NUMERIC) AS valor_pago,

    -- INT64
    SAFE_CAST(parcelas AS INT64) AS parcelas,

    adquirente,
    codigo_autorizacao,
    data_processamento

  FROM limpeza_padronizacao
),

-- 3. Deduplicação
deduplicacao AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY payment_id
      ORDER BY data_pagamento DESC NULLS LAST
    ) AS rnk
  FROM tipificacao
)

-- Resultado final limpo, tipado e deduplicado
SELECT
  payment_id,
  order_id,
  data_pagamento,
  metodo_pagamento,
  status_pagamento,
  valor_pago,
  parcelas,
  adquirente,
  codigo_autorizacao,
  data_processamento
FROM deduplicacao
WHERE rnk = 1;
