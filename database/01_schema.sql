-- =============================================================================
-- Transparência Jacareí — Schema PostgreSQL
-- Camadas: raw (dados brutos) → staging (limpos) → mart (analítico)
-- =============================================================================

-- Schemas
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS mart;


-- =============================================================================
-- CAMADA RAW — dados exatamente como vêm da API
-- =============================================================================

CREATE TABLE IF NOT EXISTS raw.raw_licitacoes (
    id_processo_compra  TEXT,
    nr_processo_compra  TEXT,
    nr_modalidade       TEXT,
    nr_edital           TEXT,
    ano_modalidade      TEXT,
    ds_modalidade       TEXT,
    ds_tp_aquisicao     TEXT,
    ds_unidade_adm      TEXT,
    objeto              TEXT,
    lei                 TEXT,
    sigla               TEXT,
    sistema             TEXT,
    vl_estimado         NUMERIC,
    dt_abertura         DATE,
    dt_homologacao      DATE,
    ds_situacao         TEXT,
    st_aberto           BOOLEAN,
    qtd_anexos          INTEGER,
    coletado_em         TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS raw.raw_detalhes (
    id_processo_compra  TEXT,
    dt_processo_compra  DATE,
    dt_julgamento       DATE,
    dt_adjudicacao      DATE,
    dt_homologacao      DATE
);

CREATE TABLE IF NOT EXISTS raw.raw_itens (
    id_processo_compra  TEXT,
    razao_social        TEXT,
    documento           TEXT,   -- CNPJ/CPF sem formatação
    valor_total         NUMERIC
);


-- =============================================================================
-- CAMADA STAGING — deduplicada, tipada, enriquecida
-- =============================================================================

CREATE TABLE IF NOT EXISTS staging.licitacoes AS
SELECT DISTINCT ON (id_processo_compra)
    id_processo_compra::INTEGER,
    nr_processo_compra,
    nr_modalidade,
    nr_edital,
    ano_modalidade::INTEGER,
    ds_modalidade,
    ds_tp_aquisicao,
    ds_unidade_adm,
    TRIM(objeto)                                AS objeto,
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

CREATE TABLE IF NOT EXISTS staging.detalhes AS
SELECT DISTINCT ON (id_processo_compra)
    id_processo_compra::INTEGER,
    dt_processo_compra,
    dt_julgamento,
    dt_adjudicacao,
    dt_homologacao
FROM raw.raw_detalhes
ORDER BY id_processo_compra;

CREATE TABLE IF NOT EXISTS staging.itens AS
SELECT
    id_processo_compra::INTEGER,
    razao_social,
    documento,
    -- Classifica CNPJ (14 dígitos) vs CPF (11)
    CASE WHEN LENGTH(documento) = 14 THEN 'CNPJ'
         WHEN LENGTH(documento) = 11 THEN 'CPF'
         ELSE 'desconhecido' END                AS tipo_documento,
    valor_total
FROM raw.raw_itens
WHERE valor_total > 0;


-- =============================================================================
-- CAMADA MART — views analíticas prontas para o Metabase
-- =============================================================================

-- Visão geral enriquecida com dias em aberto
CREATE OR REPLACE VIEW mart.v_licitacoes AS
SELECT
    l.id_processo_compra,
    l.nr_processo_compra,
    l.ano_modalidade,
    l.ds_modalidade,
    l.ds_tp_aquisicao,
    l.ds_unidade_adm,
    l.objeto,
    l.lei,
    l.vl_estimado,
    l.dt_abertura,
    l.dt_homologacao,
    l.ds_situacao,
    l.st_aberto,
    -- Dias em aberto (processos ainda não homologados)
    CASE
        WHEN l.dt_homologacao IS NULL AND l.dt_abertura IS NOT NULL
        THEN CURRENT_DATE - l.dt_abertura
        ELSE NULL
    END                                     AS dias_em_aberto,
    d.dt_processo_compra,
    d.dt_julgamento,
    d.dt_adjudicacao,
    -- Prazo de julgamento em dias
    CASE
        WHEN d.dt_julgamento IS NOT NULL AND d.dt_processo_compra IS NOT NULL
        THEN d.dt_julgamento - d.dt_processo_compra
        ELSE NULL
    END                                     AS dias_ate_julgamento,
    l.qtd_anexos
FROM staging.licitacoes l
LEFT JOIN staging.detalhes d USING (id_processo_compra);


-- Ranking de fornecedores (CNPJ)
CREATE OR REPLACE VIEW mart.v_fornecedores AS
SELECT
    documento,
    tipo_documento,
    razao_social,
    COUNT(DISTINCT id_processo_compra)      AS qtd_processos,
    SUM(valor_total)                        AS valor_total_ganho,
    MIN(valor_total)                        AS menor_contrato,
    MAX(valor_total)                        AS maior_contrato,
    ROUND(AVG(valor_total)::NUMERIC, 2)     AS ticket_medio
FROM staging.itens
GROUP BY documento, tipo_documento, razao_social
ORDER BY valor_total_ganho DESC;


-- Volume por secretaria
CREATE OR REPLACE VIEW mart.v_por_secretaria AS
SELECT
    ds_unidade_adm                          AS secretaria,
    ano_modalidade,
    COUNT(*)                                AS qtd_licitacoes,
    SUM(vl_estimado)                        AS vl_total_estimado,
    COUNT(*) FILTER (WHERE st_aberto)       AS qtd_abertas,
    COUNT(*) FILTER (WHERE NOT st_aberto)   AS qtd_encerradas
FROM staging.licitacoes
GROUP BY ds_unidade_adm, ano_modalidade
ORDER BY ano_modalidade DESC, vl_total_estimado DESC;


-- Volume por modalidade
CREATE OR REPLACE VIEW mart.v_por_modalidade AS
SELECT
    ds_modalidade,
    ano_modalidade,
    COUNT(*)                                AS qtd,
    SUM(vl_estimado)                        AS vl_total,
    ROUND(AVG(vl_estimado)::NUMERIC, 2)     AS ticket_medio
FROM staging.licitacoes
WHERE vl_estimado > 0
GROUP BY ds_modalidade, ano_modalidade
ORDER BY ano_modalidade DESC, vl_total DESC;


-- Processos há mais tempo em aberto (fila de atenção)
CREATE OR REPLACE VIEW mart.v_em_aberto_criticos AS
SELECT
    id_processo_compra,
    nr_edital,
    ano_modalidade,
    ds_unidade_adm,
    objeto,
    vl_estimado,
    dt_abertura,
    CURRENT_DATE - dt_abertura             AS dias_em_aberto,
    CASE
        WHEN CURRENT_DATE - dt_abertura > 90  THEN 'crítico'
        WHEN CURRENT_DATE - dt_abertura > 30  THEN 'atenção'
        ELSE 'normal'
    END                                    AS nivel_alerta
FROM staging.licitacoes
WHERE st_aberto = TRUE
  AND dt_abertura IS NOT NULL
ORDER BY dias_em_aberto DESC;


-- Concentração de mercado por processo
CREATE OR REPLACE VIEW mart.v_concentracao_por_processo AS
SELECT
    i.id_processo_compra,
    l.objeto,
    l.ds_unidade_adm,
    l.vl_estimado,
    COUNT(DISTINCT i.documento)             AS qtd_fornecedores,
    MAX(i.valor_total)                      AS maior_valor_unico,
    ROUND(
        100.0 * MAX(i.valor_total) / NULLIF(SUM(i.valor_total), 0),
        1
    )                                       AS pct_maior_fornecedor
FROM staging.itens i
JOIN staging.licitacoes l USING (id_processo_compra)
GROUP BY i.id_processo_compra, l.objeto, l.ds_unidade_adm, l.vl_estimado
ORDER BY pct_maior_fornecedor DESC;
