# Blocked-Bill Discovery — "laws on my theme that are being blocked"

**Design:** [`research/10-blocked-bill-discovery.md`](../../research/10-blocked-bill-discovery.md)
(classifier, four tabs, who-layer, live/ETL split). **API gotchas:** `research/08`.
**Status:** backlog — design approved & committed (958ea47); implementation not started.

Surface the bills on a theme that *stalled* (never reached a nominal roll-call), classify **why**,
rank by **proximity to a vote**, and name **who is blocking**. Mirror image of `research/09` step 4.

```
Blocked(theme) = AllBills(theme, window) − Voted(theme) − BecameLaw(theme)
              → classify() via one /proposicoes/{id} detail call
              → {state: alive|dead, rung | deathReason, organ, daysStalled}
```

## Acceptance criteria

### Classifier engine (shared by all tabs)
- [ ] `classify(bill)` reads `/proposicoes/{id}` → `statusProposicao.codSituacao` and returns
      `{state, rung | deathReason, siglaOrgao, daysStalled}` (research/10 §3).
- [ ] Momentum-ladder code map (§3a) implemented: untouched ▰▱▱▱▱ → awaiting Ordem do Dia ▰▰▰▰▱.
- [ ] Dead/terminal code map (§3b) implemented: 📁 arquivada · ✋ retirada · ⊘ prejudicada · ✕ recusada.
- [ ] `null` codSituacao treated as the untouched rung (not an error).
- [ ] Terminal-success codes (virou lei / sanção / vetado) excluded from `Blocked` (§3c).
- [ ] **Tune the code→rung map against sampled live bills per `codSituacao`** before trusting it
      (research/10 §7.1 — the one interpretive step).

### Bill universe & set math
- [ ] `AllBills(theme, window)` pages `/proposicoes?codTema=…&dataApresentacaoInicio=…` (explicit
      window — list defaults to a recent slice; `idLegislatura` does not filter — research/08).
- [ ] `Blocked = AllBills − Voted(theme) − BecameLaw(theme)`, reusing the `Voted` set from research/09 step 4.

### The four tabs (filters/sorts over the classified set — research/10 §4)
- [ ] **Tab A — Has momentum:** `alive AND rung ≥ ▰▰▱▱▱`; sort rung desc, then daysStalled desc.
- [ ] **Tab B — Everything stalled:** `alive`, no floor; same sort (untouched sinks to bottom).
- [ ] **Tab C — Current legislatura:** Tab B windowed to `dataApresentacaoInicio=2023-02-01`.
- [ ] **Tab D — Dead/terminal:** `state == dead`, grouped by death reason, then date desc.

### "Who is blocking it" (lazy, on row-expand — research/10 §5)
- [ ] Current relator + party from `/proposicoes/{id}/tramitacoes` (NOT `/relatores` — returns empty).
- [ ] Current órgão (`siglaOrgao`) + its president from `/orgaos/{idOrgao}/membros`.
- [ ] Urgência-approved detection from tramitação → sets the ▰▰▰▰▱⁺ rung.

### Delivery (live-lazy first — research/10 §6a)
- [ ] Wire into `app/` (server proxy + frontend). Classify a bounded slice (top N newest) live.
- [ ] **No silent truncation:** show "classified top N of M — full coverage needs the precompute".
- [ ] Document the ETL precompute path (§6b) as the scale follow-up (separate backlog task).

### Process
- [ ] Convert design → implementation plan (writing-plans) before coding.
- [ ] User review of `research/10` confirmed.
</content>
