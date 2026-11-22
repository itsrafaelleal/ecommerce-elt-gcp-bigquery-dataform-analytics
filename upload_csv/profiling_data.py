#%%
import json
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv


# Config

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
RAW_DIR = Path(BASE_DIR / "data" / "raw")

EXPECTED_FILES = [
    "clientes_example.csv",
    "produtos_example.csv",
    "pedidos_example.csv",
    "itens_pedido_example.csv",
    "pagamentos_example.csv",
    "eventos_marketing_example.csv",
    "metas_orcamento_2025_example.csv",
]

# construir o profiling

def gerar_relatorio_na(df) -> dict:
    relatorio_na = {}
    for coluna in df.columns:
        qtd_vazios = (df[coluna] == "").sum()
        qtd_NaN = df[coluna].isna().sum()
        total = int(qtd_NaN + qtd_vazios)
        if total > 0:
          relatorio_na[coluna] = total
    return relatorio_na

relatorio_profiling ={}

for name in EXPECTED_FILES:          
    df = pd.read_csv(RAW_DIR / name)
    chave_primaria = df.columns[0]
    
    relatorio_profiling[name] ={
          "linhas": int(df.shape[0]),
          "colunas": int(df.shape[1]),
          "vazios_por_coluna": gerar_relatorio_na(df),
          "chave_primaria": chave_primaria,
          "chaves_duplicadas": int(df[chave_primaria].duplicated().sum()),
      }

#%%  SALVAR

print(json.dumps(relatorio_profiling, indent=2, ensure_ascii=False))


OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

caminho_saida = OUTPUT_DIR / "relatorio_profiling.json"
with open(caminho_saida, "w", encoding="utf-8") as f:
    json.dump(relatorio_profiling, f, indent=2, ensure_ascii=False)

print(f"Relatório salvo em: {caminho_saida}")
