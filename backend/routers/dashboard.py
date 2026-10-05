from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.mart import VPorSecretaria, VPorModalidade
from models.staging import Licitacao

router = APIRouter()

@router.get("/resumo")
def resumo_dashboard(ano: int | None = None, db: Session = Depends(get_db)):
    query = db.query(
        func.count(Licitacao.id_processo_compra).label("total_processos"),
        func.sum(Licitacao.vl_estimado).label("valor_total_estimado")
    )
    
    abertos_query = db.query(func.count(Licitacao.id_processo_compra)).filter(Licitacao.st_aberto == True)
    
    if ano:
        query = query.filter(Licitacao.ano_modalidade == ano)
        abertos_query = abertos_query.filter(Licitacao.ano_modalidade == ano)
        
    resumo = query.first()
    total_abertos = abertos_query.scalar()
    
    return {
        "total_processos": resumo.total_processos or 0,
        "valor_total_estimado": resumo.valor_total_estimado or 0,
        "total_abertos": total_abertos or 0
    }

@router.get("/graficos")
def graficos_dashboard(ano: int | None = None, db: Session = Depends(get_db)):
    q_sec = db.query(VPorSecretaria)
    q_mod = db.query(VPorModalidade)
    
    if ano:
        q_sec = q_sec.filter(VPorSecretaria.ano_modalidade == ano)
        q_mod = q_mod.filter(VPorModalidade.ano_modalidade == ano)
        
    por_secretaria = q_sec.all()
    por_modalidade = q_mod.all()
    
    return {
        "por_secretaria": por_secretaria,
        "por_modalidade": por_modalidade
    }
