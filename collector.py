"""
Transparência Jacareí — Scraper principal
Coleta licitações, detalhes e itens/fornecedores via API do SIAP.
"""

import time
import logging
import re
from datetime import datetime, date
from typing import Optional

import requests
import pandas as pd
from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_URL = "https://siap.jacarei.sp.gov.br/portal-transparencia/api"
DB_URL = "postgresql://postgres:1234@localhost:5432/transparencia_jacarei"

ANOS = [date.today().year]                         # coleta apenas o ano atual por enquanto
DELAY_SEGUNDOS = 0.8                               # respeito ao servidor
MAX_RETRIES = 3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("coleta.log"),
    ],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

SESSION = requests.Session()
SESSION.headers.update({"Accept": "application/json"})


def _get(url: str, params: dict = None) -> Optional[dict | list]:
    for tentativa in range(1, MAX_RETRIES + 1):
        try:
            r = SESSION.get(url, params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.HTTPError as e:
            log.warning(f"HTTP {r.status_code} em {url} (tentativa {tentativa}): {e}")
        except Exception as e:
            log.warning(f"Erro em {url} (tentativa {tentativa}): {e}")
        time.sleep(2 ** tentativa)
    log.error(f"Falhou após {MAX_RETRIES} tentativas: {url}")
    return None


# ---------------------------------------------------------------------------
# Extração
# ---------------------------------------------------------------------------

def buscar_licitacoes_ano(ano: int) -> list[dict]:
    """Endpoint principal — lista todas as licitações de um ano."""
    # A API espera o parâmetro de ano no formato de data que o portal envia.
    # Usamos a representação ISO mais limpa que o backend aceita.
    url = f"{BASE_URL}//licitacoes/licitacoes/index"
    params = {
        "ano": f"Thu Dec 31 {ano} 00:00:00 GMT-0300 (Horário Padrão de Brasília)",
        "id_entidade": 1,
        "id_situacao_licitacao": 0,
        "tipo_situacao": "Geral",
    }
    dados = _get(url, params=params)
    if not dados:
        return []
    licitacoes = dados.get("licitacoes", [])
    log.info(f"  {ano}: {len(licitacoes)} licitações encontradas")
    return licitacoes


def buscar_detalhes(id_processo_compra: str) -> Optional[dict]:
    """Datas de adjudicação, homologação, julgamento e abertura do processo."""
    url = f"{BASE_URL}//sup_processo_compra"
    dados = _get(url, params={"id_processo_compra": id_processo_compra})
    if not dados:
        return None
    processos = dados.get("processo_compra", [])
    return processos[0] if processos else None


def buscar_itens(id_processo_compra: str) -> list[dict]:
    """Empresas participantes e valores vencedores por item."""
    url = f"{BASE_URL}//sup_itens"
    dados = _get(url, params={"id_processo_compra": id_processo_compra})
    if isinstance(dados, list):
        return dados
    return []


def buscar_anexos(id_processo_compra: str) -> list[dict]:
    """Links dos editais e documentos anexos."""
    url = f"{BASE_URL}//licitacoes/licitacoes/anexos.json"
    dados = _get(url, params={"id_processo_compra": id_processo_compra})
    if isinstance(dados, list):
        return dados
    return []


# ---------------------------------------------------------------------------
# Transformação
# ---------------------------------------------------------------------------

def _parse_valor(valor_str: str) -> Optional[float]:
    """'R$ 3.074.707,00' → 3074707.0"""
    if not valor_str:
        return None
    limpo = re.sub(r"[R$\s]", "", valor_str).replace(".", "").replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        return None


def _parse_data(dt_str: str) -> Optional[date]:
    """Aceita 'DD/MM/YYYY HH:MM' ou 'YYYY-MM-DD'."""
    if not dt_str:
        return None
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(dt_str.strip(), fmt).date()
        except ValueError:
            continue
    return None


def transformar_licitacao(raw: dict) -> dict:
    return {
        "id_processo_compra":   raw.get("id_processo_compra"),
        "nr_processo_compra":   raw.get("nr_processo_compra"),
        "nr_modalidade":        raw.get("nr_modalidade"),
        "nr_edital":            raw.get("nr_edital"),
        "ano_modalidade":       raw.get("ano_modalidade"),
        "ds_modalidade":        raw.get("ds_modalidade"),
        "ds_tp_aquisicao":      raw.get("ds_tp_aquisicao"),
        "ds_unidade_adm":       raw.get("ds_unidade_adm"),
        "objeto":               (raw.get("objeto") or "").strip(),
        "lei":                  raw.get("lei"),
        "sigla":                raw.get("sigla", "").strip(),
        "sistema":              raw.get("sistema", "").strip(),
        "vl_estimado":          _parse_valor(raw.get("vl_estimado")),
        "dt_abertura":          _parse_data(raw.get("dt_abertura")),
        "dt_homologacao":       _parse_data(raw.get("dt_homologacao")),
        "ds_situacao":          raw.get("ds_st_processo_compra"),
        "st_aberto":            raw.get("st_dt_abertura", False),
        "qtd_anexos":           int(raw.get("qtd_anexos") or 0),
        "coletado_em":          datetime.utcnow(),
    }


def transformar_detalhe(raw: dict, id_processo_compra: str) -> dict:
    return {
        "id_processo_compra":   id_processo_compra,
        "dt_processo_compra":   _parse_data(raw.get("dt_processo_compra")),
        "dt_julgamento":        _parse_data(raw.get("dt_julgamento")),
        "dt_adjudicacao":       _parse_data(raw.get("dt_adjudicacao")),
        "dt_homologacao":       _parse_data(raw.get("dt_homologacao")),
    }


def transformar_item(raw: dict, id_processo_compra: str) -> dict:
    return {
        "id_processo_compra":   id_processo_compra,
        "razao_social":         (raw.get("razao_social") or "").strip(),
        "documento":            re.sub(r"\D", "", raw.get("documento") or ""),
        "valor_total":          float(raw.get("valor_total") or 0),
    }


# ---------------------------------------------------------------------------
# Carga no PostgreSQL
# ---------------------------------------------------------------------------

def upsert_licitacoes(engine, registros: list[dict]):
    if not registros:
        return
    df = pd.DataFrame(registros)
    df.to_sql("raw_licitacoes", engine, schema="raw", if_exists="append",
              index=False, method="multi")
    log.info(f"  → {len(df)} linhas em raw.raw_licitacoes")


def upsert_detalhes(engine, registros: list[dict]):
    if not registros:
        return
    df = pd.DataFrame(registros)
    df.to_sql("raw_detalhes", engine, schema="raw", if_exists="append",
              index=False, method="multi")


def upsert_itens(engine, registros: list[dict]):
    if not registros:
        return
    df = pd.DataFrame(registros)
    df.to_sql("raw_itens", engine, schema="raw", if_exists="append",
              index=False, method="multi")


# ---------------------------------------------------------------------------
# Orquestração principal
# ---------------------------------------------------------------------------

def coletar_tudo():
    engine = create_engine(DB_URL)
    log.info("=== Início da coleta ===")

    for ano in ANOS:
        log.info(f"Coletando ano {ano}...")
        licitacoes_raw = buscar_licitacoes_ano(ano)

        licitacoes_t  = []
        detalhes_t    = []
        itens_t       = []

        for lic in licitacoes_raw:
            id_pc = lic.get("id_processo_compra")
            if not id_pc:
                continue

            licitacoes_t.append(transformar_licitacao(lic))

            time.sleep(DELAY_SEGUNDOS)

            detalhe = buscar_detalhes(id_pc)
            if detalhe:
                detalhes_t.append(transformar_detalhe(detalhe, id_pc))

            time.sleep(DELAY_SEGUNDOS)

            itens = buscar_itens(id_pc)
            for item in itens:
                itens_t.append(transformar_item(item, id_pc))

            time.sleep(DELAY_SEGUNDOS)

        upsert_licitacoes(engine, licitacoes_t)
        upsert_detalhes(engine, detalhes_t)
        upsert_itens(engine, itens_t)

    log.info("=== Coleta finalizada ===")


if __name__ == "__main__":
    coletar_tudo()
