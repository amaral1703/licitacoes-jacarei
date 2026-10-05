from sqlalchemy import Column, Integer, String, Boolean, Date, Numeric
from database import Base

class VLicitacao(Base):
    __tablename__ = "v_licitacoes"
    __table_args__ = {'schema': 'mart'}

    id_processo_compra = Column(Integer, primary_key=True)
    nr_processo_compra = Column(String)
    ano_modalidade = Column(Integer)
    ds_modalidade = Column(String)
    ds_tp_aquisicao = Column(String)
    ds_unidade_adm = Column(String)
    objeto = Column(String)
    lei = Column(String)
    vl_estimado = Column(Numeric)
    dt_abertura = Column(Date)
    dt_homologacao = Column(Date)
    ds_situacao = Column(String)
    st_aberto = Column(Boolean)
    dias_em_aberto = Column(Integer)
    dt_processo_compra = Column(Date)
    dt_julgamento = Column(Date)
    dt_adjudicacao = Column(Date)
    dias_ate_julgamento = Column(Integer)
    qtd_anexos = Column(Integer)

class VFornecedor(Base):
    __tablename__ = "v_fornecedores"
    __table_args__ = {'schema': 'mart'}

    documento = Column(String, primary_key=True)
    tipo_documento = Column(String)
    razao_social = Column(String)
    qtd_processos = Column(Integer)
    valor_total_ganho = Column(Numeric)
    menor_contrato = Column(Numeric)
    maior_contrato = Column(Numeric)
    ticket_medio = Column(Numeric)

class VPorSecretaria(Base):
    __tablename__ = "v_por_secretaria"
    __table_args__ = {'schema': 'mart'}

    secretaria = Column(String, primary_key=True)
    ano_modalidade = Column(Integer, primary_key=True)
    qtd_licitacoes = Column(Integer)
    vl_total_estimado = Column(Numeric)
    qtd_abertas = Column(Integer)
    qtd_encerradas = Column(Integer)

class VPorModalidade(Base):
    __tablename__ = "v_por_modalidade"
    __table_args__ = {'schema': 'mart'}

    ds_modalidade = Column(String, primary_key=True)
    ano_modalidade = Column(Integer, primary_key=True)
    qtd = Column(Integer)
    vl_total = Column(Numeric)
    ticket_medio = Column(Numeric)

class VEmAbertoCritico(Base):
    __tablename__ = "v_em_aberto_criticos"
    __table_args__ = {'schema': 'mart'}

    id_processo_compra = Column(Integer, primary_key=True)
    nr_edital = Column(String)
    ano_modalidade = Column(Integer)
    ds_unidade_adm = Column(String)
    objeto = Column(String)
    vl_estimado = Column(Numeric)
    dt_abertura = Column(Date)
    dias_em_aberto = Column(Integer)
    nivel_alerta = Column(String)

class VConcentracaoPorProcesso(Base):
    __tablename__ = "v_concentracao_por_processo"
    __table_args__ = {'schema': 'mart'}

    id_processo_compra = Column(Integer, primary_key=True)
    objeto = Column(String)
    ds_unidade_adm = Column(String)
    vl_estimado = Column(Numeric)
    qtd_fornecedores = Column(Integer)
    maior_valor_unico = Column(Numeric)
    pct_maior_fornecedor = Column(Numeric)
