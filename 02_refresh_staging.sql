-- =============================================================================
-- Refresh das camadas staging e mart
-- Execute após cada coleta: psql $DB_URL -f 02_refresh_staging.sql
-- =============================================================================

BEGIN;

-- Staging: licitacoes
TRUNCATE staging.licitacoes;
INSERT INTO staging.licitacoes
SELECT DISTINCT ON (id_processo_compra)
    id_processo_compra::INTEGER,
    nr_processo_compra,
    nr_modalidade,
    nr_edital,
    ano_modalidade::INTEGER,
    ds_modalidade,
    ds_tp_aquisicao,
    ds_unidade_adm,
    TRIM(objeto),
    lei,
    sigla,
    vl_estimado,
    dt_abertura,
    dt_homologacao,
    ds_situacao,
    st_aberto,
    qtd_anexos,
    coletado_em
FROM raw.raw_licitacoes
ORDER BY id_processo_compra, coletado_em DESC;

-- Staging: detalhes
TRUNCATE staging.detalhes;
INSERT INTO staging.detalhes
SELECT DISTINCT ON (id_processo_compra)
    id_processo_compra::INTEGER,
    dt_processo_compra,
    dt_julgamento,
    dt_adjudicacao,
    dt_homologacao
FROM raw.raw_detalhes
ORDER BY id_processo_compra;

-- Staging: itens
TRUNCATE staging.itens;
INSERT INTO staging.itens
SELECT
    id_processo_compra::INTEGER,
    razao_social,
    documento,
    CASE WHEN LENGTH(documento) = 14 THEN 'CNPJ'
         WHEN LENGTH(documento) = 11 THEN 'CPF'
         ELSE 'desconhecido' END,
    valor_total
FROM raw.raw_itens
WHERE valor_total > 0;

COMMIT;

-- As views mart.v_* são recalculadas automaticamente (são VIEWs, não tabelas)
SELECT 'Refresh concluído em ' || now() AS status;
