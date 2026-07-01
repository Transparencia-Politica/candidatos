# Wealth-Tax Signature Vote Package

*Curated package note for the current `tributacao-da-riqueza` scoring theme. Compiled on
2026-07-01 from the local seed in `app/db.py`, the scoring tracker in `research/16`, and the
earlier POC findings in `research/07`. This note documents curation choices; it did not perform a
new live API audit.*

This package is the first maintained example of the project protocol:

```text
theme -> curated laws -> keyword directions -> weights -> cached roll-calls -> scorecard
```

The purpose is to keep the wealth-tax score explainable. Each law included here must answer one
question: does a recorded vote reveal something useful about taxing concentrated wealth, capital
income, offshore wealth, exclusive funds, dividends, or large fortunes?

---

## Inclusion rules

A law belongs in the **signature package** when all of these are true:

- It directly affects taxation of wealth, capital income, high incomes, offshore assets, exclusive
  funds, dividends, or large fortunes.
- It can be connected to nominal roll-calls through the Câmara / Senado cache.
- A `Sim` / `Não` direction can be stated in plain language.
- The law is more than general tax context: it has a concrete relationship to concentration of
  wealth or capital-income taxation.

A law belongs in **context only** when it is fiscally important but does not directly measure
wealth taxation. Context laws may still render in the UI, but they should use `direction = 0`,
`wealth_relevant = 0`, and a low weight.

---

## Current package

| Role | Law / seed slug | Keyword(s) | Direction | Weight tier | Why it belongs |
|---|---|---|---|---|---|
| Core | `igf-grandes-fortunas` / PLP 108/2024 highlight | `igf-patrimonio` | `Sim` = favors taxing large fortunes | very high | Direct annual tax on wealth above R$ 10M; this is the clearest wealth-stock signal in the seed. Source URL stored in seed: <https://dadosabertos.camara.leg.br/api/v2/proposicoes/2438459>. |
| Core | `pl-4173-2023` | `offshore`, `fundos-exclusivos` | `Sim` = favors taxing offshore income / exclusive funds | very high | Directly targets offshore structures and exclusive funds, both central to high-wealth tax avoidance. Source URL stored in seed: <https://dadosabertos.camara.leg.br/api/v2/proposicoes/2383287>. |
| Core | `pl-1087-2025` | `imposto-minimo-super-ricos` | `Sim` = favors minimum taxation of high incomes / capital distributions | very high | Adds a minimum tax on high incomes and taxes large monthly profit/dividend flows. Source URL stored in seed: <https://dadosabertos.camara.leg.br/api/v2/proposicoes/2487436>. |
| Supporting | `pl-2337-2021` | `dividendos` | `Sim` = favors taxing distributed profits / dividends | high | Dividend taxation is directly relevant to capital-income taxation, but this bill package is broader and older than the core set. Source URL stored in seed: <https://dadosabertos.camara.leg.br/api/v2/proposicoes/2288389>. |
| Context | `pec-45-2019` | `tributacao-do-consumo` | `direction = 0` | context | Consumption-tax reform is important fiscal context, but it does not directly measure wealth, capital income, or large-fortune taxation. Source URL stored in seed: <https://dadosabertos.camara.leg.br/api/v2/proposicoes/2196833>. |

---

## Scoring contract

The current scoring contract after tracker items 1-7:

- `Sim` / `Não` on directional wealth-tax laws affect `pro_redistribution_score`.
- The score is weighted by the curated keyword tier.
- A multi-keyword law contributes once at law level; keywords remain visible as explanations.
- `self_interest_alignment_score` is separate from redistribution and only appears when declared
  assets overlap the affected tax base.
- `Abstenção`, `Obstrução`, and `Artigo 17` are recorded neutral evidence.
- `AUSENTE` and `sem votação nominal` affect coverage/confidence, not the policy score.
- Context laws remain visible but do not move wealth-tax scores.

---

## Maintenance checklist

When adding or changing a wealth-tax law:

1. Add or update the seed in `app/db.py`.
2. Assign a role: core, supporting, or context.
3. Add one or more keywords with `direction`, `weight`, and `wealth_relevant`.
4. Document the law in this package table with the source URL stored in the seed.
5. Update `tests/test_topic_config.py` so the package composition is intentional.
6. Rebuild cached votes / scorecards as needed, then run `python3 app/snapshot.py site`.

This package is not meant to be large. It is meant to be legible, auditable, and strong enough that
each included vote can be defended in public.
