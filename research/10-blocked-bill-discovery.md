# Blocked-Bill Discovery — Surfacing the Laws That *Didn't* Get Voted

*Compiled 2026-06-27. The mirror image of [`09-topic-to-law-discovery.md`](09-topic-to-law-discovery.md):
where 09 step 4 **discards** every bill that never reached a nominal roll-call, this report
**keeps** them — the bills on a theme that stalled — classifies **why** they stalled, ranks them
by **how close they got to a vote**, and names **who is sitting on them**. API shapes verified live
2026-06-27 against the Câmara Dados Abertos API.*

> **Why this exists:** a citizen cares about a theme (e.g. *meio ambiente*) and wants to see not
> just how deputies voted, but the bills on that theme that are **being blocked** — stuck in
> committee, archived, awaiting an Ordem-do-Dia slot, or quietly killed. The voted bills feed the
> scorecard; the *unvoted* ones feed accountability. `Blocked(theme) = AllBills(theme) − Voted(theme) − BecameLaw(theme)`.

---

## 1. The answer in one line

**A bill's stall reason and proximity to a vote are fully recoverable from its `codSituacao`
(situação code) plus its `/tramitacoes` history — but neither is in the `/proposicoes` *list*, so
classification is a per-bill detail call. Build one `classify(bill)` engine, then expose the four
tabs as filters/sorts over its output.**

---

## 2. Verified API reality (this is what forces the design) ✅/❌

All checked live 2026-06-27, theme `48` (Meio Ambiente e Desenvolvimento Sustentável):

| # | Finding | Status | Consequence |
|---|---|---|---|
| 1 | `/proposicoes` **list** rows = `{id, uri, siglaTipo, codTipo, numero, ano, ementa, dataApresentacao}` — **no `statusProposicao`, no `keywords`** | ✅ verified | Can't classify from the list. Same list-vs-detail trap doc 08 records for TSE. |
| 2 | `?codSituacao=923` and `?codSituacao=1140` return the **same 1319 total and identical rows** as no filter | ✅ verified | **`codSituacao` is silently ignored.** No cheap server-side status query. Classification = per-bill detail (N+1). |
| 3 | `?idLegislatura=57` → **0 rows** | ✅ verified | Not a valid window. Use date/`ano` params instead. |
| 4 | No window → 1319 rows; `?ano=2024&ano=2025&ano=2026` → 3489; `?dataApresentacaoInicio=2023-02-01` → 4466 | ✅ verified | `/proposicoes` **defaults to a recent window**; pass an explicit `ano`/`dataApresentacaoInicio` to reach the historical corpus. |
| 5 | `/proposicoes/{id}` detail → `statusProposicao` = `{codSituacao, descricaoSituacao, siglaOrgao, descricaoTramitacao, despacho, regime, dataHora}`. Brand-new bills have `codSituacao: null` (only an "Apresentação de Proposição" tramitação) | ✅ verified | The detail call **is** the classifier input. `null` situação = the untouched rung. |
| 6 | `/referencias/proposicoes/codSituacao` = **99 codes** (the controlled situação vocabulary) | ✅ verified | The precise classifier — map codes to rungs/death-reasons, don't parse prose. |
| 7 | `/proposicoes/{id}/relatores` → **0 rows** for a reported bill (PEC 45) | ⚠️ verified empty | Don't rely on this sub-resource for the "who". Parse the relator-designation event out of `/tramitacoes`. |

**Net:** there is no one-call classification. The shared cost is one `/proposicoes/{id}` detail per
bill. That draws the live/ETL line precisely (§6).

---

## 3. The classifier — `classify(bill) → {state, rung | deathReason, organ, since}`

Input: the bill's `statusProposicao` (one detail call) + membership in `Voted(theme)` (reuse
09 step 4). Output: one of three states.

### 3a. Momentum ladder (alive, stalled — *ranked* by proximity to a nominal vote)

| Rung | Meaning | `codSituacao` (verified vocab names) |
|---|---|---|
| ▰▱▱▱▱ | **Submitted, untouched** — no relator yet | `null` (only "Apresentação"), `906` Aguardando Distribuição, `907` Aguardando Designação de Relator(a) |
| ▰▰▱▱▱ | **Has relator, no parecer** — awaiting the report | `915` Aguardando Parecer, `1380` Aguardando Elaboração do Parecer pelo Relator, `1295` Aguardando Reformulação de Parecer, `928` Aguardando Análise de Parecer, `1297`/`1300` Parecer da Comissão Especial |
| ▰▰▰▱▱ | **Reported / moving between comissões** | `903` Aguardando Deliberação (in a committee), `1280` Comissão em funcionamento, `922` Aguardando Vistas, `925` Tramitando em Conjunto |
| ▰▰▰▰▱ | **Cleared committees, awaiting Ordem do Dia** — needs scheduling | `924` Pronta para Pauta, `903` Aguardando Deliberação when `siglaOrgao ∈ {PLEN, MESA}` |
| ▰▰▰▰▱⁺ | **Urgência approved, still unscheduled** — strictly closer | *not a situação code* → requires a `/tramitacoes` scan for an approved *requerimento de urgência*; resolved on expand/ETL, never in the list pass |
| ▰▰▰▰▰ | *(reached a nominal roll-call)* | **leaves this list** — it's in `Voted(theme)`, the scorecard set |

### 3b. Dead / terminal (shown in Tab D — *not* momentum-ranked)

| Mark | Reason | Source |
|---|---|---|
| 📁 | **Arquivada** (fim de legislatura / despacho) | `923` Arquivada, `930` Enviada ao Arquivo, `914`/`931`/`940` archive-pending |
| ✋ | **Retirada pelo autor** / devolvida | `950` Retirado pelo(a) Autor(a), `1120` Devolvida ao(à) Autor(a) |
| ⊘ | **Prejudicada / perdeu eficácia** | `1222` Prejudicialidade, `920` Aguardando Deliberação sobre Prejudicialidade, `1292` Perdeu a Eficácia |
| ✕ | **Rejeitada / recusada** | `941` Recusado |
| 🔇 | **Resolved by votação simbólica** — passed with no individual record | bill has a `/votacoes` entry but **empty `/votos`** (doc 08) — detected from votações, not `codSituacao` |

### 3c. Excluded from "blocked" entirely (terminal *success*)

`1140` Transformado em Norma Jurídica, `1150` Aguardando Sanção, `1160` Aguardando Remessa à Sanção,
`937` Vetado totalmente, `1285` Tramitação Finalizada — these reached an outcome; they are not blocked.

> **Mapping caveat (per AGENTS.md "don't invent"):** the 99 situação *names* are verified live
> (#6). The *assignment* of each code to a rung above is interpretation of its Portuguese name and
> should be **tuned against a sample of live bills per code** before the ETL is trusted — treat
> §3a/§3b as the classifier's initial table, refined empirically, not a verified behavior claim.

---

## 4. The four tabs — each is a filter+sort over `classify`-d `Blocked(theme)`

There is **one** pipeline. The tabs are views; they do **not** re-query differently.

```
Blocked(theme) = AllBills(theme, window) − Voted(theme) − BecameLaw(theme)
   then classify() each → {state, rung|deathReason, organ, since}
```

| Tab | Predicate over classified set | Sort | Notes |
|---|---|---|---|
| **A — Has momentum** | `state == alive AND rung ≥ ▰▰▱▱▱` (relator assigned or beyond — excludes `null`/`906`/`907`) | rung desc, then `daysStalled` desc | The high-signal list. Hides the dead long tail of untouched drafts. |
| **B — Everything stalled, ranked** | `state == alive` (no rung floor) | rung desc, then `daysStalled` desc | Untouched drafts sink to the bottom via the rung sort. The complete in-progress picture. |
| **C — Current legislatura** | Tab B, but `AllBills` windowed to `dataApresentacaoInicio = 2023-02-01` (57ª legislatura) | rung desc, then `daysStalled` desc | A narrower `window` on the same pipeline — **not** a different classifier. |
| **D — Dead / terminal** | `state == dead` | grouped by `deathReason` (📁✋⊘✕🔇), then `since` desc | Where bills go to die. Answers "what got killed and how". |

- `daysStalled` = `now − statusProposicao.dataHora` (time in the current situação). From detail/ETL.
- Tabs A and C are just **filter axes** over B (a rung floor and a date window). One engine, four lenses.

---

## 5. The "who is blocking it" layer (lazy, on row-expand)

Attached only when a user expands a row — never in the list pass.

| Field | How | Caveat |
|---|---|---|
| **Current relator + party** | scan `/proposicoes/{id}/tramitacoes` for the *Designação de Relator(a)* event; take the latest | `/relatores` sub-resource returned empty (#7) — use tramitações |
| **Current órgão** | `statusProposicao.siglaOrgao` (e.g. CCJ, CFT, PLEN) | already in the detail call |
| **Órgão president** | `/orgaos/{idOrgao}/membros` → member with the *Presidente* role | the actor who controls scheduling in that committee |
| **Urgência filed?** | scan `/tramitacoes` for an approved *requerimento de urgência* | also sets the ▰▰▰▰▱⁺ rung |

This is the accountability payload: the relator who never reported, the committee president who
never put it on the pauta. It ties back to the scorecard — a deputy who buries theme bills.

---

## 6. Two implementation modes (the live/ETL line)

Classification costs **one detail call per bill**, and a windowed theme has thousands of bills
(#4). So:

### 6a. Live-lazy — ship now, in the existing `app/` POC
- `AllBills(theme, window)`: 1 paginated `/proposicoes?codTema=…&dataApresentacaoInicio=…` call → ids + ementa.
- Classify only a **bounded slice** (e.g. the first N = 30–50 bills, newest first) via per-bill
  detail — because `codSituacao` is not in the list (#2) and detail is N+1.
- Tabs A/B/C/D operate over that classified slice.
- **No silent truncation:** show "*classified top N of M bills on this theme — full coverage needs
  the precompute*". Honesty over a fake-complete list (AGENTS.md: don't invent; don't imply coverage).
- "Who" layer fetched lazily on expand. Matches the proxy+browser architecture of `app/server.py`.

### 6b. ETL precompute — the scale path (research/09 §6.3 territory)
- Nightly sweep: for each `codTema`, fully page `AllBills(theme, window)`, call detail per bill
  (rate-limit ≥0.3–1s, real User-Agent — doc 08), store `{id, codSituacao, rung, deathReason,
  siglaOrgao, since, votedFlag}` to a per-theme JSON.
- App reads JSON → **all four tabs are instant over the full corpus**. This is the **only** way
  Tab B ("everything") and the `daysStalled` ranking are honest at scale.
- Reuse the `Voted(theme)` set already computed for scoring (09 step 4) — `Blocked` is its complement.

**Decision:** build 6a now (live, bounded, honest banner); the app stays as light as the current
POC. 6b is documented here and ready when live calls are outgrown.

---

## 7. Open items to verify before/while building
1. **Tune the §3 code→rung map** against sampled live bills per `codSituacao` (the one interpretive
   step). Especially `903` (committee vs plenary split on `siglaOrgao`).
2. **`/orgaos/{id}/membros` president role label** — confirm the exact role string for "Presidente".
3. **`daysStalled` source field** — confirm `statusProposicao.dataHora` is the *entry into current
   situação*, not the last-touched timestamp.
4. **Symbolic-vote (🔇) detection cost** — it needs a `/votacoes` + `/votos` check per bill; fold it
   into the ETL, not the live pass.

## 8. Sources
- Câmara API — `/proposicoes`, `/proposicoes/{id}`, `/referencias/proposicoes/codSituacao`,
  `/proposicoes/{id}/relatores`, `/proposicoes/{id}/tramitacoes` — **verified live 2026-06-27** (§2).
- [`09-topic-to-law-discovery.md`](09-topic-to-law-discovery.md) — the topic→bill pipeline whose
  step 4 this report inverts; `Voted(theme)` reuse.
- [`08-api-field-notes.md`](08-api-field-notes.md) — list-vs-detail trap, symbolic-vote empty
  `/votos`, rate-limit etiquette. New gotchas from §2 appended there.
</content>
</invoke>
