# Perfis dos pré-candidatos à Presidência 2026 — dados do TSE

> **Documentos standalone, não integrados ao modelo de scoring por votos.**
> Estes perfis foram montados a partir do **TSE DivulgaCand**. Os candidatos à Presidência
> não votam no Congresso, portanto **não entram no pipeline de roll-calls** (`ingest`/`score_candidate`).
> Dados estruturados brutos: [`perfis-precandidatos-2026.data.json`](perfis-precandidatos-2026.data.json).
>
> ⚠️ **Sobre o patrimônio:** cada valor é a **declaração de bens de uma eleição passada** (não é
> patrimônio atual e não existe declaração de 2026 antes do registro, em agosto/2026). Os valores
> vêm de eleições/anos/cargos diferentes e **não são diretamente comparáveis** (inflação, lapso
> temporal, cargos distintos). Cada figura está rotulada com o ano e o cargo de origem.

## Cobertura (honesta)

**Com perfil montado (4):** Lula, Ronaldo Caiado, Romeu Zema, Samara Martins.

**Excluídos por falta de dado no DivulgaCand:**

| Pré-candidato | Motivo |
|---|---|
| Flávio Bolsonaro (PL) | Última candidatura em **2018** (senador). O endpoint `listar/2018/.../5` retorna vazio para todos os códigos testados (ver `research/14`). |
| Cabo Daciolo (Mobiliza) | Concorreu à Presidência em **2018**; mesma limitação da API para 2018. |
| Joaquim Barbosa (DC) | Nunca disputou cargo eletivo → sem candidatura no TSE → sem declaração. |
| Augusto Cury (Avante) | Nunca disputou cargo eletivo → sem declaração. |
| Renan Santos (Missão) | Primeira candidatura → sem declaração até o registro (ago/2026). |
| Edmilson Costa (PCB) / Hertz Dias (PSTU) / Rui Costa Pimenta (PCO) | Sem candidatura recente resolvível no DivulgaCand (PCB/PSTU lançaram outros nomes em 2022; candidaturas antigas têm cobertura irregular no REST). |

---

## Luiz Inácio Lula da Silva (PT)

- **Origem do dado:** Presidente — eleição 2022 (BR), SQ `280001607829`
- **Nome completo:** Luiz Inácio Lula da Silva · **Nascimento:** 06/10/1945, Garanhuns/PE
- **Ocupação declarada:** Torneiro Mecânico · **Instrução:** Ensino Fundamental completo
- **Coligação (2022):** Coligação Brasil da Esperança
- **Patrimônio declarado (2022, Presidente):** **R$ 7.423.725,78** — 23 bens
  - Ações / participações: R$ 49.333,17
  - Poupança / renda fixa / contas: R$ 211.326,26
  - Outros: R$ 7.163.066,35
- [Fonte TSE](https://divulgacandcontas.tse.jus.br/divulga/rest/v1/candidatura/buscar/2022/BR/2040602022/candidato/280001607829)

## Ronaldo Caiado (PSD/União)

- **Origem do dado:** Governador (GO) — eleição 2022, SQ `90001646326`
- **Nome completo:** Ronaldo Ramos Caiado · **Nascimento:** 25/09/1949, Anápolis/GO
- **Ocupação declarada:** Médico · **Instrução:** Superior completo
- **Coligação (2022):** Pra Seguir em Frente
- **Patrimônio declarado (2022, Governador):** **R$ 24.874.436,19** — 53 bens
  - Ações / participações: R$ 883.475,34
  - Poupança / renda fixa / contas: R$ 71.679,88
  - Outros: R$ 23.919.280,97
- [Fonte TSE](https://divulgacandcontas.tse.jus.br/divulga/rest/v1/candidatura/buscar/2022/GO/2040602022/candidato/90001646326)

## Romeu Zema (Novo)

- **Origem do dado:** Governador (MG) — eleição 2022, SQ `130001701690`
- **Nome completo:** Romeu Zema Neto · **Nascimento:** 28/10/1964, Araxá/MG
- **Ocupação declarada:** Governador · **Instrução:** Superior completo
- **Coligação (2022):** Minas nos Trilhos
- **Patrimônio declarado (2022, Governador):** **R$ 129.795.313,70** — 16 bens
  - Ações / participações: R$ 92.942.274,81
  - Poupança / renda fixa / contas: R$ 1.386.332,58
  - Outros: R$ 35.466.706,31
- [Fonte TSE](https://divulgacandcontas.tse.jus.br/divulga/rest/v1/candidatura/buscar/2022/MG/2040602022/candidato/130001701690)

## Samara Martins (UP)

- **Origem do dado:** Vice-presidente — eleição 2022 (BR), SQ `280001602703`
- **Nome completo:** Samara Martins da Silva · **Nascimento:** 31/08/1987, Belo Horizonte/MG
- **Ocupação declarada:** Odontóloga · **Instrução:** Superior completo
- **Coligação (2022):** UP
- **Patrimônio declarado (2022, Vice-presidente):** **R$ 3.364,55** — 3 bens
  - Poupança / renda fixa / contas: R$ 3.364,55
- [Fonte TSE](https://divulgacandcontas.tse.jus.br/divulga/rest/v1/candidatura/buscar/2022/BR/2040602022/candidato/280001602703)

---

## Metodologia

- **Endpoint de lista:** `/candidatura/listar/{ano}/{UF}/2040602022/{cargo}/candidatos`
  (cargos: 1=Presidente, 2=Vice, 3=Governador, 5=Senador, 6=Dep. Federal).
- **Endpoint de detalhe (com `bens`/`totalDeBens`):** `/candidatura/buscar/{ano}/{UF}/2040602022/candidato/{SQ}`.
- Reaproveitados os helpers do app: `fetch_json`, `tse_candidates_from_response`, `fetch_tse_detail`,
  `bucketize_assets`, `br_float`, `normalize_name` (mesmo mecanismo do `score_candidate.py`).
- Cada par nome/ocupação/patrimônio foi conferido manualmente (o matcher faz fallback por substring).
- **Limite confirmado:** a eleição de **2018** retorna lista vazia no REST do DivulgaCand para todos
  os códigos testados — declarações de 2018 não são recuperáveis por esta via.
