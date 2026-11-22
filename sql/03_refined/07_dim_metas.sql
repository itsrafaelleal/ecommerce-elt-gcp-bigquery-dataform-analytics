-- CAMADA REFINED — DIMENSÃO DE METAS (dim_metas)
-- TABELA: dim_metas
-- DESCRIÇÃO: Desdobra o orçamento mensal Top-Down para os 365 dias do ano ponderando pelo peso sazonal do dia da semana

CREATE OR REPLACE TABLE `veloja-ecommerce-medalhao.refined.dim_metas` AS
WITH calendario_2025 AS (
  SELECT
    dia AS data_referencia,
    FORMAT_DATE('%Y-%m', dia) AS ano_mes,
    EXTRACT(DAYOFWEEK FROM dia) AS num_dia_semana,
    FORMAT_DATE('%A', dia) AS nome_dia_semana,
    -- Pesos padrão de varejo e-commerce por dia da semana (1=Dom, 2=Seg, 3=Ter, 4=Qua, 5=Qui, 6=Sex, 7=Sáb)
    CASE EXTRACT(DAYOFWEEK FROM dia)
      WHEN 1 THEN 0.68  -- Domingo
      WHEN 2 THEN 1.18  -- Segunda
      WHEN 3 THEN 1.22  -- Terça
      WHEN 4 THEN 1.15  -- Quarta
      WHEN 5 THEN 1.08  -- Quinta
      WHEN 6 THEN 0.97  -- Sexta
      WHEN 7 THEN 0.72  -- Sábado
    END AS peso_dia_semana
  FROM UNNEST(GENERATE_DATE_ARRAY('2025-01-01', '2025-12-31', INTERVAL 1 DAY)) AS dia
),

pesos_mensais AS (
  SELECT
    c.*,
    SUM(peso_dia_semana) OVER (PARTITION BY ano_mes) AS soma_pesos_mes,
    peso_dia_semana / SUM(peso_dia_semana) OVER (PARTITION BY ano_mes) AS fator_participacao_dia
  FROM calendario_2025 c
)

SELECT
  TO_HEX(MD5(CAST(p.data_referencia AS STRING))) AS meta_dia_sk,
  p.data_referencia,
  p.ano_mes,
  p.num_dia_semana,
  p.nome_dia_semana,
  ROUND(CAST(p.fator_participacao_dia AS NUMERIC), 6) AS fator_participacao_dia,

  -- Metas Mensais Originais (para referência de contexto)
  m.meta_receita_liquida AS meta_mensal_receita,
  m.meta_pedidos AS meta_mensal_pedidos,

  -- Metas Diárias Desdobradas (somáveis: a soma dos dias do mês = meta mensal)
  CAST(ROUND(m.meta_receita_liquida * p.fator_participacao_dia, 2) AS NUMERIC) AS meta_diaria_receita,
  CAST(ROUND(m.meta_pedidos * p.fator_participacao_dia, 0) AS INT64) AS meta_diaria_pedidos,

  -- Metas de Razão (não somáveis: o alvo de eficiência vale para dia, mês e ano)
  m.meta_ticket_medio,
  m.meta_margem_pct,
  m.teto_desconto_pct,
  m.meta_roas,

  -- Limiares de Semáforo e Governança
  m.limiar_verde_pct,
  m.limiar_amarelo_pct,
  m.origem_meta,
  CURRENT_TIMESTAMP() AS data_processamento

FROM pesos_mensais p
INNER JOIN `veloja-ecommerce-medalhao.trusted.metas_orcamento` m
  ON p.ano_mes = m.ano_mes
ORDER BY p.data_referencia;
