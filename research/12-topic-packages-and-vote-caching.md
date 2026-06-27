# Topic Packages & Vote Caching — Why We Store Laws and Never Re-Fetch Them

*Compiled 2026-06-27. The architectural rationale for storing a topic's laws and roll-calls once
(a "topic package") and scoring every politician against that cache — instead of re-fetching the
laws each time we add a new political figure. Builds on the backend in
[`11-integration-plan.md`](11-integration-plan.md). API facts verified live (see
[`08-api-field-notes.md`](08-api-field-notes.md)).*

> **The one-sentence reason:** a roll-call vote is **immutable** and **deputy-independent**, so a
> topic's voting data is a *fixed, shared dataset* — fetch it once, then comparing any number of
> politicians is a database lookup, not a new search.

---

## 1. What a "topic package" is

A **topic package** is a topic frozen into reusable data. For *wealth taxation* it contains:

1. the **topic**,
2. its **laws** (found by discovery — see [`09-topic-to-law-discovery.md`](09-topic-to-law-discovery.md)),
3. the **keywords** under each law, with a `direction` (does a `Sim` advance the thesis?),
4. the **frozen roll-calls** for those laws: every votação's full `/votos` (all deputies) and its
   `/orientacoes` (the Governo/Oposição line).

It is built **once** (discovery → ingestion) and then reused indefinitely.

---

## 2. Why the laws *must* be stored (not re-fetched per politician)

### 2.1 Roll-calls are immutable
A vote that happened on a date never changes — the tally, who voted how, and the government
orientation are historical fact. There is **no fresh data to fetch** on a re-run. Storing it loses
nothing; re-fetching gains nothing.

### 2.2 A roll-call is deputy-independent
`/votacoes/{id}/votos` returns **every** deputy's vote in a single response (400+ rows), not one
politician's. So the moment we fetch a votação once, we already hold the vote of **every current
and future** politician on it. Fetching it again "for a new politician" re-downloads data we
already have.

### 2.3 The cost difference is structural, not marginal
Tiago's current `infer_law_vote` fetches the votações **inside the per-politician loop**, so:

| Approach | API calls to score N politicians |
|---|---|
| **Re-fetch per politician** (current) | `O(N × laws × votações)` — same roll-calls downloaded N times |
| **Store once, score from cache** | `O(laws × votações)` **one time**, then `O(0)` per politician |

For the wealth-taxation package (~16 voted laws, ~90 nominal votações) scoring 513 deputies, that
is **~90 fetches once** vs. **~46,000 repeated fetches** — and the repeated version is exactly what
triggers the API throttling that surfaces as the "fake CORS" failures (see `08`).

### 2.4 Comparison requires a stable baseline
To rank/compare politicians fairly they must be measured against the **same** set of laws and the
**same** vote records. A stored package guarantees that; live re-fetching invites drift (different
recent-vote windows, partial fetches, throttled gaps) between one politician and the next.

---

## 3. Why adding a new political figure does NOT re-fetch the laws

Scoring a politician needs three things; only one is per-person, and the laws are never among them:

| Data needed to score a politician | Source | Fetched when adding a new politician? |
|---|---|---|
| The **laws** + their **keywords/direction** | topic package (stored) | **No** — already stored |
| How the politician **voted** on each law | the cached roll-calls (`/votos`, all deputies) | **No** — their vote is already in the stored roll-call; it's a lookup by `deputado_.id` |
| The politician's **wealth** (`bens`) | TSE, per candidate | **Once** — fetched the first time this person is scored, then cached in `politics` |

So a new figure costs **one** wealth fetch (their own `bens`) and **zero** law/vote fetches.
Comparing politicians already in the system costs **zero** API calls — pure cache.

---

## 4. The only times we re-touch the API

1. **A law in the package is voted again** — a new votação appears for that proposição. Re-ingest
   *only that law's new roll-calls* (incremental, cheap). Past votes are untouched.
2. **Curation** — we add/remove a law from the topic, or change a keyword's `direction`.
3. **A brand-new politician's wealth** — one TSE call for their `bens`, then cached.

Everything else is permanent. A package can even be **versioned/frozen** (e.g. *wealth-taxation @
2026-06*) for a reproducible, auditable public tool.

---

## 5. How this lands in the existing schema

The `topics → laws → keywords` tables already exist (discovery fills them). The package's frozen
voting data needs a **vote cache** — two new tables:

```sql
-- one row per roll-call of a package law (deputy-independent, immutable)
votacoes(
  id TEXT PRIMARY KEY,            -- Câmara votação id (e.g. "2196833-326")
  law_id INT,                    -- FK -> laws
  date TEXT,
  description TEXT,
  is_nominal BOOL,               -- had a real /votos roll-call
  gov_orientation TEXT,          -- Governo line: Sim/Não  (from /orientacoes)
  opp_orientation TEXT           -- Oposição line
)

-- the full roll-call: every deputy's vote (this is what makes re-fetch unnecessary)
votos(
  votacao_id TEXT,               -- FK -> votacoes
  camara_deputado_id INT,        -- the voter
  tipo_voto TEXT,                -- Sim/Não/Abstenção/Obstrução/Artigo 17
  PRIMARY KEY (votacao_id, camara_deputado_id)
)
```

Then `score_camara_candidate` stops calling the API for votes and instead does:

```sql
SELECT tipo_voto FROM votos
 WHERE camara_deputado_id = :id
   AND votacao_id IN (the package's votações);
```

`infer_law_vote`'s live fetching moves into a **one-time ingestion step** that populates these
tables when the package is built or refreshed.

---

## 6. Workflow summary

```
BUILD ONCE:   discover laws → ingest each law's votações + /votos + /orientacoes → store package
SCORE ANYONE: look up their votes in the cached roll-calls (+ fetch their wealth once)
COMPARE:      every politician measured against the same stored package → from cache, no API
REFRESH:      only when a package law gets a new vote, or you curate the package
```

**Net effect:** "prepare a package of laws once (e.g. wealth taxation), and never research those
laws again" — exactly the goal. New political figures are compared against the stored package; the
laws and their roll-calls are fetched a single time, forever.

---

## 7. Relationship to the integration plan
This makes a **vote-cache layer** a first-class integration item (a 4th, alongside discovery,
gov/opp alignment, and mandate scoping in [`11-integration-plan.md`](11-integration-plan.md)):
it is what turns discovery's output into a reusable package and removes per-politician law fetching.
