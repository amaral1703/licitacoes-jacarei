from fastapi import APIRouter

router = APIRouter()

@router.post("/executar")
def executar_pipeline():
    return {"mensagem": "Disparo da coleta em background iniciado - teste inicial"}
