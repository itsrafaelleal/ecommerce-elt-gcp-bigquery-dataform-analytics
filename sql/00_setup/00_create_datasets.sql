
CREATE OR REPLACE TABLE `veloja-ecommerce-medalhao.trusted.clientes` AS

WITH limpeza_padronizacao AS (

  SELECT
    customer_id,
    TRIM(LOWER(nome)) AS nome,
    TRIM(LOWER(email)) AS email,
    cpf_hash,
    TRIM(data_cadastro) AS data_cadastro,

    UPPER(TRIM(estado)) AS estado,
    REPLACE(UPPER(TRIM(pais)), 'BRASIL', 'BR') AS pais,

    REPLACE(
      TRIM(LOWER(canal_aquisicao)),
      'paid search',
      'paid_search'
    ) AS canal_aquisicao,

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

    estado,
    pais,
    canal_aquisicao,

    -- BOOL
    CASE
      WHEN ativo IN ('true', '1', 'sim') THEN TRUE
      WHEN ativo IN ('false', '0', 'nao') THEN FALSE
      ELSE NULL
    END AS ativo,

    -- INT64
    CASE
      WHEN SAFE_CAST(idade AS INT64) BETWEEN 0 AND 100
        THEN SAFE_CAST(idade AS INT64)
      ELSE NULL
    END AS idade,

    -- NUMERIC
    SAFE_CAST(
      REPLACE(renda_estimada, ',', '.') AS NUMERIC
    ) AS renda_estimada,

    -- TIMESTAMP
    COALESCE(
      SAFE_CAST(
        SAFE.PARSE_DATETIME('%d/%m/%Y %H:%M', ultima_atualizacao)
        AS TIMESTAMP
      ),
      SAFE_CAST(
        SAFE.PARSE_DATETIME('%Y-%m-%dT%H:%M:%S', ultima_atualizacao)
        AS TIMESTAMP
      )
    ) AS ultima_atualizacao

  FROM limpeza_padronizacao

)

SELECT
  *,
  CURRENT_TIMESTAMP() AS data_processamento
FROM tipificacao;
