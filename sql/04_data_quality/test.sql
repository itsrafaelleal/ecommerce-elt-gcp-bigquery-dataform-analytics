-- CAMADA: DATA QUALITY & AUDITORIA PÓS-REFINED
-- OBJETIVO: Bateria de testes automatizados de qualidade, integridade e consistência contábil
-- MÉTODO: Cada teste busca anomalias. 0 erros = PASSOU. >0 erros = FALHOU.

WITH testes AS (


  -- 1. UNICIDADE E NÃO-NULOS (CHAVES PRIMÁRIAS / SURROGATE KEYS)


  -- Teste 1.1: A chave substituta customer_sk na dim_clientes é única e nunca é nula?
  SELECT
    'pk_unica_dim_clientes' AS nome_teste,
    'dim_clientes' AS tabela_avaliada,
    'Chave customer_sk deve ser unica e nao nula' AS descricao_regra,
    (COUNT(*) - COUNT(DISTINCT customer_sk)) + COUNTIF(customer_sk IS NULL) AS linhas_com_erro
  FROM `veloja-ecommerce-medalhao.refined.dim_clientes`

  UNION ALL

  -- Teste 1.2: A chave substituta product_sk na dim_produtos é única e nunca é nula?
  SELECT
    'pk_unica_dim_produtos',
    'dim_produtos',
    'Chave product_sk deve ser unica e nao nula',
    (COUNT(*) - COUNT(DISTINCT product_sk)) + COUNTIF(product_sk IS NULL)
  FROM `veloja-ecommerce-medalhao.refined.dim_produtos`

  UNION ALL

  -- Teste 1.3: A chave order_id na fact_pedidos é única e nunca é nula?
  SELECT
    'pk_unica_fact_pedidos',
    'fact_pedidos',
    'Chave order_id deve ser unica e nao nula',
    (COUNT(*) - COUNT(DISTINCT order_id)) + COUNTIF(order_id IS NULL)
  FROM `veloja-ecommerce-medalhao.refined.fact_pedidos`

  UNION ALL

  -- Teste 1.4: A chave order_item_id na fact_itens_pedido é única e nunca é nula?
  SELECT
    'pk_unica_fact_itens_pedido',
    'fact_itens_pedido',
    'Chave order_item_id deve ser unica e nao nula',
    (COUNT(*) - COUNT(DISTINCT order_item_id)) + COUNTIF(order_item_id IS NULL)
  FROM `veloja-ecommerce-medalhao.refined.fact_itens_pedido`

  UNION ALL

  -- Teste 1.5: Cada dia (data_pedido) aparece no máximo 1 vez no mart_vendas_diarias?
  SELECT
    'pk_unica_mart_vendas_diarias',
    'mart_vendas_diarias',
    'Data de pedido deve ser unica por dia no mart',
    (COUNT(*) - COUNT(DISTINCT data_pedido)) + COUNTIF(data_pedido IS NULL)
  FROM `veloja-ecommerce-medalhao.refined.mart_vendas_diarias`

  UNION ALL

  -- Teste 1.6: A combinação de campanha e canal é única no mart_performance_campanhas?
  SELECT
    'pk_unica_mart_performance_campanhas',
    'mart_performance_campanhas',
    'A combinacao campanha + canal deve ser unica',
    (COUNT(*) - COUNT(DISTINCT CONCAT(campanha, '_', canal))) AS linhas_com_erro
  FROM `veloja-ecommerce-medalhao.refined.mart_performance_campanhas`

  UNION ALL


  -- 2. CONSISTÊNCIA MATEMÁTICA E RECONCILIAÇÃO FINANCEIRA


  -- Teste 2.1: Em fact_pedidos, o valor_receita_liquida é exatamente igual a valor_itens_bruto - valor_desconto?
  SELECT
    'consistencia_receita_liquida',
    'fact_pedidos',
    'valor_receita_liquida deve ser exatamente igual a valor_itens_bruto - valor_desconto',
    COUNTIF(ABS(valor_receita_liquida - (valor_itens_bruto - valor_desconto)) > 0.01)
  FROM `veloja-ecommerce-medalhao.refined.fact_pedidos`

  UNION ALL

  -- Teste 2.2: Em fact_itens_pedido, a margem_item é exatamente igual a receita_item - custo_item?
  SELECT
    'consistencia_margem_itens',
    'fact_itens_pedido',
    'margem_item deve ser exatamente igual a receita_item - custo_item',
    COUNTIF(ABS(margem_item - (receita_item - custo_item)) > 0.01)
  FROM `veloja-ecommerce-medalhao.refined.fact_itens_pedido`

  UNION ALL

  -- Teste 2.3: Em mart_vendas_diarias, o ticket_medio é exatamente igual a receita_liquida / pedidos?
  SELECT
    'consistencia_ticket_medio_mart',
    'mart_vendas_diarias',
    'ticket_medio deve ser igual a receita_liquida / pedidos (arredondado a 2 casas)',
    COUNTIF(ABS(ticket_medio - ROUND(SAFE_DIVIDE(receita_liquida, pedidos), 2)) > 0.02)
  FROM `veloja-ecommerce-medalhao.refined.mart_vendas_diarias`

  UNION ALL


  -- 3. REGRAS DE NEGÓCIO E DOMÍNIO (FLAGS DE VALIDADE)


  -- Teste 3.1: Em fact_pedidos, existe algum pedido com flag_pedido_valido = TRUE que seja cancelado/devolvido ou com valor_pago_aprovado <= 0?
  SELECT
    'regra_flag_pedido_valido',
    'fact_pedidos',
    'Pedidos com flag_pedido_valido=TRUE nao podem ser cancelados/devolvidos e devem ter valor aprovado > 0',
    COUNTIF(flag_pedido_valido = TRUE AND (status_pedido IN ('cancelado', 'devolvido', 'falha_pagamento') OR valor_pago_aprovado <= 0))
  FROM `veloja-ecommerce-medalhao.refined.fact_pedidos`

  UNION ALL

  -- Teste 3.2: Em fact_itens_pedido, existe algum item com flag_item_valido = TRUE com quantidade <= 0 ou preco_unitario <= 0?
  SELECT
    'regra_flag_item_valido',
    'fact_itens_pedido',
    'Itens com flag_item_valido=TRUE devem ter quantidade > 0 e preco_unitario > 0',
    COUNTIF(flag_item_valido = TRUE AND (quantidade <= 0 OR preco_unitario <= 0))
  FROM `veloja-ecommerce-medalhao.refined.fact_itens_pedido`

  UNION ALL

  -- Teste 3.3: Em dim_clientes, existe alguma faixa_idade ou faixa_renda nula ou com valor fora do padrão esperado?
  SELECT
    'dominio_faixas_clientes',
    'dim_clientes',
    'faixa_idade e faixa_renda nao podem ser nulas nem conter valores fora do padrao',
    COUNTIF(
      faixa_idade NOT IN ('18-24', '25-34', '35-49', '50-64', '65+', 'nao_informado')
      OR faixa_renda NOT IN ('Ate R$ 3.000', 'R$ 3.001 a R$ 7.000', 'R$ 7.001 a R$ 12.000', 'Acima de R$ 12.000', 'nao_informado')
    )
  FROM `veloja-ecommerce-medalhao.refined.dim_clientes`

  UNION ALL


  -- 4. RECONCILIAÇÃO CONTÁBIL (FATO VS. DATA MART)


  -- Teste 4.1: A soma da receita_liquida no mart_vendas_diarias é rigorosamente igual à soma de valor_receita_liquida dos pedidos válidos na fact_pedidos?
  SELECT
    'reconciliacao_fato_vs_mart',
    'mart_vendas_diarias',
    'Receita liquida acumulada no mart deve bater exatamente com os pedidos validos da fato',
    (
      SELECT CASE 
        WHEN ABS(SUM(m.receita_liquida) - (SELECT SUM(valor_receita_liquida) FROM `veloja-ecommerce-medalhao.refined.fact_pedidos` WHERE flag_pedido_valido = TRUE)) > 0.01 THEN 1 
        ELSE 0 
      END
      FROM `veloja-ecommerce-medalhao.refined.mart_vendas_diarias` m
    )

  UNION ALL


  -- 5. INTEGRIDADE REFERENCIAL (DETECÇÃO DE ÓRFÃOS)


  -- Teste 5.1: Existem pedidos válidos na fact_pedidos cujo customer_id não existe na dim_clientes (pedidos órfãos)?
  SELECT
    'orfaos_pedidos_sem_cliente',
    'fact_pedidos',
    'Pedidos validos cujo customer_id nao existe na dimensao de clientes',
    COUNTIF(c.customer_id IS NULL AND p.flag_pedido_valido = TRUE)
  FROM `veloja-ecommerce-medalhao.refined.fact_pedidos` p
  LEFT JOIN `veloja-ecommerce-medalhao.refined.dim_clientes` c
    ON p.customer_id = c.customer_id

  UNION ALL

  -- Teste 5.2: Existem itens válidos na fact_itens_pedido cujo product_id não existe na dim_produtos (itens órfãos)?
  SELECT
    'orfaos_itens_sem_produto',
    'fact_itens_pedido',
    'Itens validos cujo product_id nao existe na dimensao de produtos',
    COUNTIF(pr.product_id IS NULL AND i.flag_item_valido = TRUE)
  FROM `veloja-ecommerce-medalhao.refined.fact_itens_pedido` i
  LEFT JOIN `veloja-ecommerce-medalhao.refined.dim_produtos` pr
    ON i.product_id = pr.product_id

  UNION ALL

  -- ===========================================================================
  -- 6. GOVERNANÇA E CONSISTÊNCIA DA CAMADA DE METAS
  -- ===========================================================================

  -- Teste 6.1: Cada dia do ano (365 dias) possui uma única meta diária e não nula em dim_metas?
  SELECT
    'pk_unica_dim_metas',
    'dim_metas',
    'A tabela dim_metas deve ter 365 dias unicos e sem chaves nulas',
    ABS(COUNT(*) - 365) + (COUNT(*) - COUNT(DISTINCT data_referencia)) + COUNTIF(meta_dia_sk IS NULL)
  FROM `veloja-ecommerce-medalhao.refined.dim_metas`

  UNION ALL

  -- Teste 6.2: A soma das metas diárias de receita em dim_metas bate com a soma do orçamento mensal Top-Down?
  SELECT
    'reconciliacao_meta_diaria_vs_mensal',
    'dim_metas',
    'A soma das metas diarias desdobradas deve bater com o orcamento anual (diferenca < R$ 1,00)',
    (
      SELECT CASE
        WHEN ABS(SUM(meta_diaria_receita) - (SELECT SUM(meta_receita_liquida) FROM `veloja-ecommerce-medalhao.trusted.metas_orcamento`)) > 1.00 THEN 1
        ELSE 0
      END
      FROM `veloja-ecommerce-medalhao.refined.dim_metas`
    )

  UNION ALL

  -- Teste 6.3: Todos os status de semáforo em mart_metas_vs_realizado pertencem ao domínio válido (VERDE_ESCURO, VERDE_CLARO, AMARELO, VERMELHO)?
  SELECT
    'dominio_semaforo_metas',
    'mart_metas_vs_realizado',
    'Colunas de status devem conter apenas VERDE_ESCURO, VERDE_CLARO, AMARELO ou VERMELHO',
    COUNTIF(
      status_receita NOT IN ('VERDE_ESCURO', 'VERDE_CLARO', 'AMARELO', 'VERMELHO')
      OR status_pedidos NOT IN ('VERDE_ESCURO', 'VERDE_CLARO', 'AMARELO', 'VERMELHO')
      OR status_ticket NOT IN ('VERDE_ESCURO', 'VERDE_CLARO', 'AMARELO', 'VERMELHO')
      OR status_margem NOT IN ('VERDE_ESCURO', 'VERDE_CLARO', 'AMARELO', 'VERMELHO')
      OR status_desconto NOT IN ('VERDE_ESCURO', 'VERDE_CLARO', 'AMARELO', 'VERMELHO')
    )
  FROM `veloja-ecommerce-medalhao.refined.mart_metas_vs_realizado`
)

-- RELATÓRIO CONSOLIDADO DE EXECUÇÃO
SELECT
  nome_teste,
  tabela_avaliada,
  linhas_com_erro,
  CASE
    WHEN linhas_com_erro = 0 THEN ' PASSOU'
    ELSE ' FALHOU'
  END AS status_teste,
  descricao_regra
FROM testes
ORDER BY 
  CASE WHEN linhas_com_erro > 0 THEN 1 ELSE 2 END, 
  tabela_avaliada,
  nome_teste;
