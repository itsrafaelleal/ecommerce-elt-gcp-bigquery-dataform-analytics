
#%%
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

from google.cloud import storage
from dotenv import load_dotenv


# Config

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
RAW_PREFIX = os.getenv("GCS_RAW_PREFIX")
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

def check_config(BASE_DIR, BUCKET_NAME, RAW_PREFIX, RAW_DIR):

    if not BASE_DIR.exists() or not BUCKET_NAME or not RAW_PREFIX or not RAW_DIR.exists():
        raise ValueError("Variáveis de ambiente ou diretórios não encontrados")
    print("Todas as configurações encontradas")
    
check_config(BASE_DIR, BUCKET_NAME, RAW_PREFIX, RAW_DIR)

#%% verificacao dos arquivos

def calcular_sha256(caminho: Path) -> str:

    h = hashlib.sha256()
    with open(caminho, "rb") as f:  # "rb" = binário, pois o hash é sobre bytes
        for bloco in iter(lambda: f.read(8192), b""):
            h.update(bloco)
    return h.hexdigest()  # devolve o hash como texto hexadecimal


def check_files(raw_prefix: str) -> dict:
    
    faltando = [nome for nome in EXPECTED_FILES if not (RAW_DIR / nome).exists()]
    if faltando:
        raise FileNotFoundError(
            f"Arquivos esperados não encontrados em {RAW_DIR}: {faltando}"
        )
    
    arquivos = []
    for nome in EXPECTED_FILES:
        caminho = RAW_DIR / nome
        nome_destino = nome.replace("_example.csv", ".csv")
        arquivos.append(
            {
                "nome": nome,
                "nome_destino": nome_destino,
                "tamanho_bytes": caminho.stat().st_size,
                "sha256": calcular_sha256(caminho),
                "destino_gcs": f"gs://{BUCKET_NAME}/{raw_prefix}/{nome_destino}",
            }
        )
    
    return {
        "projeto": "veloja-ecommerce-medalhao",
        "bucket": BUCKET_NAME,
        "raw_prefix": raw_prefix,
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(),
        "total_arquivos": len(arquivos),
        "arquivos": arquivos,
    }        

# var da funcao
hoje = datetime.now(timezone.utc).strftime("%Y%m%d")
raw_prefix = f"{RAW_PREFIX}/{hoje}"  # ex.: raw/ecommerce/20260401

# Chamada da função
manifesto = check_files(raw_prefix)
print(json.dumps(manifesto, indent=4, ensure_ascii=False))
        
#%% upload dos arquivos

# var da funcao
client = storage.Client()
bucket = client.bucket(BUCKET_NAME)

# funcao
def upload_file(bucket: storage.Bucket, local_path: Path, blob_name: str) -> None:

    blob = bucket.blob(blob_name)
    blob.upload_from_filename(str(local_path))
    print(f"  enviado -> gs://{bucket.name}/{blob_name}")


print(f"\nEnviando {manifesto['total_arquivos']} CSV(s) para gs://{BUCKET_NAME}/{raw_prefix}/")
for item in manifesto["arquivos"]:
    nome_local = item["nome"]
    nome_destino = item.get("nome_destino", nome_local)
    upload_file(bucket, RAW_DIR / nome_local, f"{raw_prefix}/{nome_destino}")


#%% salvar o manifesto (local) e enviar ao bucket

OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

caminho_manifesto = OUTPUT_DIR / "manifesto.json"
with open(caminho_manifesto, "w", encoding="utf-8") as f:
    json.dump(manifesto, f, indent=4, ensure_ascii=False)
print(f"\nManifesto salvo localmente em: {caminho_manifesto}")

blob_manifesto = f"{raw_prefix}/_manifesto/manifesto.json"
bucket.blob(blob_manifesto).upload_from_filename(str(caminho_manifesto))
print(f"Manifesto enviado -> gs://{BUCKET_NAME}/{blob_manifesto}")
