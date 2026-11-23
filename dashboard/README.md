# Veloja Analytics — Dashboard (GCP + BigQuery + Streamlit + Apache ECharts)

Dashboard executivo de tomada de decisão para a operação de e-commerce da **Veloja**, conectado diretamente às tabelas agregadas da Camada **Refined (Gold)** no Google BigQuery.

---

## Stack Tecnológica

* **Framework Web:** Python 3.10+ & Streamlit
* **Visualizações:** Apache ECharts (`streamlit-echarts`)
* **Data Warehouse:** Google Cloud Storage & Google BigQuery (`southamerica-east1`)
* **Processamento:** Pandas & PyArrow
* **Arquitetura de Dados:** Arquitetura Medalhão (Raw ➔ Trusted ➔ Refined) + Camada de Metas Top-Down (FP&A)

---

## Estrutura da Aplicação

```
dashboard/
├── .streamlit/
│   ├── config.toml              # Tema Dark Mode corporativo limpo
│   └── secrets.toml.example     # Modelo para credenciais de Service Account
├── src/
│   ├── __init__.py
│   ├── data_loader.py           # Conexão BigQuery em produção e cache (1 hora)
│   └── charts.py                # Opções de gráficos interativos do Apache ECharts
├── app.py                       # Interface principal (Layout, Filtros Globais, 4 Visões, Semáforo RAG)
├── requirements.txt             # Dependências com versões fixadas
├── .gitignore                   # Proteção de credenciais e caches
└── README.md                    # Documentação de execução e deploy
```

---

## Como Executar

### 1. Criar e Ativar Ambiente Virtual
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Instalar Dependências
```bash
pip install -r dashboard/requirements.txt
```

### 3. Rodar a Aplicação
```bash
streamlit run dashboard/app.py
```
A aplicação estará disponível em `http://localhost:8501`.

---

## Conexão com o Google BigQuery

A aplicação conecta-se diretamente ao projeto `veloja-ecommerce-medalhao` na região `southamerica-east1`:
* **Ambiente Local / Servidor:** Utiliza Application Default Credentials (`gcloud auth application-default login`) ou variável `GOOGLE_APPLICATION_CREDENTIALS`.
* **Streamlit Cloud / Container:** Utilize o modelo `.streamlit/secrets.toml.example` para configurar a Service Account em `.streamlit/secrets.toml`.

---

## Governança e Performance

1. **Cache de 1 Hora (`@st.cache_data(ttl=3600)`):** Cada consulta ao BigQuery é executada uma única vez a cada 60 minutos.
2. **Consultas Otimizadas:** Apenas as colunas necessárias das tabelas da Camada Refined são lidas.
3. **Filtros em Memória:** Os filtros de período, mês e canal de origem operam sobre os DataFrames em memória via Pandas, garantindo resposta imediata e controle de custos no GCP.
