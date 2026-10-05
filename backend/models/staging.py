from sqlalchemy import Column, Integer, String, Boolean, Date, Numeric, DateTime
from database import Base

class Licitacao(Base):
    __tablename__ = "licitacoes"
    __table_args__ = {'schema': 'staging'}

    id_processo_compra = Column(Integer, primary_key=True, index=True)
    nr_processo_compra = Column(String)
    nr_modalidade = Column(String)
    nr_edital = Column(String)
    ano_modalidade = Column(Integer, index=True)
    ds_modalidade = Column(String)
    ds_tp_aquisicao = Column(String)
    ds_unidade_adm = Column(String, index=True)
    objeto = Column(String)
    lei = Column(String)
    sigla = Column(String)
    vl_estimado = Column(Numeric)
    dt_abertura = Column(Date)
    dt_homologacao = Column(Date)
    ds_situacao = Column(String)
    st_aberto = Column(Boolean, index=True)
    qtd_anexos = Column(Integer)
    coletado_em = Column(DateTime)

class Detalhe(Base):
    __tablename__ = "detalhes"
    __table_args__ = {'schema': 'staging'}

    id_processo_compra = Column(Integer, primary_key=True)
    dt_processo_compra = Column(Date)
    dt_julgamento = Column(Date)
    dt_adjudicacao = Column(Date)
    dt_homologacao = Column(Date)

class Item(Base):
    __tablename__ = "itens"
    __table_args__ = {'schema': 'staging'}

    # Como a tabela nao possui PK natural definida no schema, usamos as colunas compostas para que o SQLAlchemy consiga mapear corretamente.
    id_processo_compra = Column(Integer, primary_key=True)
    razao_social = Column(String)
    documento = Column(String, primary_key=True)
    tipo_documento = Column(String)
    valor_total = Column(Numeric, primary_key=True)
