# VAA Academic Literature — Synthesis for voto-o-mat-br2026

Distilled from four peer-reviewed papers (cited in full below; consult them via their DOIs —
three are paywalled, Fossen & Anderson 2014 is open access). This is the methodological backbone
for the matching engine and thesis selection. Companion to `wahl-o-mat-methodology.md` (process) and
`research/04-matching-pipeline-design.md` (Brazilian prior art / pipeline).

> **The two findings that should drive our design:**
> 1. **The matching method changes the answer for up to 90% of users** (Louwerse & Rosema).
>    The algorithm is not a detail — it *is* the product. Show a **ranked list, never a single
>    "best match."**
> 2. **Accuracy rises with the number of questions per policy area; secondary issues barely
>    discriminate** (Wagner & Ruusuvirta). Ask *many* questions on each key Brazilian cleavage,
>    not one.

---

## Papers obtained (full text)

| # | Paper | Journal | Type |
|---|---|---|---|
| L1 | **Garzia & Marschall (2016)** — Research on VAAs: State of the Art and Future Directions | *Policy & Internet* 8(4):376–390 | Field survey |
| L2 | **Fossen & Anderson (2014)** — What's the point of voting advice applications? | *Electoral Studies* 36:244–251 | Normative theory |
| L3 | **Wagner & Ruusuvirta (2012)** — Matching voters to parties: VAAs and models of party choice | *Acta Politica* 47(4):400–422 | Empirical (accuracy) |
| L4 | **Louwerse & Rosema (2014)** — The design effects of VAAs: comparing methods of calculating matches | *Acta Politica* 49(3):286–312 | Empirical (method effects) |

## Still paywalled (citation-only — see `DATA-SOURCES.md` §E for links)
- Walgrave, Nuytemans & Pepermans (2009), *West European Politics* 32(6) — statement-selection bias (the foundational result; cited by all four above).
- Power & Zucco (2009), *Latin American Research Review* 44(1) — Brazilian party ideology estimates.
- Two further *Electoral Studies* 2014 VAA-symposium articles (S0261379414000444, …742) and an *EJOR* (S0377221717308524) matching-algorithm paper.

---

## L1 — Garzia & Marschall (2016): the field survey

**Citation:** Garzia, D. & Marschall, S. (2016). "Research on Voting Advice Applications: State
of the Art and Future Directions." *Policy & Internet* 8(4):376–390. DOI 10.1002/poi3.140.

**Why it matters to us:**
- **VAAs thrive in fragmented multiparty PR systems** and see almost no uptake in two-party
  majoritarian ones (Garzia 2012). **Brazil — highly fragmented, open-list PR — is the ideal
  habitat.** (Netherlands: >50% of the electorate used a VAA in 2012; Wahl-O-Mat: 13.3M uses in
  2013.)
- **Statement selection AND wording change results** — documented selection-bias source
  (Walgrave et al. 2009; Lefevere & Walgrave 2014/2015; positive vs negative phrasing matters,
  Holleman et al. 2014).
- **Party-positioning methods:** parties self-place; experts code manifestos; the **iterative
  method** (self-placement + expert verification, pioneered by Kieskompas, scaled by EU
  Profiler); and the newer **Delphi method** (Gemenis 2014). Iterative is the credible default.
- **Effects on voters:** political *knowledge* ↑ and *turnout* ↑ are robustly supported across
  study designs; *vote-change* is small and contested (self-declared switching 2–3% Belgium,
  ~6% Germany, >10% Finland/Switzerland) and mostly **short-term** (Mahéo 2016).
- **Users are non-representative** (young, male, educated, politically interested) — a robust
  finding and a known fairness caveat.
- **Recommendation echoed field-wide:** present advice as a **preference list, not a single
  best match** (Rosema & Louwerse 2016).

---

## L2 — Fossen & Anderson (2014): what is a VAA *for*?

**Citation:** Fossen, T. & Anderson, J. (2014). "What's the point of voting advice
applications? Competing perspectives on democracy and citizenship." *Electoral Studies*
36:244–251. DOI 10.1016/j.electstud.2014.04.001. **Open access (CC BY-NC-ND).**

A normative paper — no algorithms — but it forces the foundational decision. Three models
(their Table 1):

| Model | Democratic ideal | "Competence gap" it fixes | The point |
|---|---|---|---|
| **Matching** (Wahl-O-Mat, StemWijzer, Vote Compass) | social-choice; voter as "savvy political shopper" | voter *ignorance of party positions* | maximize preference→policy congruence |
| **Deliberative** | democracy as co-legislation | voter lacks *well-considered* preferences | help users *form/revise* preferences (e.g. info pop-ups on "no opinion") |
| **Contestatory / agonistic** | challenge the status quo | *framed/constricted* perception of the menu | shift the agenda; expose what's missing (e.g. statements no party holds) |

**Key warnings for us:**
- "A biased depiction… is often shrouded in claims to neutrality." **Don't claim neutrality;
  document choices.**
- Matching VAAs reduce voting to "a series of referenda" on given preferences — a real
  limitation in a candidate-centric system like Brazil's.
- Enrichment ideas worth stealing: background-info links, **justification/credibility ratings**,
  dynamic statement revision, "you could also abstain" result screens.

**Our stance:** primarily a **Matching** VAA (it's what users expect and what the data
supports), but borrow Deliberative enrichments (evidence links behind every thesis — the actual
roll-call vote) to mitigate the "series of referenda" critique.

---

## L3 — Wagner & Ruusuvirta (2012): how accurate are the matches?

**Citation:** Wagner, M. & Ruusuvirta, O. (2012). "Matching voters to parties: Voting advice
applications and models of party choice." *Acta Politica* 47(4):400–422. DOI 10.1057/ap.2011.29.

**Method:** extracted party left-right positions from **13 VAAs in 7 countries** via
**multidimensional scaling (MDS)**, validated against expert surveys (Benoit-Laver, Chapel
Hill) and CMP manifesto data using rank correlations.

**Findings that shape our build:**
- VAAs encode a **proximity (Euclidean) logic**, *not* a directional one — they do **not**
  reward parties for more extreme/intense positions (only Swiss Smartvote factors direction).
- **Convergent validity is good on the main axis** (VAA↔expert Spearman ρ mostly >0.8) for
  **left-right and economic** policy, but **poor on secondary issues**.
- **The central practical law: accuracy rises with the number of questions asked.** Secondary
  cleavages need *many* items to separate parties — 2008 Austria placed *every* party but FPÖ
  identically on immigration until a tool asked **11** immigration questions.
  → **Ask as many questions as possible per key policy area; offer short/long versions; more
  parties ⇒ more questions needed.**
- **Scales:** 20–35 statements typical (Smartvote: 73). Formats vary (yes/no/neutral/don't-know;
  5-point Likert + "no opinion"). With multi-point scales there's "arithmetically no side":
  "agrees somewhat" is equidistant from "agrees completely" and "disagrees somewhat."
- **Weighting/salience:** offered by several (double/halve a statement) but **usually on a final
  screen and most users don't use it** — don't rely on it for correctness.
- **Self-placement manipulation risk:** Finnish candidates placed themselves mid-scale on every
  item to court all sides until media exposure forced substantiation. (Another argument for
  **deriving incumbent positions from votes**, not self-report.)
- Wahl-O-Mat confirmed: a team of **young voters + political scientists, statisticians,
  journalists, and the bpb** formulate many statements, then **keep only sufficiently divisive
  items** — the *Trennschärfe* rule, in the literature.

---

## L4 — Louwerse & Rosema (2014): the matching method *is* the product

**Citation:** Louwerse, T. & Rosema, M. (2014). "The design effects of voting advice
applications: comparing methods of calculating matches." *Acta Politica* 49(3):286–312.
DOI 10.1057/ap.2013.30.

**Method:** real log files from Dutch **StemWijzer 2010** (~4.2M completions ≈ 40% of the
electorate); reimplemented **8 matching methods** on an identical 10,000-user sample (30
statements, 11 parties) and compared the advice.

**The headline result:**
- **Up to ~90% of users get a *different* "best match" depending on the method.** Even the
  closest spatial model differs for ~50% of users.
- The three **high-dimensional** methods agree closely (agreement↔city-block ρ=0.91,
  city-block↔Euclidean ρ=0.97). **Low-dimensional spatial models are pathological:**
  - **1D** gives the orthodox-Protestant **SGP 53%** and CU 27% of best-matches — because parties
    cluster at the extremes while ~50% of *voters* sit at the centre, so tiny centrist parties
    "win."
  - **2D** inflates Christian Union to 28% (vs 3% under the agreement method).
- **Why:** statements are deliberately chosen to separate *party pairs*, which pushes parties to
  the ends of each issue and does **not** yield a clean low-dimensional space. Scale homogeneity
  (Loevinger H): ~0.37 for parties on a 1D scale but only **0.07 for voters** — "policy
  preferences of voters are not strongly structured" (Converse 1964). MDS needed **3D for party
  answers but ~10D for voters**.

**Directives we adopt from L4:**
1. **Use a high-dimensional method** — the StemWijzer "agreement" count (algebraically a
   city-block model) or plain city-block/Euclidean over the raw items. **Do not** project onto a
   1D/2D ideological map unless we *separately validate* that the scale is metrically sound
   (publish the H/stress) — otherwise it distorts toward fringe parties.
2. **Never show a single best match** — show the **full ranked list / bar chart**; a single
   number overstates precision.
3. **Missing data:** compute agreement/distance over answered items only (their approach); drop
   skip-only and bot profiles (they excluded ~30,000 identical-IP bot runs).
4. **Neutral handling:** users pick "neutral" far more than parties do (11.2% vs 2.4%); 5–7-point
   scales scale better than 3-point but widen this gap — decide deliberately.
5. **VAA advice ≠ election prediction** and that's fine: under "agreement," PVV won 34% of
   best-matches while the actual election winner VVD got ~7%. The tool measures *issue
   congruence*, not electability.

---

## Cross-cutting synthesis → design directives for voto-o-mat-br2026

1. **Algorithm = product.** Default to a **high-dimensional agreement / city-block** match over
   raw theses. Treat any ideological-map view as a *secondary, separately-validated* visualization.
2. **Output a ranked list with per-thesis explanations**, never one "best match."
3. **Depth per cleavage beats breadth of cleavages.** For each major Brazilian axis
   (economic/fiscal, security/justice, environment, social/moral, institutional/anti-corruption,
   regional/federalism) ask **several** theses — secondary issues need volume to discriminate.
4. **Behavioural positioning over self-report** — directly addresses two documented failures:
   self-placement gaming (L3) and the missing-data / non-response problem (Questão Pública, doc
   05). Derive incumbent party/candidate positions from **roll-call votes**; reserve self-report
   for non-incumbent challengers and label it as such.
5. **Keep the math transparent and own the choices** (L2). Publish the method; don't claim
   neutrality; link every thesis to its evidence (the bill/vote).
6. **Expect a non-representative user base** (young, male, educated); design onboarding and
   communication to widen it, and disclose the caveat.
7. **Behavioural *Trennschärfe* as the selection filter** — keep theses whose underlying votes
   actually split the houses; this is the empirical version of the universal "only divisive
   statements survive" rule (L1, L3) and of Walgrave's M-shaped-distribution test.
