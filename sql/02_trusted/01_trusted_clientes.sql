
-- CAMADA TRUSTED — CLIENTES

CREATE OR REPLACE TABLE `veloja-ecommerce-medalhao.trusted.clientes` AS

WITH limpeza_padronizacao AS (
  SELECT
    TRIM(customer_id) AS customer_id,
    TRIM(LOWER(nome)) AS nome,
    TRIM(LOWER(email)) AS email,
    TRIM(cpf_hash) AS cpf_hash,
    TRIM(data_cadastro) AS data_cadastro,
    TRIM(cidade) AS cidade,
    UPPER(TRIM(estado)) AS estado,
    REPLACE(UPPER(TRIM(pais)), 'BRASIL', 'BR') AS pais,
    
    -- Normaliza 
    CASE 
      WHEN canal_aquisicao IS NULL OR TRIM(canal_aquisicao) = '' THEN 'nao_informado'
      ELSE REPLACE(TRIM(LOWER(canal_aquisicao)), 'paid search', 'paid_search')
    END AS canal_aquisicao,
    
    LOWER(TRIM(ativo)) AS ativo,
    TRIM(idade) AS idade,
    
    REGEXP_REPLACE(
      REPLACE(TRIM(renda_estimada), '\u00A0', ''), 
      r'[^0-9,.-]', 
      ''
    ) AS renda_estimada,
    
    TRIM(ultima_atualizacao) AS ultima_atualizacao

  FROM `veloja-ecommerce-medalhao.raw.clientes`
),

tipificacao AS (
  SELECT
    customer_id,
    nome,
    email,
    cpf_hash,

    -- DATE
    COALESCE(
      SAFE.PARSE_DATE('%d/%m/%Y', data_cadastro),
      SAFE.PARSE_DATE('%Y-%m-%d', data_cadastro),
      SAFE.PARSE_DATE('%Y/%m/%d', data_cadastro)
    ) AS data_cadastro,

    cidade,
    estado,
    pais,
    canal_aquisicao,

    -- BOOL
    CASE
      WHEN ativo IN ('true', '1', 'sim', 's') THEN TRUE
      WHEN ativo IN ('false', '0', 'nao', 'não', 'n') THEN FALSE
      ELSE FALSE
    END AS ativo,

    -- INT
    CASE
      WHEN SAFE_CAST(idade AS INT64) BETWEEN 0 AND 120
        THEN SAFE_CAST(idade AS INT64)
      ELSE NULL
    END AS idade,

    --  NUMERIC
    SAFE_CAST(REPLACE(renda_estimada, ',', '.') AS NUMERIC) AS renda_estimada,

    -- TIME
    COALESCE(
      SAFE.PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', ultima_atualizacao),
      SAFE.PARSE_TIMESTAMP('%Y/%m/%d %H:%M', ultima_atualizacao),
      SAFE.PARSE_TIMESTAMP('%d/%m/%Y %H:%M', ultima_atualizacao),
      SAFE.PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S', ultima_atualizacao)
    ) AS ultima_atualizacao

  FROM limpeza_padronizacao
),

deduplicado AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY customer_id
      ORDER BY ultima_atualizacao DESC NULLS LAST
    ) AS rnk
  FROM tipificacao
)

SELECT
  customer_id,
  nome,
  email,
  cpf_hash,
  data_cadastro,
  cidade,
  estado,
  pais,
  canal_aquisicao,
  ativo,
  idade,
  renda_estimada,
  ultima_atualizacao,
  CURRENT_TIMESTAMP() AS data_processamento
FROM deduplicado
WHERE rnk = 1;
