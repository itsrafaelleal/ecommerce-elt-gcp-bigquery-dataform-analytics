-- -- CAMADA TRUSTED — PRODUTOS


CREATE OR REPLACE TABLE `veloja-ecommerce-medalhao.trusted.produtos` AS

-- limpeza_padronizacao
WITH limpeza_padronizacao AS (
SELECT
  product_id,
  sku,
  TRIM(LOWER(nome_produto)) AS nome_produto,
  TRIM(LOWER(categoria)) AS categoria,
  TRIM(LOWER(subcategoria)) AS subcategoria,
  TRIM(LOWER(marca)) AS marca,
  TRIM(LOWER(preco_tabela)) AS preco_tabela,
  TRIM(LOWER(custo_unitario)) AS custo_unitario,
  TRIM(ativo) AS ativo,
  TRIM(data_inicio_venda) AS data_inicio_venda,
  TRIM(peso_kg) AS peso_kg,
  CURRENT_TIMESTAMP() AS data_processamento
FROM `veloja-ecommerce-medalhao.raw.produtos`),

-- tipificacao

tipificacao AS(
SELECT
  product_id,
  sku,
  nome_produto,
  categoria,
  subcategoria,
  marca,
  
  --  NUMERIC
  SAFE_CAST(REPLACE(REGEXP_REPLACE(preco_tabela, r'[^0-9,.]', ''), ',', '.') AS NUMERIC) AS preco_tabela,
  SAFE_CAST(REPLACE(REGEXP_REPLACE(custo_unitario, r'[^0-9,.]', ''), ',', '.') AS NUMERIC) AS custo_unitario,
  SAFE_CAST(REPLACE(peso_kg, ',', '.') AS NUMERIC) AS peso_kg,
   -- BOOL
  CASE
    WHEN ativo IN ('true', '1', 'sim', 's') THEN TRUE
    WHEN ativo IN ('false', '0', 'nao', 'não', 'n') THEN FALSE
    ELSE FALSE
  END AS ativo,

  -- TIME
  COALESCE(
    SAFE.PARSE_DATE('%Y-%m-%d', data_inicio_venda),
    SAFE.PARSE_DATE('%d/%m/%Y', data_inicio_venda),
    SAFE.PARSE_DATE('%Y/%m/%d', data_inicio_venda)
  ) AS data_inicio_venda,

  data_processamento
  FROM limpeza_padronizacao
),

-- deduplicacao

deduplicacao AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY product_id
      ORDER BY ativo DESC, data_inicio_venda DESC
    ) AS rnk
  FROM tipificacao
)


SELECT
  product_id,
  sku,
  nome_produto,
  categoria,
  subcategoria,
  marca marca,
  preco_tabela,
  custo_unitario,
  ativo,
  data_inicio_venda,
  peso_kg,
  data_processamento
FROM deduplicacao
WHERE rnk = 1;