# Transparência Jacareí — Pipeline de Dados

Dashboard analítico de licitações públicas da Prefeitura Municipal de Jacareí (SP),
construído com Python, PostgreSQL e Metabase. - Projeto planejado e feito a primeira versão em 2025 - melhorado em abril/maio de 2026

Versão futura com um dashboard com power BI ou com o metabase melhorado em desenvolvimento

## Fontes de dados - siap

| Endpoint                               | Descrição                            |
| -------------------------------------- | -------------------------------------- |
| `/licitacoes/licitacoes/index`       | Lista de licitações por ano          |
| `/sup_processo_compra`               | Datas de adjudicação e homologação |
| `/sup_itens`                         | Fornecedores e valores vencedores      |
| `/licitacoes/licitacoes/anexos.json` | Editais e documentos anexos            |

## Arquitetura

```
API SIAP Jacareí
      │
      ▼
scraper/collector.py   ← Python + requests + pandas
      │
      ▼
raw.*          ← dados brutos, append-only
      │
      ▼
staging.*      ← deduplicados, tipados, enriquecidos
      │
      ▼
mart.v_*       ← views analíticas prontas pro Metabase
      │
      ▼
Metabase :3000 ← dashboards públicos
```

## Como rodar

## docker

### 1. Subir o ambiente

```bash
cd docker
docker compose up -d
```

Aguarde o Metabase iniciar (~60s) e acesse http://localhost:3000

### 2. Criar o schema

```bash
# Na primeira vez (o docker já roda automaticamente os .sql em initdb.d)
# Mas se precisar rodar manualmente:
psql postgresql://postgres:postgres@localhost:5432/transparencia_jacarei \
  -f sql/01_schema.sql
```

### 3. Instalar dependências Python

```bash
cd scraper
pip install -r requirements.txt
```

### 4. Coletar os dados

```bash
python collector.py
```

A coleta respeita um delay de 0.8s entre requests. Para ~500 licitações/ano
com detalhes e itens, espere ~20 min por ano coletado.

### 5. Refresh da staging

```bash
psql postgresql://postgres:postgres@localhost:5432/transparencia_jacarei \
  -f sql/02_refresh_staging.sql
```

### 6. Configurar o Metabase

1. Acesse http://localhost:3000
2. Crie a conta admin
3. Conecte ao banco: host `postgres`, porta `5432`, banco `transparencia_jacarei`
4. Explore as views do schema `mart`:
   - `v_licitacoes` — visão geral com dias em aberto
   - `v_fornecedores` — ranking de CNPJs
   - `v_por_secretaria` — volume por órgão
   - `v_por_modalidade` — distribuição por tipo
   - `v_em_aberto_criticos` — alertas de prazo
   - `v_concentracao_por_processo` — concentração de mercado

## Dashboards sugeridos

- **Visão geral**: volume total licitado por ano + modalidade
- **Ranking de fornecedores**: quem recebe mais da Prefeitura
- **Painel de alertas**: processos abertos há mais de 30/60/90 dias
- **Concentração de mercado**: % do maior vencedor por processo
- **Linha do tempo**: evolução mensal de abertura e homologação

## Stack

- Python 3.11+
- PostgreSQL 16
- Metabase (latest)
- Docker Compose
