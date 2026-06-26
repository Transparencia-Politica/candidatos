# POC — Candidate Scoring: Wealth ⨯ Taxation Votes (Luciano Bivar)

A one-candidate proof-of-concept joining **TSE declared assets** to **Câmara roll-call votes**
to test the "interest-alignment" idea: does a legislator's personal financial interest line up
with how they vote on taxing that kind of wealth? All data pulled live from open APIs on
2026-06-26; every call is reproducible (see §5).

> **Honest framing:** with n=1 this is **not** a statistical correlation — it's an
> *interest-alignment check* and a **plumbing test** for the join (TSE `bens` ↔ Câmara `votos`).
> It is a compelling narrative demo, but conclusions about intent must stay cautious.

---

## 1. Subject

| Field | Value | Source |
|---|---|---|
| Name | Luciano Caldas Bivar | Câmara id **74478** / TSE SQ **170001609112** |
| Party / UF | MDB / PE | Câmara |
| Born / occupation | 1944 · **Empresário** (businessman) | Câmara / TSE |
| 2022 status | Eleito (por média); ficha-limpa flag clean; apto | TSE DivulgaCandContas |

## 2. Wealth profile (TSE 2022 declared assets)

**Total declared: R$ 18,621,585.46 across 24 items — ~93% capital (equities).**

| Asset type | Approx. value |
|---|---|
| Ações (shares) — 17 holdings, largest 3 = R$ 8.69M / 4.66M / 3.04M | **~R$ 17.3M** |
| Dinheiro em espécie (cash) | R$ 100,000 |
| **Depósito bancário no exterior (offshore deposit)** | R$ 85,504 |
| Caderneta de poupança / renda fixa / contas | ~R$ 140,000 |

→ His wealth is almost entirely **capital** (shares + an offshore deposit), so the bills that
*touch his interest* are those taxing **capital income, dividends, exclusive funds, and offshore
assets** — not consumption taxes.

## 3. Voting record on the relevant bills (Câmara roll-calls)

### PL 4173/2023 — taxing income from offshore entities & exclusive funds  ← most on-point
*"Dispõe sobre a tributação da renda auferida por pessoas físicas residentes no País [no
exterior / fundos]."* Directly taxes the kind of wealth Bivar holds (offshore deposit + funds).

- **Bivar was ABSENT from every recorded roll-call on this bill** (8 nominal votes on
  2023-10-25, incl. the substitutive's approval — 430–444 deputies voting each time; he appears
  in none).
- This is the cleanest result of the POC — and exactly the **missing-data** problem the VAA
  literature and the Questão Pública case flagged (doc 05/06): on the vote most aligned to his
  personal interest, there is **no recorded position**.
- ⚠️ Absence ≠ proven intent (could be leave/travel). Report it as *no recorded vote*, not "dodge".

### PEC 45/2019 — Reforma Tributária (consumption-tax overhaul, IBS/CBS)
- Voted **Sim** on the substantive passages: 1st-turn substitutive (votacao 2196833-326),
  the aglutinative amendment (…-328), and **2nd-turn approval** (…-373). → **Supported the
  reform.**
- Mixed Sim/Não on individual *destaques* (procedural amendments) — uninterpretable without each
  destaque's content and the party *orientação* (see §6).
- **Caveat:** PEC 45 reforms **consumption** taxes, not wealth/capital — so it is a *weak* proxy
  for personal-wealth interest. Supporting it says little about his stance on taxing his own
  capital.

### PL 2337/2021 — Imposto de Renda reform (incl. taxing dividends)
- Only two amendment (emenda) votes captured: voted **Sim** to Emenda 39 (rejected) and **Não**
  to Emenda 106 (rejected). The main passage was not a captured nominal vote.
- → **Position unclear** from available roll-calls.

## 4. Verdict of the POC

**The pipeline works and the story is real, but it surfaces the method's traps immediately:**

1. ✅ **Join succeeds.** We matched one person across two independent systems (TSE by SQ/UF,
   Câmara by deputy id) and pulled assets + itemized votes with open, key-less APIs.
2. ✅ **The narrative lands.** A businessman with ~R$17M in shares + an offshore deposit has **no
   recorded vote on the bill taxing offshore/fund wealth**, while supporting the (consumption-
   tax) reform that doesn't touch his capital.
3. ⚠️ **But the honest signal is thin and trap-laden:**
   - **Bill selection is everything.** PEC 45 (the famous "tax reform") is the *wrong* proxy;
     the right bills (PL 4173, PL 2337) are exactly where data is **absent or ambiguous**.
   - **Absence is the dominant outcome**, and absence is ambiguous (the literature's missing-data
     problem, live).
   - **Destaque votes are uninterpretable** without each amendment's content + the party line
     (`/orientacoes`).
   - **n=1**: no correlation, only an anecdote.

**Conclusion:** keep the POC as a *demo and a schema validator*, not as scoring evidence. To make
it a real signal it must scale to many legislators and encode each vote's **direction relative to
a thesis** (per doc 06: you cannot read raw Sim/Não without knowing what "yes" means on that
amendment).

## 5. Reproducible API calls

```bash
# Profile
curl -H "Accept: application/json" \
  "https://dadosabertos.camara.leg.br/api/v2/deputados/74478"

# TSE: find SQ_CANDIDATO (PE, 2022 general = idEleicao 2040602022, cargo 6 = Dep. Federal)
curl -A "Mozilla/5.0" -H "Accept: application/json" -H "Referer: https://divulgacandcontas.tse.jus.br/" \
  "https://divulgacandcontas.tse.jus.br/divulga/rest/v1/candidatura/listar/2022/PE/2040602022/6/candidatos"

# TSE: candidate detail incl. `bens` + `totalDeBens`  (note route order: ano/UF/idEleicao/candidato/SQ)
curl -A "Mozilla/5.0" -H "Accept: application/json" -H "Referer: https://divulgacandcontas.tse.jus.br/" \
  "https://divulgacandcontas.tse.jus.br/divulga/rest/v1/candidatura/buscar/2022/PE/2040602022/candidato/170001609112"

# Câmara: a bill's roll-calls, then the full vote list (one call = entire roll-call, NOT paginated)
curl -H "Accept: application/json" "https://dadosabertos.camara.leg.br/api/v2/proposicoes?siglaTipo=PL&numero=4173&ano=2023"
curl -H "Accept: application/json" "https://dadosabertos.camara.leg.br/api/v2/proposicoes/2383287/votacoes"
curl -H "Accept: application/json" "https://dadosabertos.camara.leg.br/api/v2/votacoes/2383287-43/votos"
```

Bill → proposition ids used: PL 4173/2023 = **2383287**, PEC 45/2019 = **2196833**,
PL 2337/2021 = **2288389**.

## 6. To turn this POC into a real score (next steps)

1. **Add `/votacoes/{id}/orientacoes`** — the Governo/Oposição/party line per vote, to interpret
   each *destaque* (what "Sim" means).
2. **Hand-code each signature vote's direction relative to a thesis** (+1 pro-thesis / −1 anti),
   per doc 06 — only then can votes be summed.
3. **Curate a small set of "signature wealth-tax votes"** (PL 4173 final, PL 2337 dividends
   destaques, any future IGF/dividend bills) rather than scanning all roll-calls.
4. **Model absence explicitly** (attendance signal) instead of dropping it — Bivar's absence is
   itself information.
5. **Scale to all incumbents** and only then compute alignment statistics (n≫1).
