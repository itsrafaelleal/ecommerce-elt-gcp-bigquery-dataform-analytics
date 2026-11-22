
-- CAMADA REFINED — CLIENTES
-- TABELA: dim_clientes
-- DESCRIÇÃO: Dimensão de clientes com chave substituta (SK) e segmentação analítica por faixas de idade e renda

CREATE OR REPLACE TABLE `veloja-ecommerce-medalhao.refined.dim_clientes` AS

SELECT
  TO_HEX(MD5(customer_id)) AS customer_sk, 
  customer_id,
  nome,
  email,
  cidade,
  estado,
  canal_aquisicao,
  data_cadastro,
  CASE 
    WHEN idade BETWEEN 18 AND 24 THEN '18-24'
    WHEN idade BETWEEN 25 AND 34 THEN '25-34'
    WHEN idade BETWEEN 35 AND 49 THEN '35-49'
    WHEN idade BETWEEN 50 AND 64 THEN '50-64'
    WHEN idade >= 65 THEN '65+'
    ELSE 'nao_informado'
  END AS faixa_idade,
  CASE 
  WHEN renda_estimada <= 3000 THEN 'Ate R$ 3.000'
  WHEN renda_estimada <= 7000 THEN 'R$ 3.001 a R$ 7.000'
  WHEN renda_estimada <= 12000 THEN 'R$ 7.001 a R$ 12.000'
  WHEN renda_estimada > 12000 THEN 'Acima de R$ 12.000'
  ELSE 'nao_informado'
END AS faixa_renda,
  ativo,
  CURRENT_TIMESTAMP() AS data_processamento
FROM `veloja-ecommerce-medalhao.trusted.clientes`

