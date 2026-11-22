
-- CAMADA TRUSTED — EVENTOS_MARKETING


CREATE OR REPLACE TABLE `veloja-ecommerce-medalhao.trusted.eventos_marketing` AS

-- 1. Limpeza inicial
WITH limpeza_padronizacao AS (
  SELECT
    TRIM(event_id) AS event_id,
    
    -- customer_id pode ser nulo em eventos anônimos
    CASE 
      WHEN customer_id IS NULL OR TRIM(customer_id) = '' OR UPPER(TRIM(customer_id)) = 'NULL' THEN NULL
      ELSE TRIM(customer_id)
    END AS customer_id,

    TRIM(data_evento) AS data_evento,

    -- Mapeamento direto: o RAW agora tem os nomes corretos com o significado certo.
    CASE 
      WHEN campanha IS NULL OR TRIM(campanha) = '' OR UPPER(TRIM(campanha)) = 'NULL' THEN 'nao_informado'
      ELSE LOWER(TRIM(campanha))
    END AS campanha,

    CASE 
      WHEN canal IS NULL OR TRIM(canal) = '' OR UPPER(TRIM(canal)) = 'NULL' THEN 'nao_informado'
      ELSE LOWER(TRIM(canal))
    END AS canal,

    CASE 
      WHEN tipo_evento IS NULL OR TRIM(tipo_evento) = '' THEN 'nao_informado'
      ELSE LOWER(TRIM(tipo_evento))
    END AS tipo_evento,

    REGEXP_REPLACE( REPLACE(TRIM(custo_campanha), '\u00A0', ''), r'[^0-9,.]', '' ) AS custo_campanha,

    CASE 
      WHEN device IS NULL OR TRIM(device) = '' OR UPPER(TRIM(device)) = 'NULL' THEN 'nao_informado'
      ELSE LOWER(TRIM(device))
    END AS device,

    CURRENT_TIMESTAMP() AS data_processamento

  FROM `veloja-ecommerce-medalhao.raw.eventos_marketing`
),

-- 2. Conversão e tipagem 
tipificacao AS (
  SELECT
    event_id,
    customer_id,

    -- TIMESTAMP
    COALESCE(
      SAFE.PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', data_evento),
      SAFE.PARSE_TIMESTAMP('%d/%m/%Y %H:%M', data_evento),
      SAFE.PARSE_TIMESTAMP('%Y/%m/%d %H:%M', data_evento),
      SAFE.PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S', data_evento),
      SAFE.PARSE_TIMESTAMP('%Y-%m-%d', data_evento)
    ) AS data_evento,

    campanha,
    canal,
    tipo_evento,

    -- NUMERIC
    COALESCE(
      SAFE_CAST(REPLACE(custo_campanha, ',', '.') AS NUMERIC),
      0.00
    ) AS custo_campanha,

    device,
    data_processamento

  FROM limpeza_padronizacao
),

-- 3. Dedup
deduplicacao AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY event_id
      ORDER BY data_evento DESC NULLS LAST
    ) AS rnk
  FROM tipificacao
)

SELECT
  event_id,
  customer_id,
  data_evento,
  campanha,
  canal,
  tipo_evento,
  custo_campanha,
  device,
  data_processamento
FROM deduplicacao
WHERE rnk = 1;
