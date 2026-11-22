
-- CAMADA REFINED — DIMENSÃO PRODUTOS
-- TABELA: dim_produtos
-- DESCRIÇÃO: Dimensão de produtos com chave substituta (SK), catálogo, categorização e cálculo de margem unitária

CREATE OR REPLACE TABLE `veloja-ecommerce-medalhao.refined.dim_produtos` AS
SELECT
  TO_HEX(MD5(product_id)) AS product_sk,
  product_id,
  sku,
  nome_produto,
  categoria,
  subcategoria,
  marca,
  preco_tabela,
  custo_unitario,
  (preco_tabela - custo_unitario) AS margem_unitaria,
  ativo,
  CURRENT_TIMESTAMP() AS data_processamento
FROM `veloja-ecommerce-medalhao.trusted.produtos`;