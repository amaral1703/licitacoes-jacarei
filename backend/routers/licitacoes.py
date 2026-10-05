from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models.mart import VLicitacao
from models.staging import Item

router = APIRouter()

@router.get("/")
def listar_licitacoes(skip: int = 0, limit: int = 50, secretaria: str | None = None, ano: int | None = None, db: Session = Depends(get_db)):
    query = db.query(VLicitacao)
    
    if secretaria:
        query = query.filter(VLicitacao.ds_unidade_adm == secretaria)
    if ano:
        query = query.filter(VLicitacao.ano_modalidade == ano)
    
    total = query.count()
    resultados = query.order_by(desc(VLicitacao.dt_abertura)).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": resultados
    }

@router.get("/{id_processo}")
def obter_licitacao(id_processo: int, db: Session = Depends(get_db)):
    licitacao = db.query(VLicitacao).filter(VLicitacao.id_processo_compra == id_processo).first()
    
    if not licitacao:
        raise HTTPException(status_code=404, detail="Licitacao nao encontrada")
    
    itens = db.query(Item).filter(Item.id_processo_compra == id_processo).all()
    
    return {
        "licitacao": licitacao,
        "itens": itens
    }
