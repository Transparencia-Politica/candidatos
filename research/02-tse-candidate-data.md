# TSE / Candidate Data for Candidato (Transparência-Política)

Research date: 2026-06-26. Scope: candidate & electoral data acquisition and screening for the 2026 Brazilian general election (1st round **4 Oct 2026**, 2nd round **25 Oct 2026**). Legislative voting APIs (Câmara/Senado) are covered by a separate report.

All endpoints below were live-tested where marked **[verified live]**.

---

## 0. TL;DR — the two data spines you should build on

1. **Bulk CSV/ZIP from the TSE Open Data Portal** (`dadosabertos.tse.jus.br`, files served from `cdn.tse.jus.br`) for the canonical, per-cycle snapshots: candidate registrations, assets, coalitions, campaign finance, cassation reasons, social media, photos, government plans.
2. **The DivulgaCandContas REST API** (`divulgacandcontas.tse.jus.br/divulga/rest/v1`) for *live, per-candidate, structured* JSON during the campaign — including fields the bulk CSVs do not surface cleanly (ficha-limpa motive flags, cassation processes, prior-election history, government-plan file links). **[verified live]**

For analytics/joins across cycles, lean on **Base dos Dados** (cleaned TSE tables in BigQuery) instead of parsing raw CSVs yourself. Use **CNJ DataJud**, **Ranking dos Políticos**, and journalism datasets for integrity/background enrichment.

---

## 1. TSE Open Data + DivulgaCandContas

### 1.1 Portal de Dados Abertos do TSE (bulk files)

- Portal home: <https://dadosabertos.tse.jus.br/> — CKAN-style catalog of datasets, grouped by theme and election year.
- Institutional landing: <https://www.tse.jus.br/administracao/painel/portal-de-dados-abertos-do-tse>
- Candidates group (per year): e.g. **2024** <https://dadosabertos.tse.jus.br/dataset/candidatos-2024> ; **2022** equivalents exist (swap the year). For 2026 the dataset will appear as `candidatos-2026`.
- Campaign-finance group: <https://dadosabertos.tse.jus.br/group/prestacao-de-contas-eleitorais> and per-year dataset e.g. <https://dadosabertos.tse.jus.br/dataset/prestacao-de-contas-eleitorais-2024>.
- Search any theme: <https://dadosabertos.tse.jus.br/dataset/?q=candidatos>
- Legacy mirror (older cycles, same files): "Repositório de Dados Eleitorais" <https://www.tse.jus.br/eleicoes/estatisticas/repositorio-de-dados-eleitorais-1/repositorio-de-dados-eleitorais>

**Update frequency:** daily during the campaign. **Source systems:** CAND, Candex, DivulgaCand. **License:** Creative Commons Atribuição.

#### Files in the "Candidatos" dataset (verified from the 2024 dataset page)

Each is a national ZIP of CSVs (one CSV per UF + a `BRASIL` aggregate). URLs follow a stable pattern on `cdn.tse.jus.br`; **for 2026, swap `2024`→`2026`.**

| Content | Resource (2024) | Download URL pattern |
|---|---|---|
| Candidate registrations (core) | `consulta_cand_2024.zip` | `https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_2024.zip` |
| Complementary info (e.g. max spend limit, declared) | `consulta_cand_complementar_2024.zip` | `https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand_complementar/consulta_cand_complementar_2024.zip` |
| **Declared assets (bens declarados)** | `bem_candidato_2024.zip` | `https://cdn.tse.jus.br/estatistica/sead/odsele/bem_candidato/bem_candidato_2024.zip` |
| Coalitions (coligações) | `consulta_coligacao_2024.zip` | `https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_coligacao/consulta_coligacao_2024.zip` |
| Seats in dispute (vagas) | `consulta_vagas_2024.zip` | `https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_vagas/consulta_vagas_2024.zip` |
| **Reasons for cassation** | `motivo_cassacao_2024.zip` | `https://cdn.tse.jus.br/estatistica/sead/odsele/motivo_cassacao/motivo_cassacao_2024.zip` |
| Candidate social media | `rede_social_candidato_2024.zip` | `https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/rede_social_candidato_2024.zip` |
| Candidate photos (JPEG, per UF) | `foto_cand_2024_<UF>_div.zip` | `https://cdn.tse.jus.br/estatistica/sead/odsele/foto_candidato/foto_cand_2024_<UF>_div.zip` |
| Government plans / proposta de governo (PDF, per UF) | per-UF package | served under the same `odsele` tree, one package per UF |

> Note: directory names under `odsele/` are the canonical thing; the only varying part is the 4-digit year. Confirm exact 2026 file names by opening `https://dadosabertos.tse.jus.br/dataset/candidatos-2026` once published.

#### CSV layout — `consulta_cand` (the core registration file)

Semicolon-delimited (`;`), Latin-1 (ISO-8859-1) encoded, header row in ALL CAPS. The layout is documented in a `leiame`/`LEIAME.pdf` shipped inside each ZIP. Key columns useful for screening:

- Identity: `NR_CPF_CANDIDATO`, `NR_TITULO_ELEITORAL_CANDIDATO`, `NM_CANDIDATO`, `NM_URNA_CANDIDATO`, `NR_CANDIDATO`, `DT_NASCIMENTO`, `DS_GENERO`, `DS_COR_RACA`, `DS_GRAU_INSTRUCAO`, `DS_OCUPACAO`, `DS_ESTADO_CIVIL`.
- Race context: `ANO_ELEICAO`, `SG_UF`, `DS_CARGO`, `CD_CARGO`, `SG_PARTIDO`, `NR_PARTIDO`, `NM_PARTIDO`, `NM_COLIGACAO`, `DS_COMPOSICAO_COLIGACAO`.
- **Eligibility / status (the screening columns):** `DS_SITUACAO_CANDIDATURA` (Apto/Inapto), `DS_DETALHE_SITUACAO_CAND` (Deferido / Indeferido / Cassado / etc.), `CD_SITUACAO_CANDIDATO_PLEITO`, `ST_REELEICAO`, `NR_PROCESSO`.
- Spend ceiling: `VR_DESPESA_MAX_CAMPANHA`.

`bem_candidato` columns: `SQ_CANDIDATO` (join key), `NR_ORDEM_BEM_CANDIDATO`, `CD_TIPO_BEM_CANDIDATO`, `DS_TIPO_BEM_CANDIDATO`, `DS_BEM_CANDIDATO`, `VR_BEM_CANDIDATO`, `DT_ULTIMA_ATUALIZACAO`. Join to candidates on **`SQ_CANDIDATO`** (sequence id, unique per candidate per election — the universal TSE join key across every file).

#### Campaign finance — "Prestação de Contas Eleitorais" dataset

Files (per year, same `odsele` pattern, e.g. `prestacao_de_contas_eleitorais_candidatos_2024.zip`):
- **`receitas_candidatos_*`** — donations received: donor name + `NR_CPF_CNPJ_DOADOR`, `DS_ORIGEM_RECEITA`, `DS_FONTE_RECEITA` (FEFC/Fundo Partidário vs. private), `VR_RECEITA`, `DS_ESPECIE_RECEITA`, plus *originating* donor for triangulated donations (`NR_CPF_CNPJ_DOADOR_ORIGINARIO`).
- **`despesas_contratadas_*` / `despesas_pagas_*`** — expenses: supplier CPF/CNPJ, `DS_DESPESA`, `VR_DESPESA`.
- Plus party/committee accounts and the analysis result (`DS_SITUACAO_PRESTACAO_CONTAS` — e.g. *Aprovada*, *Aprovada com ressalvas*, *Desaprovada*, *Não prestou*). This is the field that tells you whether the campaign accounts were **rejected**.

### 1.2 DivulgaCandContas REST API (live JSON) — **[verified live]**

The official frontend (<https://divulgacandcontas.tse.jus.br/divulga/>) is an Angular SPA backed by an undocumented public JSON API. Best community reference: **augusto-herrmann/divulgacandcontas-doc** <https://github.com/augusto-herrmann/divulgacandcontas-doc> (OpenAPI 3.0.1 spec `divulgacandcontas-swagger.yaml` on the `main` branch).

- **Base URL:** `https://divulgacandcontas.tse.jus.br/divulga/rest/v1`
- **Rate limiting:** undocumented but real — put a delay (≥1s) between calls and set a normal `User-Agent`; the repo explicitly warns IPs get blocked under load.

**Election id ("eleicao") for 2022 = `2040602022`; 2024 municipais = `2045202024`.** The 2026 general-election id will follow the `2…2026` pattern; discover it at runtime from `/eleicao/ordinarias`. For federal/general elections the "municipio/localidade" path segment is **`BR`** (national) or the UF code; cargo codes: `1`=Presidente, `3`=Governador, `5`=Senador, `6`=Deputado Federal, `7`=Deputado Estadual, `8`=Deputado Distrital.

Verified endpoints:

| Purpose | Path | Verified |
|---|---|---|
| List election years | `/eleicao/anos-eleitorais` | ✅ returns `[2024,2022,...]` |
| List ordinary elections (get the id) | `/eleicao/ordinarias` | ✅ returns objects with `id`, `nomeEleicao`, `tipoAbrangencia` |
| List candidates for a race | `/candidatura/listar/{ano}/{ufOuBR}/{idEleicao}/{cargo}/candidatos` | ✅ e.g. `/candidatura/listar/2022/BR/2040602022/1/candidatos` |
| **Candidate full detail** | `/candidatura/buscar/{ano}/{ufOuBR}/{idEleicao}/candidato/{sqCandidato}` | ✅ |
| Cargos in dispute (municipal) | `/eleicao/listar/municipios/{idEleicao}/{municipio}/cargos` | (spec) |
| Campaign-finance "prestador" | `/prestador/consulta/{idEleicao}/{ano}/{municipio}/{cargo}/90/90/{sqCandidato}` | (spec) |
| Supplementary elections | `/eleicao/suplementares/{ano}/{uf}` , `/eleicao/estados/{ano}/ano` | (spec) |

**The candidate-detail endpoint is the screening goldmine** — verified response keys include:
`nomeCompleto, cpf, tituloEleitor, dataDeNascimento, descricaoSituacao` (Deferido/Indeferido), `grauInstrucao, ocupacao, nomeColigacao, composicaoColigacao, partido, vices, cargo, eleicao`, plus:
- **`bens`** (array: `ordem, descricao, descricaoDeTipoDeBem, valor, dataUltimaAtualizacao`) and **`totalDeBens`** — e.g. tested candidate returned 17 assets totalling R$ 3.039.761,97.
- **`processosCassacao`**, **`processosDesconstituicao`** — judicial processes against the candidacy.
- **Ficha-limpa / ineligibility motive flags** (booleans): `st_MOTIVO_FICHA_LIMPA`, `st_MOTIVO_ABUSO_PODER`, `st_MOTIVO_COMPRA_VOTO`, `st_MOTIVO_CONDUTA_VEDADA`, `st_MOTIVO_GASTO_ILICITO`, `st_MOTIVO_AUSENCIA_REQUISITO`, `st_MOTIVO_IND_PARTIDO`, `ds_MOTIVO_OUTROS`; plus `isCandidatoInapto`, `candidatoApto`, `motivos`, `motivoSituacao`.
- **`arquivos`** (array with `idArquivo, codTipo, url`) — links to the **proposta de governo / government plan PDFs** and other filed documents (`codTipo` distinguishes plan vs. other; files live under `…/divulga/file/{idArquivo}…`).
- **`eleicoesAnteriores`** — prior candidacies (history across cycles, returned inline).
- `gastoCampanha`, `cnpjcampanha` (campaign CNPJ), `emails`, `sites` (official social/web).

> Practical pattern for 2026: poll `/eleicao/ordinarias` to grab the 2026 id once registrations open, enumerate races via `/candidatura/listar/...` per UF+cargo, then hit `/candidatura/buscar/...` per `sqCandidato`. Cache aggressively; reconcile against the bulk CSVs for the authoritative snapshot.

### 1.3 How to screen / evaluate a candidate from TSE alone

- **Eligibility / "ficha limpa":** TSE does not ship a single boolean "ficha limpa = yes/no". You infer it from `DS_DETALHE_SITUACAO_CAND` / `descricaoSituacao` (Indeferido/Cassado ⇒ problem) **and** the `st_MOTIVO_*` flags from DivulgaCandContas (`st_MOTIVO_FICHA_LIMPA=true` means an LC 64/90 "Lei da Ficha Limpa" ground was raised). Cross-check `processosCassacao`.
- **Rejected accounts:** `DS_SITUACAO_PRESTACAO_CONTAS = Desaprovada` / `Não prestou` in the prestação-de-contas files.
- **Criminal/judicial:** TSE only exposes *electoral* processes (cassação/desconstituição). For general criminal/civil background use **CNJ DataJud** (§3) keyed by CPF/name.
- **Asset evolution across cycles:** stack `bem_candidato` for the same `NR_CPF_CANDIDATO` across 2014/2018/2022/2026, sum `VR_BEM_CANDIDATO` per cycle, flag implausible jumps (e.g. wealth growth far above income/inflation). CPF is the stable cross-cycle key; `SQ_CANDIDATO` is per-election only.
- **Donor concentration / financing independence:** from `receitas_candidatos`, compute share of total from public funds (FEFC/Fundo Partidário) vs. private, top-N donor concentration (HHI), and self-funding ratio. Use `NR_CPF_CNPJ_DOADOR_ORIGINARIO` to unmask triangulated party money.

### 1.4 2026 timeline (verified, TSE)

Sources: <https://www.tse.jus.br/eleicoes/eleicoes-2026>, <https://www.tse.jus.br/comunicacao/noticias/2026/Marco/eleicoes-2026-confira-as-principais-datas-do-calendario-eleitoral>, <https://www.tse.jus.br/eleicoes/calendario-eleitoral>

- **20 Jul – 5 Aug 2026:** party conventions (choose candidates, coalitions).
- **15 Aug 2026:** deadline to file candidacy registration (registro de candidatura). **DivulgaCand data becomes public around this date** — registrations are published as filed, so candidate lists/details start populating in the second half of August (status begins as *registration requested*, then moves to Deferido/Indeferido as judged).
- **16 Aug 2026:** official campaign / electoral propaganda begins.
- **4 Oct 2026:** 1st round. **25 Oct 2026:** possible 2nd round.
- Campaign-finance partial reports are filed during the campaign; final prestação de contas after the election. Plan your ingestion to go live mid-August and refresh daily.

---

## 2. Base dos Dados (cleaned TSE tables in BigQuery)

- Dataset page: <https://basedosdados.org/dataset/br-tse-eleicoes> ("Eleições Brasileiras", TSE data since 1945).
- Why use it: TSE ships ~30 separate ZIPs per cycle with inconsistent column names, Latin-1 encoding, and `;` delimiters across years. Base dos Dados **harmonizes column names and types across all cycles** into one queryable schema in BigQuery, so cross-year joins (asset evolution, repeat candidates) are trivial SQL instead of an ETL project.
- BigQuery project/dataset: **`basedosdados.br_tse_eleicoes.<table>`**.

Confirmed/representative tables (verify exact slugs on the dataset page's left menu before coding):
- `candidatos` — registrations across cycles (confirmed).
- `bens_candidato` — declared assets (confirmed: `…?bdm_table=bens_candidato`).
- `despesas_candidatos`, `receitas_candidatos` — campaign expenses/donations.
- `prestacao_contas` / results of account analysis.
- `resultados_candidato`, `detalhes_votacao_municipio_zona` — vote results.
- `perfil_eleitorado` — electorate profile.

> ⚠️ Latency caveat: Base dos Dados ingests *after* TSE publishes and cleans, so for live 2026 campaign data it lags. Use it for historical/analytical joins (priors, asset evolution); use the TSE CSVs/API for the live 2026 snapshot.

### Access

Python package (`pip install basedosdados`) — <https://pypi.org/project/basedosdados/>:
```python
import basedosdados as bd
bd.list_dataset_tables(dataset_id="br_tse_eleicoes")
df = bd.read_sql(
    "SELECT ano, sigla_uf, cargo, sequencial, nome, cpf, situacao "
    "FROM `basedosdados.br_tse_eleicoes.candidatos` WHERE ano = 2022 AND cargo = 'presidente'",
    billing_project_id="YOUR_GCP_PROJECT")
```
Or query `basedosdados.br_tse_eleicoes.*` directly in the BigQuery console (you pay only BigQuery query costs; the data is a free public dataset). Requires a Google Cloud project for billing/credentials.

**Concrete query concept — asset evolution + financing mix per candidate:**
```sql
WITH bens AS (
  SELECT cpf, ano, SUM(valor) AS patrimonio
  FROM `basedosdados.br_tse_eleicoes.bens_candidato`
  GROUP BY cpf, ano),
fin AS (
  SELECT cpf_candidato AS cpf, ano,
         SUM(valor) AS total_receita,
         SUM(IF(fonte_receita IN ('Fundo Partidário','FEFC'), valor, 0)) AS publico
  FROM `basedosdados.br_tse_eleicoes.receitas_candidatos`
  GROUP BY cpf_candidato, ano)
SELECT b.cpf, b.ano, b.patrimonio,
       SAFE_DIVIDE(b.patrimonio,
         LAG(b.patrimonio) OVER (PARTITION BY b.cpf ORDER BY b.ano)) AS cresc_patrimonio,
       SAFE_DIVIDE(f.publico, f.total_receita) AS dependencia_fundo_publico
FROM bens b LEFT JOIN fin f USING (cpf, ano)
ORDER BY cresc_patrimonio DESC;
```

---

## 3. Other candidate-screening / background sources

| Source | What it offers | URL |
|---|---|---|
| **Ranking dos Políticos** | Civil-society scoring of sitting deputies/senators (votes on key bills, attendance, integrity flags). Great for *incumbents* running for reelection. CGU-recognized OSC. No public REST API documented; scrape/UI. | <https://www.politicos.org.br/> · <https://politicos.org.br/Ranking> · methodology <https://politicos.org.br/Analises> · CGU page <https://www.gov.br/cgu/pt-br/governo-aberto/iniciativas-de-governo-aberto/organizacoes-da-sociedade-civil/de-a-a-z/ranking-dos-politicos> |
| **Brasil.io – eleicoes-brasil** | Normalized TSE candidate data via REST + bulk download. Tables: `candidatos`, `bens_candidatos`, `filiados`, `votacoes`. **⚠️ Snapshot is stale (≈2018) — do not rely on it for 2026.** Useful as a worked example of a normalized schema. | dataset <https://brasil.io/dataset/eleicoes-brasil/candidatos/> · API `https://brasil.io/api/v1/dataset/eleicoes-brasil/` · how-to <https://blog.brasil.io/2020/10/10/como-acessar-os-dados-do-brasil-io/> |
| **CNJ DataJud – API Pública** | National judicial process metadata (>80M processos, all courts), Elasticsearch DSL, free public key. Key integrity-enrichment source for criminal/civil background by name/CPF. Respects sigilo rules (Portaria 160/2020). | <https://www.cnj.jus.br/sistemas/datajud/api-publica/> · wiki <https://datajud-wiki.cnj.jus.br/api-publica/> · access/key <https://datajud-wiki.cnj.jus.br/api-publica/acesso/> |
| **Portal da Classe Política (INCT-ReDem / UFPR)** | Consolidated, visualized TSE data for 2.8M candidacies 1998–2024; R package + API "planned". Good for historical context. | (announced 2026; search "Portal da Classe Política UFPR") |
| **JOTA** | Legal/political analysis + JOTA Info data products on Congress and courts (some paid/API). Editorial, not a primary dataset. | <https://www.jota.info/> |
| **Congresso em Foco** | Journalism + accountability tracking of parliamentarians; useful for reputational flags on incumbents. | <https://congressoemfoco.uol.com.br/> |
| **olhoneles/politicos** (open source) | "API com todos os candidatos brasileiros" — community project built on TSE data; reference implementation. | <https://github.com/olhoneles/politicos> |
| **TSE news on DivulgaCandContas** | Official explainer of how to read arrecadações/gastos. | <https://www.tse.jus.br/comunicacao/noticias/2022/Agosto/divulgacandcontas-consulte-arrecadacoes-e-gastos-de-campanhas-nas-eleicoes-2022> |

There is **no single official "ficha limpa list"** dataset — "ficha limpa" status is derived (see §1.3). The authoritative ineligibility signal is the TSE candidacy status + LC 64/90 motive flags, optionally enriched with CNJ DataJud and TCU/TCE rejected-accounts lists.

---

## 4. Candidate-evaluation recipe (initial screening / scoring)

Build a per-candidate record keyed by **CPF** (stable across cycles), enriched per election by **`SQ_CANDIDATO`**.

**Pipeline**
1. **Ingest (live, Aug–Oct 2026):** daily pull of TSE bulk CSVs (`consulta_cand`, `bem_candidato`, `receitas/despesas`, `motivo_cassacao`) + DivulgaCandContas API for the rich per-candidate fields (motive flags, `arquivos`/government plan, `eleicoesAnteriores`).
2. **Historicize:** join prior cycles from Base dos Dados (`basedosdados.br_tse_eleicoes.*`) on CPF for asset evolution and repeat-candidacy context.
3. **Enrich integrity:** query CNJ DataJud by name/CPF for non-electoral processes; pull Ranking dos Políticos / Congresso em Foco flags for incumbents.

**Scoring dimensions (0–100 sub-scores → weighted index)**
- **Eligibility/Integrity (gate + score):** hard gate on `Indeferido`/`Cassado`; penalize any `st_MOTIVO_*` true, `processosCassacao` present, prior `Desaprovada` accounts, relevant DataJud processes.
- **Transparency:** has government plan filed (`arquivos` with plan `codTipo`), declared social media, complete asset declaration, on-time finance reports. Reward completeness.
- **Asset plausibility:** flag year-over-year patrimônio growth above a threshold (e.g. >2× real growth between cycles) unexplained by declared occupation/income.
- **Financing independence:** lower dependence on FEFC/Fundo Partidário is *neutral-to-positive*; high donor concentration (top-1 donor share, HHI) and triangulated money are negative; high self-funding flagged separately (wealth signal).
- **Track record (incumbents):** fold in Ranking dos Políticos score and attendance/vote alignment (from the legislative-API report).

Surface each sub-score with its **source links** (TSE detail page, DataJud, finance report) so the app stays explainable and auditable — critical for a voting-advice tool's credibility. Treat derived "ficha limpa" and asset-jump flags as *signals to display with evidence*, never as unqualified verdicts.

---

## Appendix — quick-reference base URLs
- TSE open data portal: `https://dadosabertos.tse.jus.br/`
- TSE bulk file CDN root: `https://cdn.tse.jus.br/estatistica/sead/odsele/`
- DivulgaCandContas API: `https://divulgacandcontas.tse.jus.br/divulga/rest/v1`
- DivulgaCandContas frontend: `https://divulgacandcontas.tse.jus.br/divulga/`
- API docs (unofficial): `https://github.com/augusto-herrmann/divulgacandcontas-doc`
- Base dos Dados: `basedosdados.br_tse_eleicoes.*` (BigQuery) / `https://basedosdados.org/dataset/br-tse-eleicoes`
- CNJ DataJud API: `https://www.cnj.jus.br/sistemas/datajud/api-publica/`
