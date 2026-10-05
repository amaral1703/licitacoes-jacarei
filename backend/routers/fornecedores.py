from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models.mart import VFornecedor
from models.staging import Item, Licitacao

router = APIRouter()

@router.get("/")
def listar_fornecedores(limit: int = 20, documento: str | None = None, db: Session = Depends(get_db)):
    query = db.query(VFornecedor)
    
    if documento:
        query = query.filter(VFornecedor.documento == documento)
        
    resultados = query.order_by(desc(VFornecedor.valor_total_ganho)).limit(limit).all()
    return resultados

@router.get("/{documento}")
def obter_fornecedor(documento: str, db: Session = Depends(get_db)):
    fornecedor = db.query(VFornecedor).filter(VFornecedor.documento == documento).first()
    
    if not fornecedor:
        raise HTTPException(status_code=404, detail="Fornecedor nao encontrado")
    
    # Busca historico de contratos (itens) desse fornecedor juntamente com informacoes da licitacao
    contratos = db.query(Item.id_processo_compra, Item.valor_total, Licitacao.ano_modalidade, Licitacao.objeto)\
        .join(Licitacao, Item.id_processo_compra == Licitacao.id_processo_compra)\
        .filter(Item.documento == documento).all()
        
    contratos_formatados = [
        {
            "id_processo_compra": c.id_processo_compra,
            "valor_total": c.valor_total,
            "ano": c.ano_modalidade,
            "objeto": c.objeto
        } for c in contratos
    ]
    
    return {
        "fornecedor": fornecedor,
        "historico": contratos_formatados
    }
