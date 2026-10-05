from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models.mart import VEmAbertoCritico, VConcentracaoPorProcesso

router = APIRouter()

@router.get("/atrasados")
def listar_processos_atrasados(limit: int = 50, db: Session = Depends(get_db)):
    resultados = db.query(VEmAbertoCritico).order_by(desc(VEmAbertoCritico.dias_em_aberto)).limit(limit).all()
    return resultados

@router.get("/concentracao")
def listar_concentracao_mercado(limit: int = 50, db: Session = Depends(get_db)):
    resultados = db.query(VConcentracaoPorProcesso).order_by(desc(VConcentracaoPorProcesso.pct_maior_fornecedor)).limit(limit).all()
    return resultados
