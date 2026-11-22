-- 1. CLIENTES
CREATE OR REPLACE EXTERNAL TABLE `veloja-ecommerce-medalhao.raw.clientes` (
  customer_id STRING,
  nome STRING,
  email STRING,
  cpf_hash STRING,
  data_cadastro STRING,
  cidade STRING,
  estado STRING,
  pais STRING,
  canal_aquisicao STRING,
  ativo STRING,
  idade STRING,
  renda_estimada STRING,
  ultima_atualizacao STRING
)
OPTIONS (
  format = 'CSV',
  uris = ['gs://veloja-ecommerce-medalhao-raw/raw/ecommerce/20261119/clientes.csv'],
  skip_leading_rows = 1,
  field_delimiter = ',',
  allow_quoted_newlines = TRUE
);

-- 2. PRODUTOS
CREATE OR REPLACE EXTERNAL TABLE `veloja-ecommerce-medalhao.raw.produtos` (
  product_id STRING,
  sku STRING,
  nome_produto STRING,
  categoria STRING,
  subcategoria STRING,
  marca STRING,
  preco_tabela STRING,
  custo_unitario STRING,
  ativo STRING,
  data_inicio_venda STRING,
  peso_kg STRING
)
OPTIONS (
  format = 'CSV',
  uris = ['gs://veloja-ecommerce-medalhao-raw/raw/ecommerce/20261119/produtos.csv'],
  skip_leading_rows = 1,
  field_delimiter = ',',
  allow_quoted_newlines = TRUE
);

-- 3. PEDIDOS
CREATE OR REPLACE EXTERNAL TABLE `veloja-ecommerce-medalhao.raw.pedidos` (
  order_id STRING,
  customer_id STRING,
  data_pedido STRING,
  status_pedido STRING,
  origem_pedido STRING,
  cupom STRING,
  frete STRING,
  cidade_entrega STRING,
  estado_entrega STRING,
  observacao STRING
)
OPTIONS (
  format = 'CSV',
  uris = ['gs://veloja-ecommerce-medalhao-raw/raw/ecommerce/20261119/pedidos.csv'],
  skip_leading_rows = 1,
  field_delimiter = ',',
  allow_quoted_newlines = TRUE
);

-- 4. ITENS_PEDIDO
CREATE OR REPLACE EXTERNAL TABLE `veloja-ecommerce-medalhao.raw.itens_pedido` (
  order_item_id STRING,
  order_id STRING,
  product_id STRING,
  quantidade STRING,
  preco_unitario STRING,
  desconto_item STRING,
  status_item STRING
)
OPTIONS (
  format = 'CSV',
  uris = ['gs://veloja-ecommerce-medalhao-raw/raw/ecommerce/20261119/itens_pedido.csv'],
  skip_leading_rows = 1,
  field_delimiter = ',',
  allow_quoted_newlines = TRUE
);

-- 5. PAGAMENTOS
CREATE OR REPLACE EXTERNAL TABLE `veloja-ecommerce-medalhao.raw.pagamentos` (
  payment_id STRING,
  order_id STRING,
  data_pagamento STRING,
  metodo_pagamento STRING,
  status_pagamento STRING,
  valor_pago STRING,
  parcelas STRING,
  adquirente STRING,
  codigo_autorizacao STRING
)
OPTIONS (
  format = 'CSV',
  uris = ['gs://veloja-ecommerce-medalhao-raw/raw/ecommerce/20261119/pagamentos.csv'],
  skip_leading_rows = 1,
  field_delimiter = ',',
  allow_quoted_newlines = TRUE
);

-- 6. EVENTOS_MARKETING
CREATE OR REPLACE EXTERNAL TABLE `veloja-ecommerce-medalhao.raw.eventos_marketing` (
  event_id STRING,
  customer_id STRING,
  data_evento STRING,
  campanha STRING,
  canal STRING,
  tipo_evento STRING,
  custo_campanha STRING,
  device STRING
)
OPTIONS (
  format = 'CSV',
  uris = ['gs://veloja-ecommerce-medalhao-raw/raw/ecommerce/20261119/eventos_marketing.csv'],
  skip_leading_rows = 1,
  field_delimiter = ',',
  allow_quoted_newlines = TRUE
);

-- 7. METAS_ORCAMENTO
CREATE OR REPLACE EXTERNAL TABLE `veloja-ecommerce-medalhao.raw.metas_orcamento` (
  meta_id STRING,
  ano_mes STRING,
  meta_receita_liquida STRING,
  meta_pedidos STRING,
  meta_ticket_medio STRING,
  meta_margem_pct STRING,
  teto_desconto_pct STRING,
  meta_roas STRING,
  limiar_verde_pct STRING,
  limiar_amarelo_pct STRING,
  origem_meta STRING
)
OPTIONS (
  format = 'CSV',
  uris = ['gs://veloja-ecommerce-medalhao-raw/raw/ecommerce/20261119/metas_orcamento_2025.csv'],
  skip_leading_rows = 1,
  field_delimiter = ',',
  allow_quoted_newlines = TRUE
);