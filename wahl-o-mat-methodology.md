# Wahl-O-Mat — Methodology, Matching Math & Glossary (Canonical)

*Reference document for designing the Brazilian voting-advice app (voto-o-mat-br2026).
Compiled June 2026 from authoritative German sources (bpb.de, Landeszentralen, the bpb
Rechenmodell PDF, Wikipedia, university explainers). Every factual claim was verified against
a primary source; URLs are linked inline. This file merges the methodology overview, the exact
scoring math, the German-term glossary, and the Brazil adaptation notes into one place.*

> The single most important idea: **a thesis only survives if it splits the parties.**
> Everything below serves that principle.

---

## 0. What the Wahl-O-Mat is (one paragraph)

The Wahl-O-Mat ("election-o-mat") is a Voting Advice Application (VAA) run by the
**Bundeszentrale für politische Bildung (bpb)** — the German federal agency for civic
education — since 2002. It was modelled on the Dutch *StemWijzer* and first launched for the
2002 Bundestag election in cooperation with the student agency *Politikfabrik*. Users answer
**38 political statements ("Thesen")** with *agree / neutral / disagree*, optionally
double-weight statements that matter to them, and receive a percentage match with each
participating party. It is one of the most-used political tools in Germany (tens of millions
of uses per federal election). Sources: [Wikipedia: Wahl-O-Mat](https://de.wikipedia.org/wiki/Wahl-O-Mat),
[bpb: Wahl-O-Mat](https://www.bpb.de/themen/wahl-o-mat/).

---

## 1. Who makes it

| Actor | Role |
|---|---|
| **Bundeszentrale für politische Bildung (bpb)** | Federal Agency for Civic Education. Owns and operates Wahl-O-Mat (since 2002). Non-partisan public institution. |
| **Landeszentrale für politische Bildung (LpB/LzpB)** | The *state-level* counterpart. Co-runs regional editions (Landtag) and European editions. |
| **Redaktionsteam** (editorial team) | **20–25 young / first-time voters (aged 16/18–26)**, recruited by open online application, who draft and select the theses. |
| **Scientific & pedagogical advisors** | Several **political scientists, statisticians, and educators**, plus subject-matter experts and bpb/LpB staff, who guide the team and safeguard methodological quality. A federal edition's full team is on the order of ~38 people, of whom ~24 are young voters. |
| **The parties** | Every ballot-qualified party answers the full thesis pool; their answers become the official answer key. **Parties never write or select theses — they only answer them.** |
| **Independent evaluation team** | Researchers at **Heinrich-Heine-Universität Düsseldorf** have independently studied Wahl-O-Mat's effects on users at every election since 2004 (evaluation, not authorship). |

The bpb also maintains a standing **wissenschaftlicher Beirat (scientific advisory board)** of
up to twelve experts for civic-education matters generally.

**Crucial neutrality rule:** *Parties do not write or select the theses.* Their only role is to
**answer** the finished theses and to **authorize** those answers (see §3).

Sources: [bpb: Die Entstehung eines Wahl-O-Mat](https://www.bpb.de/themen/wahl-o-mat/45292/die-entstehung-eines-wahl-o-mat/),
[SLPB: Wie entsteht der Wahl-O-Mat](https://www.slpb.de/themen/staat-und-recht/wahlen-beteiligung-und-parteien/wahlen/wahl-o-mat/wie-entsteht-der-wahl-o-mat),
[bpb FAQ BTW 2025](https://www.bpb.de/themen/wahl-o-mat/bundestagswahl-2025/558464/haeufig-gestellte-fragen-zum-wahl-o-mat/),
[Wikipedia](https://de.wikipedia.org/wiki/Wahl-O-Mat).

---

## 2. The build pipeline (the ~80–100 → 38 funnel)

```
Party manifestos + current debates
        │
        ▼
  Workshop 1 — DRAFTING (3 days, ~3 months before the election)
        │   young team splits into ~5 thematic subgroups, drafts a large POOL
        ▼
   ~80–100 candidate theses
        │   the ENTIRE pool is sent to every ballot-qualified party
        ▼
  Parties answer each: agree / neutral / disagree (+ optional justification)
        │
        ▼
  Workshop 2 — SELECTION (~1 week before launch)
        │   team narrows the pool using 3 criteria (importance, discrimination, balance);
        │   because parties already answered the full pool, discrimination is DATA-DRIVEN
        ▼
   Final 38 theses          ← the published Wahl-O-Mat
        │
        ▼
  Build, test, launch (2–4 weeks before the election)
```

### Step 1 — First workshop (~3 months out): generate the pool

The full team meets for a **three-day workshop**. Working in **~5 thematic subgroups** (typical
fields: labour/economy, energy/environment, family & education, finances/budget, and
state/governance/internal affairs), the young editors — advised by the experts — draft
**~80 to 100 candidate theses ("Thesen")**.

**Source material:** the **party and election manifestos (Partei- und Wahlprogramme)** of *all*
ballot-admitted parties, their public programmatic statements, and the salient debates of the
campaign. Theses are grounded in what parties actually claim they will do, and chosen to span
the major policy fields.

**What makes a "good" thesis (drafting criteria):**
- **Relevant and of broad public interest** — one of the most important topics of *this* election.
- **Clearly and simply worded** — understandable to non-experts; avoids jargon.
- **A genuine yes/no political position**, not a factual question — a party can meaningfully say agree/neutral/disagree.
- **Decidable from manifestos** — parties can take a defensible position on it.
- Collectively, a **broad thematic spectrum** so no policy area dominates.

### Step 2 — Parties answer the full pool

The ~80–100 candidate theses are sent to the parties, who answer *all* of them (see §3). This is
what makes the next step possible: editors can see, empirically, which theses split the parties.

### Step 3 — Second workshop / "Auswahlworkshop" (~1 week before launch): narrow to 38

The whole team reconvenes and selects the final **38 theses** from the pool. Because the parties
have already answered the *full* pool, the **discrimination** filtering is **measured from real
data**, not guessed.

### Step 4 — Build, test, launch

The finished tool is programmed and tested, and goes live **2–4 weeks before the election**.

> **Funnel summary:** ~80–100 candidate theses → parties answer all → keep the ones that are
> *important AND split the parties AND keep topic balance* → **38** final theses.
>
> The thesis count is conventionally **38** for the federal (Bundestag) edition; regional and
> European editions vary (often ~38, sometimes 30–40). The number is an editorial convention,
> not a rule.

Sources: [bpb: Entstehung](https://www.bpb.de/themen/wahl-o-mat/45292/die-entstehung-eines-wahl-o-mat/),
[SLPB](https://www.slpb.de/themen/staat-und-recht/wahlen-beteiligung-und-parteien/wahlen/wahl-o-mat/wie-entsteht-der-wahl-o-mat),
[bpb FAQ BTW 2025](https://www.bpb.de/themen/wahl-o-mat/bundestagswahl-2025/558464/haeufig-gestellte-fragen-zum-wahl-o-mat/).

---

## 3. Selection criteria for the final 38

The bpb names **three official criteria** applied at the selection workshop:

1. **Topic importance (Bedeutung)** — is the issue actually significant in this election?
2. **Trennschärfe (discriminating power)** — does it split the parties? *The* decisive filter
   (see glossary). Measured from the parties' answers to the full pool.
3. **Policy-area balance (Themenbalance)** — the final 38 must span policy fields, not cluster.

Secondary editorial constraints also applied:

4. **Relevance & currency (Aktualität)** — tied to the live campaign.
5. **Clarity (Verständlichkeit)** — short, unambiguous, answerable with agree/disagree.

---

## 4. How parties answer, and how the set is validated

- **Who is invited:** every party admitted to the ballot / running a list at the relevant level.
  Participation is voluntary; each party decides whether to take part.
- **Channel & timing:** parties receive all candidate theses through a **secured online input
  system ("abgesichertes Online-Eingabesystem")** and have **~2–3 weeks** to respond.
- **Response format:** for each thesis, exactly one of **"stimme zu" (agree) / "neutral" /
  "stimme nicht zu" (disagree)**, plus an **optional justification of up to 500 characters**
  (which users can read in the tool). CDU and CSU answer jointly.
- **Quality control:** the political scientists review answers for internal consistency and
  clarity and may flag them back to the party for revision — **but the party always has the
  final say** on its own positioning.
- **Validation of the final set:** because every party has answered the entire pool *before* the
  final 38 are chosen, the editors select precisely those theses on which party answers genuinely
  differ. This is the empirical check that the tool will actually discriminate.

Sources: [bpb FAQ BTW 2025](https://www.bpb.de/themen/wahl-o-mat/bundestagswahl-2025/558464/haeufig-gestellte-fragen-zum-wahl-o-mat/),
[Wikipedia](https://de.wikipedia.org/wiki/Wahl-O-Mat).

---

## 5. The matching algorithm — exact math

The official scoring is published by the bpb as the **"Rechenmodell des Wahl-O-Mat"**
(CC BY-NC-ND 3.0, 2022). [PDF](https://www.bpb.de/system/files/dokument_pdf/Rechenmodell_des_Wahl-O-Mat.pdf).
The grids and worked example below are transcribed directly from that document.

### 5.1 The answer options

User and party each take one of three positions per thesis — **agree / neutral / disagree** —
and the user can additionally **skip** a thesis or **weight (double)** it.

### 5.2 Per-thesis points — *without* weighting

The Wahl-O-Mat scores both **agreement** and **proximity** (a neutral-vs-agree gap is "closer"
than an agree-vs-disagree gap). Points the user earns toward a given party, by
(user position × party position):

| User ↓ \ Party → | agree | neutral | disagree |
|---|---|---|---|
| **agree** | **2** | 1 | 0 |
| **neutral** | 1 | **2** | 1 |
| **disagree** | 0 | 1 | **2** |
| **skip** | 0 | 0 | 0 |

- **Exact match → 2 points.**
- **Off-by-one / partial match → 1 point** (e.g., party "neutral", user "agree").
- **Direct opposite (agree vs disagree) → 0 points.**
- **Skipped thesis → 0 points, and it is excluded from the maximum too** (it drops out of the
  calculation entirely).

### 5.3 Per-thesis points — *with* weighting (the "doubly weighted" thesis)

Weighting a thesis simply **multiplies that thesis's whole row by 2** — both the points earned
and the maximum it contributes double:

| User ↓ \ Party → | agree | neutral | disagree |
|---|---|---|---|
| **agree** | **4** | 2 | 0 |
| **neutral** | 2 | **4** | 2 |
| **disagree** | 0 | 2 | **4** |
| **skip** | 0 | 0 | 0 |

So a weighted thesis can yield up to **4** points (and counts **4** toward the maximum) versus
**2** for an unweighted one. "Counts double" means it raises both numerator and denominator for
that thesis, increasing its leverage on the final percentage.

### 5.4 Maximum points per thesis

- Unweighted, not skipped → max **2**
- Weighted, not skipped → max **4**
- Skipped → max **0** (removed from the sum)

### 5.5 Normalization to a percentage

For each party:

```
match% = (sum of points earned across all theses)
         ───────────────────────────────────────────  × 100
         (sum of maximum points across all theses)
```

The maximum is **not fixed** — it depends on how many theses the user skipped (subtract from the
max) and how many they weighted (add to the max). Each party is scored against the *same*
user-defined maximum, so they are directly comparable. Parties are then ranked by descending
match%.

### 5.6 Official worked example (from the Rechenmodell PDF)

The PDF works a full 38-thesis example for 4 parties. The user **skips** theses 1 and 35 (each
contributes 0 to the max) and **weights** several theses (5, 6, 20, 23, 24, 25, 26, 34), each
contributing up to 4. Summing the "maximale Punkte" column gives a **maximum of 86 points**:

| Party | Points earned | Max | Match % |
|---|---|---|---|
| Partei 1 | 29 | 86 | **33.7 %** |
| Partei 2 | 49 | 86 | **57.0 %** |
| Partei 3 | 54 | 86 | **62.8 %** |
| Partei 4 | 34 | 86 | **39.5 %** |

Check: 29/86 = 0.337, 49/86 = 0.570, 54/86 = 0.628, 34/86 = 0.395 — exactly the published
percentages. So the algorithm is just **(points earned ÷ user-specific maximum) × 100**, with
per-thesis points read off the 2-point (or 4-point if weighted) proximity grid, and skipped
theses dropped from both numerator and denominator. **There is no hidden ideological model, no
clustering, no machine learning in the user-facing match score.** (Third-party analysts like
D. Kriesel and Michael Hunger have *additionally* run clustering/graph analyses on the published
party-answer matrices, but that is downstream research, not part of the official match.)

This is deliberately simple and transparent — every point is explainable to the voter.

Source: [bpb Rechenmodell PDF](https://www.bpb.de/system/files/dokument_pdf/Rechenmodell_des_Wahl-O-Mat.pdf).

### 5.7 Known methodological criticisms (worth designing around)

- **Binary/coarse positions.** Reducing every issue to agree/neutral/disagree loses nuance;
  critics call the ternary reduction the algorithm's biggest weakness.
  ([wegewerk critique](https://www.wegewerk.com/de/blog/wahl-o-mat-binaer-aequilibrierter-unfug-ist-kein-spiel/))
- **Small single-issue parties** can be advantaged or disadvantaged by thesis selection, since a
  party with few core themes is matched on whichever themes happen to be in the 38.
- **Self-reported positions.** Parties answer based on manifestos, which may diverge from actual
  voting behaviour in office (see §7).
- **Thesis-selection power.** Whoever picks the 38 themes implicitly sets the agenda; the bpb
  mitigates this via the young-voter team, expert oversight, and the discrimination criterion,
  but it remains a real editorial lever.

---

## 6. Glossary of specific terms

Each entry: **German term — literal meaning → what it is → why it matters → Brazilian equivalent.**

### Trennschärfe
**Literal:** "cutting sharpness" / selectivity (*trennen* = to separate, *Schärfe* = sharpness).
**What it is:** the degree to which a thesis **separates the parties** — how much their answers
diverge. A thesis where every party answers "agree" has **zero Trennschärfe**.
**Why it matters:** it is the primary survival filter. A non-discriminating thesis carries no
information for the voter — matching everyone equally tells you nothing. The whole point of the
~80→38 funnel is to keep the high-Trennschärfe theses and discard the consensus ones.
**Statistical analogue:** a quiz item with high **discrimination index**, or a feature with high
**variance / information gain** across classes.
**Brazil equivalent:** **behavioral Trennschärfe** — instead of asking how much *self-reported
party answers* diverge, measure how much **actual roll-call votes (votações nominais)** on a bill
split the parties/deputies. Keep topics where legislators genuinely voted differently; drop
near-unanimous votes. A more reliable, manipulation-resistant version.

### These / Thesen
**Literal:** thesis / theses — a **statement**, not a question.
**What it is:** the ~38 declarative statements the user reacts to (e.g. "Germany should…").
Phrased so a party and a voter can both take a clear agree/disagree stance.
**Brazil equivalent:** **tese** — a policy statement, ideally backed by a concrete bill or vote
(e.g. "O Brasil deveria…").

### Wahlprogramm (pl. Wahlprogramme)
**Literal:** "election program" → **party manifesto / platform**.
**What it is:** a party's official written policy program for the election. The **primary source**
the editorial team mines to draft theses.
**Why it matters:** theses are grounded in what parties actually promise, not invented.
**Brazil equivalent:** **programa partidário** and the candidate's **proposta de governo** (the
government-plan document filed with the TSE at registration). Note: in Brazil these are
weaker/less binding and candidate-centric, which is why **voting records** are a better anchor.

### Bundeszentrale für politische Bildung (bpb)
**Literal:** "Federal Center for Political Education."
**What it is:** Germany's public, non-partisan civic-education agency; operator of Wahl-O-Mat.
**Brazil equivalent:** no exact match. Nearest analogs in spirit: the **TSE's** voter-education
arm, or independent civic-tech orgs (e.g. **Open Knowledge Brasil**). A credible Brazilian VAA
would likely need an independent, visibly non-partisan steward.

### Landeszentrale für politische Bildung
**Literal:** "State Center for Political Education" — the regional bpb.
**Brazil equivalent:** a state-level electoral/education body (e.g. a **TRE** — Tribunal Regional
Eleitoral) for state-election editions.

### Redaktionsteam
**Literal:** "editorial team" (*Redaktion* = editorial office).
**What it is:** the group that drafts and selects theses — **built around young / first-time
voters** plus expert advisors.
**Why it matters:** centering young voters keeps questions close to real voter concerns and away
from party-strategist framing; the diversity guards against bias.
**Brazil equivalent:** a **citizen/young-voter editorial panel** + academic advisors. Important
for credibility and to avoid any single ideological tilt in thesis selection.

### Jung- und Erstwähler
**Literal:** "young and first-time voters" (*Erstwähler* = someone voting for the first time).
**What it is:** the demographic that forms the core of the editorial team.
**Brazil equivalent:** **eleitores jovens / de primeira viagem** — in Brazil voting is optional
at 16–17 and from 70+, compulsory 18–69, so first-time voters skew very young.

### Redaktionsworkshop
**Literal:** "editorial workshop."
**What it is:** the multi-day in-person session where the team drafts the thesis pool and, after
parties answer, narrows it to the final set.
**Brazil equivalent:** **oficina editorial** — the working session that produces the teses.

### Position / Parteiposition
**Literal:** a party's stance on a thesis: **agree (Stimme zu) / neutral / disagree (Stimme nicht
zu)**, plus a justification (**Begründung**).
**What it is:** the official answer key the user is matched against.
**Brazil equivalent:** the party/candidate stance — either **self-reported** (manifesto/survey)
or, better, **derived from votos** (how they voted on the bill behind the tese).

### Begründung
**Literal:** "justification / reasoning."
**What it is:** the short text (≤500 chars) each party supplies explaining its position on a
thesis; shown to users who want to dig in.
**Brazil equivalent:** **justificativa** — and you can auto-generate a factual one from the
actual vote ("voted YES on PL X on date Y").

### Gewichtung (doppelte Gewichtung)
**Literal:** "weighting" / "double weighting."
**What it is:** the user can mark theses that matter most to them; those count **double** in the
score.
**Why it matters:** lets the match reflect the voter's priorities, not just raw agreement.
**Brazil equivalent:** **ponderação / peso dobrado** — same mechanic.

### StemWijzer
**Literal:** Dutch for "vote pointer / vote guide."
**What it is:** the **original** voting-advice application (Netherlands, 1989) that Wahl-O-Mat was
modeled on. The historical root of the whole VAA genre.
**Brazil equivalent:** prior art to study; the Brazilian product analog is **brasil.vota.com**.

### Voting Advice Application (VAA)
**Literal:** the academic/English umbrella term for tools like Wahl-O-Mat, StemWijzer, etc.
**What it is:** the research field that studies thesis selection bias, scale-equating, and match
algorithms. Worth citing for methodology and known pitfalls.
**Brazil equivalent:** same term; sometimes Portuguese **"aplicativo de orientação de voto."**

---

## 7. Adaptation notes for Brazil (design implications)

The German design transfers cleanly in its *editorial* logic but needs rework for Brazil's
**multi-party, candidate-centric, coalition-heavy** system.

**a) Manifestos are a weak anchor.** Brazil's system is candidate-centric, open-list
proportional, with many fragmented parties and loosely-binding *propostas de governo*.
→ Anchor theses to **real legislative behavior** (votações nominais) wherever possible.

**b) Many parties → the proximity scoring still works, but presentation must scale.** Germany
shows ~6–15 parties; Brazil has ~30 registered parties and large legislative blocs. The
(earned ÷ max) × 100 score is party-count-agnostic and works unchanged. But a ranked list of 30
parties is unhelpful — consider grouping by federation/coalition (*federações partidárias*) and
surfacing the top-N plus the user's worst matches.

**c) Party *and* candidate matching.** Brazilians vote for **named candidates** (president,
governor, senators, and *open-list* deputies) more than for an abstract party. Generalize the
German "party answers the theses" model to **candidates answer the theses** (at least for
executive races and prominent legislative candidates), with party as a fallback/aggregate. This
multiplies the response-collection burden enormously — a key reason to consider (d).

**d) Ground theses in real roll-call votes, not self-reported answers — the biggest
opportunity.** Brazil's Câmara dos Deputados and Senado publish **recorded roll-call votes
(votações nominais)** via open-data APIs (dadosabertos.camara.leg.br, legis.senado.leg.br).
Instead of (or alongside) asking parties/candidates to self-report agree/neutral/disagree —
which invites strategic, manifesto-flavoured answers — you can **derive an incumbent's position
on a thesis from how they actually voted** on the corresponding bill(s). This:
  - removes the self-report bias the German tool is criticized for;
  - lets you cover *every* sitting deputy/senator without asking them anything;
  - makes each thesis auditable ("this politician voted YES on PL X on date Y").
  Mapping a plain-language thesis to one or more concrete *proposições/votações* becomes the core
  editorial task — a sharper version of the German "ground theses in manifestos" step. Keep a
  self-report path only for non-incumbents (challengers with no voting record) and for issues
  with no clean roll-call.

**e) Keep the discrimination criterion — and you can now compute it from data.** Because you have
actual vote records, you can *measure* a candidate thesis's discriminating power (variance/entropy
of positions across politicians) before publishing, and drop low-discrimination theses
automatically — a stronger, more objective version of the German "must split the parties" rule.

**f) Federalism & ballot complexity.** Brazil elects president, governor, senators, federal
deputies, and state deputies, often simultaneously. Decide whether the tool is per-race (separate
thesis sets and matches for the presidential race vs. your local deputy) or unified. Per-race is
closer to the German model and lets roll-call grounding map to the right chamber.

**g) Preserve the trust architecture.** The bpb's credibility rests on: non-partisan public
ownership, theses written by ordinary young voters (not parties), full transparency of the
scoring math, and parties only *answering*, never *selecting*. Replicate all four — and the
roll-call grounding adds a fifth, even stronger trust anchor: *the data, not the politician,
states the position.* Keep the math transparent: reuse Wahl-O-Mat's simple, explainable point
system; resist black-box ideology models for the public-facing score (use ideal-point estimation
only as an internal aid, clearly labeled).

---

## Sources

- [bpb — Die Entstehung eines Wahl-O-Mat](https://www.bpb.de/themen/wahl-o-mat/45292/die-entstehung-eines-wahl-o-mat/)
- [bpb — Häufig gestellte Fragen zum Wahl-O-Mat (Bundestagswahl 2025)](https://www.bpb.de/themen/wahl-o-mat/bundestagswahl-2025/558464/haeufig-gestellte-fragen-zum-wahl-o-mat/)
- [bpb — Rechenmodell des Wahl-O-Mat (PDF, scoring grids & worked example)](https://www.bpb.de/system/files/dokument_pdf/Rechenmodell_des_Wahl-O-Mat.pdf)
- [bpb — Wahl-O-Mat (overview)](https://www.bpb.de/themen/wahl-o-mat/)
- [SLPB (Sächsische LpB) — Wie entsteht der Wahl-O-Mat?](https://www.slpb.de/themen/staat-und-recht/wahlen-beteiligung-und-parteien/wahlen/wahl-o-mat/wie-entsteht-der-wahl-o-mat)
- [Wikipedia (DE) — Wahl-O-Mat](https://de.wikipedia.org/wiki/Wahl-O-Mat)
- [wegewerk — critique of the binary structure](https://www.wegewerk.com/de/blog/wahl-o-mat-binaer-aequilibrierter-unfug-ist-kein-spiel/)
- [D. Kriesel — Wahl-O-Mat-Auswertung BTW 2017 (downstream clustering analysis)](https://www.dkriesel.com/blog/2017/0904_wahl-o-mat-auswertung_teil_2_thesen-_und_parteienverwandtschaften)
</content>
</invoke>
