# Candidate-Evaluation & Preference-Matching Pipeline — Design & Prior Art

Research brief for **voto-o-mat-br2026**, a Brazilian Wahl-O-Mat analog for the 2026 general election.
Focus: **methodology** and **existing products**. Raw Câmara/Senado/TSE API endpoints are covered by other agents and are deliberately omitted here.

Date: 2026-06-26.

---

## 0. Executive framing

A Brazilian VAA (Voting Advice Application) must do something harder than a German Wahl-O-Mat: Germany matches voters to a handful of **parties** under a closed/semi-open list; Brazil's general election is **open-list proportional** for the Câmara and state assemblies, so the unit the voter actually picks is an **individual candidate** among hundreds in their state. That single fact reshapes the whole pipeline — the product must rank *candidates*, not just parties, and most candidates (challengers, first-timers) have **no roll-call record at all**.

The recommended architecture is therefore a **multi-signal scoring pipeline** with clearly separated, individually normalized sub-scores — issue match, diligence, integrity, ideological proximity — combined under **transparent, user-adjustable weights**, never a single opaque blended number. The rest of this document justifies that design from prior art and political-science method.

---

## 1. Existing Brazilian tools (prior art)

### 1.1 brasil.vota.com — the closest live analog

- URL: <https://brasil.vota.com/> · Quiz: <https://brasil.vota.com/en/political-quiz> · Candidate finder: <https://brasil.vota.com/candidates/>
- **What it is:** a localized instance of the global VOTA.com voting-guide platform (also runs `portugal.vota.com`, US, etc.). Self-describes as independent, unaffiliated with parties/investors.
- **Data & method:** a self-declared **issue questionnaire**, not legislative behavior. Each question is a policy statement across categories (Governance, Economic, Social, Environmental…). User answers **Yes / No / "other stances"** plus a per-question **importance slider** ("Least → Most"). Output dashboards: *My parties*, *My ideologies*, *My ballot* (candidate matches), *My support map*. The importance slider implies a **salience-weighted proximity model** (see §2/§3) — the canonical VAA design — but the exact distance metric is not published.
- **Strengths:** broad coverage, clean UX, importance weighting, candidate-level "ballot," already operating in Brazil.
- **Limits:** positions are **stated** (self-report / editorial), not derived from votes, so it can't catch "says X, votes Y." Matching algorithm is closed/unauditable. Candidate coverage depends on candidates engaging.
- **Takeaway for us:** this is the UX bar and the obvious incumbent. Our differentiator is **grounding positions in actual roll-call behavior** for incumbents, which vota.com does not appear to do.

### 1.2 Radar Parlamentar — party/legislator similarity via PCA on roll-calls

- URLs: <https://radarparlamentar.polignu.org/> · wiki <https://ccsl.ime.usp.br/wiki/Radar_Parlamentar> · code <https://github.com/radar-parlamentar/radar> (now GitLab) · maintained by **PoliGNU** (USP).
- **Method (the important part):** for a chosen set of roll-calls in a period, build a matrix where each **party (or parliamentarian)** is a row and each **roll-call** is a column. Each vote is encoded numerically (Sim / Não, with abstention/obstruction/absence handled as intermediate/missing). **Principal Component Analysis (PCA)** then reduces this high-dimensional voting matrix to a **2-D plane**; circles = parties/legislators, **distance between circles ≈ how similarly they vote**, circle size ≈ bench size. The two axes are *emergent* (the directions of maximum variance), not pre-labeled "left/right" — though the first component usually reads as a government/opposition or ideological axis.
- **Notable property they document:** the 2-D PCA representation is *more* faithful when **fewer** votes are included for a tight period; over long windows with many votes, 2-D loses fidelity (see PoliGNU note: <https://polignu.org/en/node/666>). This is the classic dimensionality caveat (§4).
- **Coverage:** Câmara, Senado, Câmara Municipal de São Paulo; pluggable to other houses. Listed on the open-data portal: <https://dados.gov.br/aplicativo/radar-parlamentar>.
- **Takeaway:** PCA on the roll-call matrix is the cheapest credible way to produce an **ideological-proximity** signal (§3d) and a "parties like your answers" map. We can reuse this approach directly; it is unsupervised and needs no hand-coding.

### 1.3 Basômetro (Estadão Dados) — government-support index

- URLs: <http://blog.estadaodados.com/tag/basometro/> · code <https://github.com/estadao/basometro> and <https://github.com/estadaoDados/basometro>.
- **Method:** measures **governismo** — the % of nominal votes in which a deputy/party followed the **government leader's official orientation** (orientação de liderança). A pro-government vote = exactly matching the leader's indicated position (if leadership says "Sim," only "Sim" counts as support); **"Não," obstruction, and abstention all count as against**. Votes where the Executive issued **no orientation / freed the bench are discarded**, so the index is computed only over votes with an explicit government position. Uses all **nominal** votes from the Câmara open-data API since 2011.
- **Strengths:** simple, transparent, reproducible; a single interpretable axis (loyalty to government).
- **Limits:** one-dimensional (government vs not) — it is *not* an issue-position measure; binarizing abstention as "against" is an editorial choice that can distort.
- **Takeaway:** the **"orientação de liderança" join** is a reusable trick — party/government leadership orientations are published per vote and give a cheap, defensible reference direction. Useful as a *secondary* loyalty/independence signal, not as the issue-match core.
- Related live products in the same vein: Congresso em Foco's "Radar do Congresso / Governismo" (<https://radar.congressoemfoco.com.br/governismo/camara>).

### 1.4 Ranking dos Políticos — multi-axis parliamentarian scorecard (best scoring exemplar)

- URLs: <https://ranking.org.br/> · criteria <https://ranking.org.br/CriteriosAvaliacao> · methodology org page <https://olb.org.br/metodologia-do-ranking-de-parlamentares/> · Wikipedia <https://pt.wikipedia.org/wiki/Ranking_dos_Pol%C3%ADticos>. Civil-society org, founded 2011; data from Câmara, Senado, and courts.
- **Scoring formula (concrete and reusable):**

  `FINAL = BASE + BONUS − PENALTIES`, on a **0–10** scale, where BASE (max 10) =
  - **Votes (V): up to 7.5 pts (75%)** — alignment of the legislator's votes with bills scored by the org's **Conselho de Leis** (a panel of experts that assigns each bill a value against the org's pillars).
  - **Spending / cota (G): up to 1 pt (10%)**
  - **Attendance / presença (PRE): up to 1 pt (10%)**
  - **Privileges (PRI): up to 0.5 pt (5%)**

  **BONUS:** Legislative Production (PL) +0.6, Legislative Articulation (AL) +0.4.
  **PENALTIES:** Legal cases (PRO) **−0.5 per conviction**.
- **Editorial pillars (important caveat):** scoring is anchored to three "non-negotiable" pillars — **anticorrupção, antiprivilégios, antidesperdício** (fiscal-conservative/anti-waste worldview). The Conselho de Leis decides whether a given bill is "good" or "bad," so the 75% "Votes" component **encodes a political value judgment**. This is exactly the partisanship trap a neutral VAA must avoid (§4).
- **Takeaway:** great template for the **mechanics** (separate axes, explicit weights, bonus/penalty, integrity & attendance as first-class signals), but its fixed editorial scoring of bills is the thing **not** to copy if we want non-partisanship. Our equivalent of the "Conselho de Leis" judgment must be **moved to the user** (the user's quiz answers decide which side of a bill is "good"), not baked in.

### 1.5 Serenata de Amor / Rosie / Jarbas — expense-anomaly detection (integrity signal)

- URLs: <https://serenata.ai/> · Jarbas explainer <https://medium.com/data-science-brigade/jarbas-apresenta-todas-as-suspeitas-da-rob%C3%B4-rosie-da-opera%C3%A7%C3%A3o-serenata-de-amor-cd021e9be045> · Wikipedia <https://pt.wikipedia.org/wiki/Opera%C3%A7%C3%A3o_Serenata_de_Amor>.
- **Method:** **Rosie** is a Python pipeline that ingests every CEAP (Cota para Exercício da Atividade Parlamentar) reimbursement, computes a **probability of irregularity** per receipt, and emits human-readable justifications (e.g., over-priced meals, suppliers that don't exist, refuels exceeding tank capacity, expenses on non-session days). It mixes rule-based heuristics with statistical outlier detection (distance from typical price distributions for a category). **Jarbas** is the public front-end to browse those flags. Reported impact: 9,000+ suspicions, ~800 formal denúncias, ~150 reimbursements canceled.
- **Takeaway:** this is the model for an **integrity sub-signal** built from expense data. We don't need to rebuild Rosie; we can surface *whether a sitting legislator has flagged/contested CEAP spending* as one transparency input. For challengers without a mandate, this signal is simply absent (handle as missing, §2/§3).

### 1.6 Past-election candidate matchers & academic VAAs for Brazil

- **Questão Pública (2010) — the first VAA in Latin America.** Built for the **2010 Senate election** in Brazil by a consortium of Brazilian + international NGOs and universities; documented in a Springer chapter (Garzia & Marschall, eds., *Matching Voters with Parties and Candidates*, 2014): <https://link.springer.com/chapter/10.1007/978-3-642-23333-3_19>. It is the academic precedent that a candidate/party-matching VAA is feasible and was attempted in Brazil. (Full text paywalled; cite as precedent.)
- **O Globo "com qual candidato você se identifica" (2022).** A presidential matcher: 11 questions on economy/culture/health; the **same questionnaire was sent to all major candidates** to define the reference positions. Crucially, **Lula (PT) and Bolsonaro did not answer**, so the two front-runners had no profile — a textbook illustration of the candidate-non-response / missing-data failure mode (§4). Reporting: <https://costanorte.com.br/geral/quiz-mostra-com-qual-candidato-a-presidencia-voce-se-identifica-1398410.html>.
- **General finding:** no durable, candidate-level Brazilian VAA grounded in roll-call data was found beyond brasil.vota.com (questionnaire-based) and the academic Questão Pública precedent. This is the **open niche** our product fills: *votes-grounded, candidate-level, auditable, non-partisan*.

---

## 2. Turning legislative behavior into policy positions

Goal: convert an incumbent's roll-call history into a position on each **policy thesis** the quiz tests, comparable to the user's answer on that thesis.

### 2.1 The core problem the task flags — vote *direction* relative to bill content

You **cannot sum "Sim" votes**. A "Sim" means *opposite* things depending on whether the bill *advances* or *blocks* the thesis. Example thesis: *"The state should expand environmental licensing controls."* A "Sim" on a bill that **loosens** licensing is evidence **against** that thesis; a "Sim" on a bill that **tightens** it is evidence **for** it.

**Recommendation:** every roll-call used must be **hand-coded for direction** relative to each thesis it touches:

`direction d_{v,t} ∈ {+1, −1}` = "does a *Sim* on vote *v* move policy toward thesis *t* (+1) or away (−1)?"

Then a legislator's stance contribution from vote *v* is `s = vote_sign × d_{v,t}`, where `vote_sign = +1` for Sim, `−1` for Não. Average (weighted) across the votes mapped to thesis *t* to get a position in `[−1, +1]`.

This manual direction-coding is the **single most important and most labor-intensive step**, and it is precisely the thing that **distinguishes a thesis-based VAA from NOMINATE/IRT**:

| Approach | Where "direction" comes from | Pros | Cons |
|---|---|---|---|
| **Thesis-based coding (recommended for the quiz)** | Humans hand-code each bill's direction vs each thesis | Directly comparable to user answers; explainable ("voted to loosen licensing 4×") | Labor-intensive; needs editorial care to stay neutral; coverage limited to coded bills |
| **Ideal-point estimation (NOMINATE / IRT)** | *Estimated from the data* — each bill gets latent "yea-locating" parameters; no hand-coding | Unsupervised, scales to all votes, robust ideological axis | Latent axes aren't directly "your quiz issue"; harder to explain to a voter |

Use **both**: hand-coded directions for the **issue-match** signal (§3a), and an unsupervised ideal-point/PCA estimate for the **ideological-proximity** signal (§3d).

### 2.2 Handling abstentions, obstruction, and absences

Brazilian nominal votes include `Sim`, `Não`, `Abstenção`, `Obstrução`, `Art.17` (presiding), and **absence**. Recommended coding for the issue-match score:

- **Sim / Não** → `+1 / −1` (multiplied by the bill's thesis direction).
- **Abstenção / Obstrução** → treat as **partial/neutral (0)** *and* **down-weight** that vote in the average (it is a weak signal, often tactical/coalitional, not a genuine policy preference). Do **not** binarize abstention as "against" the way Basômetro does — that is an editorial choice unsuitable for a neutral issue-match.
- **Absence** → **missing data**, excluded from the legislator's denominator (don't penalize the *issue* score for it; absence belongs to the **attendance** signal §3b instead). Track it separately.
- **Coverage guard:** if a legislator has fewer than *k* coded votes on thesis *t* (e.g., k=3), mark the position **"insufficient record"** and fall back to manifesto/party signal rather than asserting a false precise position.

### 2.3 Weighting "key votes"

Not all roll-calls are equally informative. Practical weights:

- **Salience / decisiveness:** PECs, final passage, and close/contested votes carry more information than procedural or near-unanimous votes. Up-weight contested votes; **down-weight near-unanimous votes** (they don't discriminate between candidates — the IRT analog is a low-discrimination item).
- **Recency:** optionally decay older legislatures.
- **Avoid double-counting** multiple procedural votes on the same matter (e.g., destaques) — collapse to the substantive decision.

### 2.4 Ideal points in one paragraph (the political-science grounding)

The mainstream methods place each legislator at a point in a low-dimensional space such that votes are predicted by proximity to bill "cutpoints." **W-NOMINATE** (Poole–Rosenthal) assumes bell-shaped (normal) utility and estimates legislator coordinates from the yea/nay matrix; **IDEAL / IRT (2-PL item-response)** is the Bayesian analog where each bill has *difficulty* and *discrimination* parameters and each legislator a latent position. Cross-country work reports these methods correlate **>0.80** across the US, Brazilian, and Chilean chambers, so they transfer to Brazil. For our purposes, **PCA on the roll-call matrix (à la Radar Parlamentar) is a perfectly adequate, dependency-light approximation** of the first ideal-point dimension; reserve full W-NOMINATE/IRT for a v2 if we want calibrated uncertainty. References: NOMINATE <https://en.wikipedia.org/wiki/NOMINATE_(scaling_method)>, voteview comparison <https://legacy.voteview.com/pdf/nominatevideal.pdf>.

---

## 3. Scoring & matching design

Produce a **ranked list of candidates "best for you"** by combining four **separately normalized sub-scores (each 0–100)** and **not** collapsing them prematurely.

### 3a. Issue-position match (votes + manifesto) — the spine

- For each thesis *t*: user answer `u_t ∈ {−1, 0, +1}` (Não/neutro/Sim, with an **importance slider** `w_t`); candidate position `c_t ∈ [−1, +1]` from §2 (votes) or, where votes are absent, from **manifesto/proposta de governo / survey** (clearly labeled as *stated*, not *revealed*).
- **Distance metric:** use **weighted City-Block (Manhattan)** distance, the VAA standard (used by Swiss *smartvote* and most academic VAAs). It is more interpretable and less sensitive to one extreme axis than Euclidean:

  `match_issue = 1 − ( Σ_t w_t · |u_t − c_t| ) / ( Σ_t w_t · max_dist )` → scale to 0–100.

  The importance weight `w_t` directly implements **salience** (an issue rated twice as important doubles its contribution) — exactly the mechanism brasil.vota.com's slider implies.
- **Show the workings:** for the top matches, display the agree/disagree breakdown per thesis with the underlying *evidence* ("voted to loosen environmental licensing, Apr 2025") — this is the auditability that distinguishes us from closed quizzes.

### 3b. Attendance / diligence

- From presença em sessões/votações and absence rate (§2.2). Normalize to a percentile within the relevant house/cohort (comparing a deputy to deputies, not to senators).
- Keep it **separate** from issue match — a diligent legislator you disagree with should not float to the top of an "agrees with you" list.

### 3c. Integrity / transparency

- Inputs: **declared assets** evolution (TSE bem de candidato), **campaign-finance** disclosure quality, **Ficha Limpa / criminal & electoral record**, and (for incumbents) **CEAP-anomaly flags** in the Serenata/Jarbas spirit.
- Encode as a small set of **flags + a 0–100 transparency score**, not a single moralized number. Ficha Limpa ineligibility is a **hard flag** worth surfacing prominently rather than averaging away.

### 3d. Ideological proximity

- From PCA/ideal-point of the roll-call matrix (§1.2, §2.4): place the **user** on the same axes by projecting their quiz answers through the bill-direction coding, then compute proximity to each candidate/party. For challengers without votes, fall back to **party** coordinates (with a visible "based on party, not personal record" caveat).

### 3e. Combining, normalizing, presenting

- **Normalize each sub-score to 0–100** with a documented transform (percentile-within-cohort or min–max with fixed anchors). **Never** sum raw quantities of different kinds (a %, a flag, and a distance are not commensurable — summing them silently embeds value judgments; the Ranking dos Políticos `BASE+BONUS−PENALTY` formula is a clean *exemplar of the mechanics* but bakes in an editorial worldview via its 75% bill-scoring, which we must avoid).
- **Weighting:** offer **transparent presets** ("I care most about issues" / "I care most about integrity") **and** user-adjustable sliders across the four axes. Default to **issue-match-dominant** but always show the other three axes alongside.
- **Presentation:** a ranked card list. Each candidate card shows: overall match %, the **four axis bars**, top 3 agreements / top 3 disagreements with evidence links, integrity flags, party, and "record-based vs stated" provenance badges. Let users **re-sort by any single axis**. Avoid a single hero number with no breakdown — that is both less trustworthy and less useful.

---

## 4. Pitfalls & fairness

Known VAA failure modes (academic literature) and Brazil-specific ones, with mitigations.

1. **Thesis/statement selection bias.** Statement choice provably shifts which parties match more users — both individually and in aggregate (Acta Politica, "Design effects of VAAs": <https://link.springer.com/article/10.1057/ap.2013.30>). *Mitigation:* publish the thesis set and selection rationale; balance issues across the spectrum; pre-test that no party/cohort is systematically advantaged; ideally have a cross-partisan review panel sign off.
2. **Equating user and candidate scales.** A user's "Sim" and a candidate's revealed-vote "+1" are not guaranteed to live on the same scale; the spatial model itself is a choice and different valid models give different advice (StemWijzer study). *Mitigation:* keep dimensionality honest, prefer interpretable City-Block over fragile multi-dim spatial maps, and validate axes (dynamic scale validation, Germann/Mendez/Wheatley/Serdült 2015).
3. **Missing data — the dominant Brazilian problem.** (a) **Challengers have no votes**; (b) candidates may **not answer** the questionnaire (O Globo 2022: Lula & Bolsonaro never replied, so the two front-runners had no profile). *Mitigation:* never impute a position as "against" by default; show **"no record / did not respond"** explicitly; fall back to party position with a visible caveat; require a minimum coverage threshold before asserting a match (§2.2).
4. **Party vs candidate under open-list PR.** The voter picks a *candidate*, but seats are won by the **party/coalition** total, and a vote for a popular candidate can elect a co-listed candidate the voter dislikes (the "puxador de votos" effect). A pure candidate match hides this. *Mitigation:* surface **both** candidate match and the candidate's **party/coalition** context, and explain the list mechanic so the user understands their vote also helps the coalition.
5. **Coalition / federation effects (2026 specifics).** Party **federations** and coalitions blur the "party position" signal, and **leadership-orientation** votes (Basômetro's basis) reflect coalition discipline, not personal conviction. *Mitigation:* down-weight whip-driven/near-unanimous votes (§2.3); distinguish *personal* record from *party-line* behavior; label which is which.
6. **Editorializing the bills.** Whoever codes a bill's direction or "goodness" injects a worldview (the Ranking dos Políticos Conselho de Leis is explicit about its anticorrupção/antiprivilégios/antidesperdício lens). *Mitigation:* code bills only for **factual direction** (does Sim advance or block the thesis), and let the **user's answer** decide which direction is "good." Keep direction-coding documented, versioned, and open to challenge.
7. **Binarizing abstention as opposition.** Defensible for a government-loyalty index (Basômetro), wrong for a neutral issue match. *Mitigation:* treat abstention/obstruction as down-weighted neutral (§2.2).
8. **Over-precision & opacity.** A single confident percentage invites false trust. *Mitigation:* show uncertainty/coverage, the per-thesis breakdown, and provenance; make the algorithm and data open. VAAs measurably move vote choice and turnout (Cambridge EPSR; meta-analyses), so credibility and transparency are an ethical obligation, not a nicety.
9. **Non-partisanship governance.** *Mitigation:* open-source the matching code and the bill-direction dataset; document funding/independence (as vota.com does); offer the same data to all sides; let users audit any candidate's evidence trail.

---

## 5. Concrete recommendation (the pipeline in one picture)

```
Quiz answers (Sim/Não/neutro + importance wₜ per thesis)
        │
        ▼
[A] Issue match  ── weighted City-Block distance vs candidate position cₜ
        cₜ from:  incumbents → hand-direction-coded roll-calls (§2.1)
                  challengers → manifesto/survey (labeled "stated")
[B] Attendance   ── presença percentile within house cohort
[C] Integrity    ── Ficha Limpa flag + assets/finance + CEAP anomalies (Serenata-style)
[D] Ideology     ── PCA/ideal-point of roll-call matrix (Radar Parlamentar method),
                    user projected onto same axes
        │
        ▼
Normalize each → 0–100  ·  combine under transparent, user-adjustable weights
        │
        ▼
Ranked candidate cards: overall % + four axis bars + top agreements/disagreements
   with evidence links + integrity flags + party/coalition context + provenance badges
```

**Differentiator vs incumbents:** brasil.vota.com matches on *stated* answers; Radar/Basômetro analyze legislators but don't match *you*; Ranking scores legislators against a *fixed editorial lens*. Our pipeline matches the **user** to **candidates** using **revealed votes** (hand-coded for direction), keeps the four signals **separate and auditable**, and pushes all value judgments **to the user**, which is the credible, non-partisan position.

---

## Sources

- brasil.vota.com — <https://brasil.vota.com/>, quiz <https://brasil.vota.com/en/political-quiz>, candidates <https://brasil.vota.com/candidates/>
- Radar Parlamentar — <https://radarparlamentar.polignu.org/>, wiki <https://ccsl.ime.usp.br/wiki/Radar_Parlamentar>, PCA-quality note <https://polignu.org/en/node/666>, code <https://github.com/radar-parlamentar/radar>, dados.gov <https://dados.gov.br/aplicativo/radar-parlamentar>
- Basômetro — <http://blog.estadaodados.com/tag/basometro/>, code <https://github.com/estadao/basometro>, <https://github.com/estadaoDados/basometro>; Congresso em Foco Governismo <https://radar.congressoemfoco.com.br/governismo/camara>
- Ranking dos Políticos — <https://ranking.org.br/>, criteria <https://ranking.org.br/CriteriosAvaliacao>, methodology <https://olb.org.br/metodologia-do-ranking-de-parlamentares/>, Wikipedia <https://pt.wikipedia.org/wiki/Ranking_dos_Pol%C3%ADticos>
- Serenata de Amor / Rosie / Jarbas — <https://serenata.ai/>, Jarbas explainer <https://medium.com/data-science-brigade/jarbas-apresenta-todas-as-suspeitas-da-rob%C3%B4-rosie-da-opera%C3%A7%C3%A3o-serenata-de-amor-cd021e9be045>, Wikipedia <https://pt.wikipedia.org/wiki/Opera%C3%A7%C3%A3o_Serenata_de_Amor>
- Questão Pública (first VAA in Latin America, 2010 Senate) — Springer chapter <https://link.springer.com/chapter/10.1007/978-3-642-23333-3_19>
- O Globo 2022 candidate matcher — <https://costanorte.com.br/geral/quiz-mostra-com-qual-candidato-a-presidencia-voce-se-identifica-1398410.html>
- VAA design-effects & spatial-model critique — Acta Politica <https://link.springer.com/article/10.1057/ap.2013.30>, spatial models <https://www.sciencedirect.com/science/article/abs/pii/S0261379414000444>
- Candidates/voters under list systems — Cambridge EPSR <https://www.cambridge.org/core/journals/european-political-science-review/article/candidates-voters-and-voting-advice-applications/B4BBA53D4C023855DCA885A5B6F9E135>
- Open-list PR in Brazil — <http://socialsciences.scielo.org/pdf/s_dados/v3nse/scs_a05.pdf>
- Ideal-point / NOMINATE / IRT — Wikipedia <https://en.wikipedia.org/wiki/NOMINATE_(scaling_method)>, voteview comparison <https://legacy.voteview.com/pdf/nominatevideal.pdf>, issue-specific IRT <https://sooahnshin.com/issueirt.pdf>
- smartvote / proximity & weighting — Acta Politica "Matching voters to parties" <https://link.springer.com/article/10.1057/ap.2011.29>
