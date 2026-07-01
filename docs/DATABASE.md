# Database model for scorecards

*Working implementation note for the local MySQL scorecard layer. Added on 2026-06-26;
updated for Docker Compose + MySQL on 2026-06-26.*

The scorecard database follows the chain:

```text
topics -> laws -> keywords -> scores <- politics
```

## Current tech stack

| Layer | Technology |
|---|---|
| Local environment | Docker Compose |
| Database | MySQL 8.4 |
| Backend/API | Python 3.12 standard-library HTTP server |
| Database driver | PyMySQL |
| Frontend | Static HTML/CSS/JavaScript served by the Python app |
| External sources | Câmara Dados Abertos and TSE DivulgaCandContas |

## Architecture

```text
Câmara/TSE APIs
    |
    v
app/score_candidate.py -> MySQL <- app/server.py -> app/index.html
```

The script scores one politician at a time and persists the calculated rows in `scores`. The API
then serves the persisted scorecards and reference tree to the frontend.

## Tables

| Table | Role |
|---|---|
| `topics` | Broad issue areas, such as `tributacao-da-riqueza`. |
| `laws` | Câmara propositions connected to one topic. Stores the Câmara proposition id, label, source URL, and whether the law is a key wealth signal. |
| `keywords` | Search/scoring concepts under a law, such as offshore, fundos exclusivos, or dividendos. The `direction` field says what a `Sim` vote means for that keyword: `+1`, `-1`, or `0` for context-only. |
| `politics` | Politicians/candidates keyed by `camara_id`, with TSE election identifiers and declared-asset buckets. |
| `scores` | The join table between one `politic` and one `keyword`. It stores the calculated score, the asset-exposure context value, vote label, presence counts, and evidence JSON. |

## Runtime flow

1. `app/db.py` connects to MySQL, creates the schema, and seeds the initial topic/law/keyword reference data.
2. `app/score_candidate.py` fetches one politician from Câmara and TSE, resolves the TSE candidate when possible, calculates scores for every seeded keyword, and upserts into `scores`.
3. `app/server.py` exposes candidate search, on-demand scoring, and stored scorecards.
4. `app/index.html` searches candidates and renders scorecards through the local API; it no longer calls Câmara/TSE directly.

## API surface

| Endpoint | Method | Role |
|---|---|---|
| `/api/candidates/search?q=nome` | `GET` | Searches Câmara deputies by name and returns candidate choices. |
| `/api/scorecards` | `GET` | Lists stored scorecards from MySQL. |
| `/api/scorecards` | `POST` | Accepts `{"camara_id": 123}`. Returns cached MySQL data when present, or calculates and stores the scorecard. |
| `/api/scorecards/{camara_id}` | `GET` | Reads one stored scorecard. |
| `/api/politics` | `GET` | Lists stored politicians. |
| `/api/topics` | `GET` | Lists the topic/law/keyword reference tree. |

## Local environment

```bash
docker compose up --build
```

The app is served at <http://127.0.0.1:8765>. The MySQL service is exposed locally on port `3306`
with:

| Setting | Value |
|---|---|
| Database | `candidato` |
| User | `candidato` |
| Password | `candidato` |
| Container URL | `mysql://candidato:candidato@mysql:3306/candidato` |
| Host URL | `mysql://candidato:candidato@127.0.0.1:3306/candidato` |

To populate the scorecard data:

```bash
docker compose run --rm app python app/score_candidate.py
```

The MySQL data lives in the Docker volume `candidatos_candidato_mysql_data` by default. MySQL is
the only supported application database; set `DATABASE_URL` to a MySQL URL when running outside
Compose.
