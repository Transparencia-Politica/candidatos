#!/usr/bin/env python3
"""MySQL data layer for Candidato scorecards."""
from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from typing import Any
from urllib.parse import unquote, urlparse


APP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(APP_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "data")
DEFAULT_DATABASE_URL = "mysql://candidato:candidato@127.0.0.1:3306/candidato"
DATABASE_URL = (
    os.environ.get("DATABASE_URL")
    or os.environ.get("CANDIDATO_DATABASE_URL")
    or os.environ.get("CANDIDATO_DB")
    or DEFAULT_DATABASE_URL
)
DB_PATH = DATABASE_URL


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def as_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def from_json(value: str | None, fallback: Any = None) -> Any:
    if not value:
        return {} if fallback is None else fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {} if fallback is None else fallback


class MySQLResult:
    def __init__(self, cursor: Any):
        self.lastrowid = getattr(cursor, "lastrowid", None)
        self.rowcount = getattr(cursor, "rowcount", 0)
        self._rows = list(cursor.fetchall()) if cursor.description else []
        cursor.close()

    def fetchall(self) -> list[dict[str, Any]]:
        return self._rows

    def fetchone(self) -> dict[str, Any] | None:
        return self._rows[0] if self._rows else None

    def __iter__(self):
        return iter(self._rows)


class MySQLConnection:
    dialect = "mysql"

    def __init__(self, raw: Any):
        self.raw = raw

    def execute(self, sql: str, params: Any = None) -> MySQLResult:
        cursor = self.raw.cursor()
        cursor.execute(mysql_sql(sql), params)
        return MySQLResult(cursor)

    def executescript(self, script: str) -> None:
        for statement in split_sql_script(script):
            self.execute(statement)

    def commit(self) -> None:
        self.raw.commit()

    def close(self) -> None:
        self.raw.close()


def mysql_sql(sql: str) -> str:
    sql = re.sub(r":([A-Za-z_][A-Za-z0-9_]*)", r"%(\1)s", sql)
    return sql.replace("?", "%s")


def split_sql_script(script: str) -> list[str]:
    return [statement.strip() for statement in script.split(";") if statement.strip()]


def is_sqlite_target(target: str) -> bool:
    return (
        target.startswith("sqlite:///")
        or target.endswith(".db")
        or target.endswith(".sqlite")
        or target.endswith(".sqlite3")
        or "://" not in target
    )


def connect(database_url: str | None = None) -> sqlite3.Connection | MySQLConnection:
    target = database_url or DATABASE_URL
    if is_sqlite_target(target):
        db_path = target.removeprefix("sqlite:///")
        if not os.path.isabs(db_path):
            db_path = os.path.abspath(db_path)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    parsed = urlparse(target)
    if parsed.scheme not in ("mysql", "mysql+pymysql"):
        raise ValueError(f"Unsupported DATABASE_URL scheme: {parsed.scheme}")
    try:
        import pymysql
        import pymysql.cursors
    except ImportError as exc:
        raise RuntimeError("MySQL support requires PyMySQL. Install dependencies with `pip install -r requirements.txt`.") from exc

    raw = pymysql.connect(
        host=parsed.hostname or "127.0.0.1",
        port=parsed.port or 3306,
        user=unquote(parsed.username or ""),
        password=unquote(parsed.password or ""),
        database=(parsed.path or "/").lstrip("/"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )
    return MySQLConnection(raw)


SCHEMA_MYSQL = """
CREATE TABLE IF NOT EXISTS topics (
  id INT AUTO_INCREMENT PRIMARY KEY,
  slug VARCHAR(160) NOT NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT NOT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at VARCHAR(32) NOT NULL DEFAULT '',
  UNIQUE KEY uq_topics_slug (slug)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS laws (
  id INT AUTO_INCREMENT PRIMARY KEY,
  topic_id INT NOT NULL,
  slug VARCHAR(160) NOT NULL,
  camara_proposicao_id INT NOT NULL,
  label VARCHAR(255) NOT NULL,
  kind VARCHAR(32) NOT NULL,
  number VARCHAR(32) NOT NULL,
  year INT NOT NULL,
  description TEXT NOT NULL,
  source_url TEXT NOT NULL,
  is_key TINYINT(1) NOT NULL DEFAULT 0,
  wealth_relevant TINYINT(1) NOT NULL DEFAULT 1,
  sort_order INT NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at VARCHAR(32) NOT NULL DEFAULT '',
  UNIQUE KEY uq_laws_slug (slug),
  UNIQUE KEY uq_laws_camara_proposicao_id (camara_proposicao_id),
  KEY idx_laws_topic (topic_id),
  CONSTRAINT fk_laws_topic FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS keywords (
  id INT AUTO_INCREMENT PRIMARY KEY,
  law_id INT NOT NULL,
  slug VARCHAR(160) NOT NULL,
  label VARCHAR(255) NOT NULL,
  description TEXT NOT NULL,
  direction INT NOT NULL DEFAULT 1,
  weight DOUBLE NOT NULL DEFAULT 1.0,
  wealth_relevant TINYINT(1) NOT NULL DEFAULT 1,
  sort_order INT NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at VARCHAR(32) NOT NULL DEFAULT '',
  UNIQUE KEY uq_keywords_slug (slug),
  KEY idx_keywords_law (law_id),
  CONSTRAINT fk_keywords_law FOREIGN KEY (law_id) REFERENCES laws(id) ON DELETE CASCADE,
  CONSTRAINT chk_keywords_direction CHECK (direction IN (-1, 0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS politics (
  id INT AUTO_INCREMENT PRIMARY KEY,
  camara_id INT NOT NULL,
  tse_sq VARCHAR(64),
  tse_year INT,
  tse_uf VARCHAR(2),
  tse_election_id VARCHAR(64),
  name VARCHAR(255) NOT NULL,
  party VARCHAR(64) NOT NULL DEFAULT '',
  uf VARCHAR(2) NOT NULL DEFAULT '',
  birth_date VARCHAR(32),
  occupation VARCHAR(255) NOT NULL DEFAULT '',
  profile_json LONGTEXT NOT NULL,
  wealth_total DOUBLE NOT NULL DEFAULT 0,
  wealth_capital DOUBLE NOT NULL DEFAULT 0,
  wealth_buckets_json LONGTEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at VARCHAR(32) NOT NULL DEFAULT '',
  UNIQUE KEY uq_politics_camara_id (camara_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS scores (
  id INT AUTO_INCREMENT PRIMARY KEY,
  politic_id INT NOT NULL,
  keyword_id INT NOT NULL,
  score_value DOUBLE,
  self_interest_value DOUBLE,
  vote_status VARCHAR(64) NOT NULL,
  vote_label VARCHAR(160) NOT NULL,
  stance VARCHAR(64),
  present_count INT NOT NULL DEFAULT 0,
  nominal_count INT NOT NULL DEFAULT 0,
  coverage_value DOUBLE NOT NULL DEFAULT 0,
  evidence_json LONGTEXT NOT NULL,
  calculated_at VARCHAR(32) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at VARCHAR(32) NOT NULL DEFAULT '',
  UNIQUE KEY uq_scores_politic_keyword (politic_id, keyword_id),
  KEY idx_scores_politic (politic_id),
  KEY idx_scores_keyword (keyword_id),
  CONSTRAINT fk_scores_politic FOREIGN KEY (politic_id) REFERENCES politics(id) ON DELETE CASCADE,
  CONSTRAINT fk_scores_keyword FOREIGN KEY (keyword_id) REFERENCES keywords(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""


SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS topics (
  id INTEGER PRIMARY KEY,
  slug TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS laws (
  id INTEGER PRIMARY KEY,
  topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
  slug TEXT NOT NULL UNIQUE,
  camara_proposicao_id INTEGER NOT NULL UNIQUE,
  label TEXT NOT NULL,
  kind TEXT NOT NULL,
  number TEXT NOT NULL,
  year INTEGER NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  source_url TEXT NOT NULL DEFAULT '',
  is_key INTEGER NOT NULL DEFAULT 0,
  wealth_relevant INTEGER NOT NULL DEFAULT 1,
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS keywords (
  id INTEGER PRIMARY KEY,
  law_id INTEGER NOT NULL REFERENCES laws(id) ON DELETE CASCADE,
  slug TEXT NOT NULL UNIQUE,
  label TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  direction INTEGER NOT NULL DEFAULT 1 CHECK (direction IN (-1, 0, 1)),
  weight REAL NOT NULL DEFAULT 1.0,
  wealth_relevant INTEGER NOT NULL DEFAULT 1,
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS politics (
  id INTEGER PRIMARY KEY,
  camara_id INTEGER NOT NULL UNIQUE,
  tse_sq TEXT,
  tse_year INTEGER,
  tse_uf TEXT,
  tse_election_id TEXT,
  name TEXT NOT NULL,
  party TEXT NOT NULL DEFAULT '',
  uf TEXT NOT NULL DEFAULT '',
  birth_date TEXT,
  occupation TEXT NOT NULL DEFAULT '',
  profile_json TEXT NOT NULL DEFAULT '{}',
  wealth_total REAL NOT NULL DEFAULT 0,
  wealth_capital REAL NOT NULL DEFAULT 0,
  wealth_buckets_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scores (
  id INTEGER PRIMARY KEY,
  politic_id INTEGER NOT NULL REFERENCES politics(id) ON DELETE CASCADE,
  keyword_id INTEGER NOT NULL REFERENCES keywords(id) ON DELETE CASCADE,
  score_value REAL,
  self_interest_value REAL,
  vote_status TEXT NOT NULL,
  vote_label TEXT NOT NULL,
  stance TEXT,
  present_count INTEGER NOT NULL DEFAULT 0,
  nominal_count INTEGER NOT NULL DEFAULT 0,
  coverage_value REAL NOT NULL DEFAULT 0,
  evidence_json TEXT NOT NULL DEFAULT '{}',
  calculated_at TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (politic_id, keyword_id)
);

CREATE INDEX IF NOT EXISTS idx_laws_topic ON laws(topic_id);
CREATE INDEX IF NOT EXISTS idx_keywords_law ON keywords(law_id);
CREATE INDEX IF NOT EXISTS idx_scores_politic ON scores(politic_id);
CREATE INDEX IF NOT EXISTS idx_scores_keyword ON scores(keyword_id);
"""


TOPICS = [
    {
        "slug": "tributacao-da-riqueza",
        "title": "Tributação da riqueza",
        "description": "Projetos que afetam renda de capital, dividendos, fundos exclusivos e ativos no exterior.",
        "sort_order": 10,
    },
    {
        "slug": "reforma-tributaria",
        "title": "Reforma tributária",
        "description": "Projetos tributários amplos usados como contexto, mesmo quando não medem riqueza diretamente.",
        "sort_order": 20,
    },
]


LAWS = [
    {
        "topic_slug": "tributacao-da-riqueza",
        "slug": "pl-4173-2023",
        "camara_proposicao_id": 2383287,
        "label": "PL 4173/2023",
        "kind": "PL",
        "number": "4173",
        "year": 2023,
        "description": "Tributa renda no exterior e fundos exclusivos.",
        "source_url": "https://dadosabertos.camara.leg.br/api/v2/proposicoes/2383287",
        "is_key": 1,
        "wealth_relevant": 1,
        "sort_order": 10,
    },
    {
        "topic_slug": "tributacao-da-riqueza",
        "slug": "pl-2337-2021",
        "camara_proposicao_id": 2288389,
        "label": "PL 2337/2021",
        "kind": "PL",
        "number": "2337",
        "year": 2021,
        "description": "Reforma do imposto de renda, incluindo tributação de dividendos.",
        "source_url": "https://dadosabertos.camara.leg.br/api/v2/proposicoes/2288389",
        "is_key": 0,
        "wealth_relevant": 1,
        "sort_order": 20,
    },
    {
        "topic_slug": "reforma-tributaria",
        "slug": "pec-45-2019",
        "camara_proposicao_id": 2196833,
        "label": "PEC 45/2019",
        "kind": "PEC",
        "number": "45",
        "year": 2019,
        "description": "Reforma tributária sobre consumo; contexto fraco para patrimônio pessoal.",
        "source_url": "https://dadosabertos.camara.leg.br/api/v2/proposicoes/2196833",
        "is_key": 0,
        "wealth_relevant": 0,
        "sort_order": 30,
    },
]


KEYWORDS = [
    {
        "law_slug": "pl-4173-2023",
        "slug": "offshore",
        "label": "Offshore",
        "description": "Renda auferida por pessoas físicas em entidades controladas no exterior.",
        "direction": 1,
        "weight": 1.0,
        "wealth_relevant": 1,
        "sort_order": 10,
    },
    {
        "law_slug": "pl-4173-2023",
        "slug": "fundos-exclusivos",
        "label": "Fundos exclusivos",
        "description": "Tributação periódica de fundos exclusivos.",
        "direction": 1,
        "weight": 1.0,
        "wealth_relevant": 1,
        "sort_order": 20,
    },
    {
        "law_slug": "pl-2337-2021",
        "slug": "dividendos",
        "label": "Dividendos",
        "description": "Tributação de lucros e dividendos distribuídos.",
        "direction": 1,
        "weight": 1.0,
        "wealth_relevant": 1,
        "sort_order": 30,
    },
    {
        "law_slug": "pec-45-2019",
        "slug": "tributacao-do-consumo",
        "label": "Tributação do consumo",
        "description": "Reorganização de impostos sobre consumo, sem medir diretamente patrimônio pessoal.",
        "direction": 0,
        "weight": 0.4,
        "wealth_relevant": 0,
        "sort_order": 40,
    },
]


def is_mysql(conn: sqlite3.Connection | MySQLConnection) -> bool:
    return getattr(conn, "dialect", "sqlite") == "mysql"


def init_db(database_url: str | None = None) -> sqlite3.Connection | MySQLConnection:
    conn = connect(database_url)
    conn.executescript(SCHEMA_MYSQL if is_mysql(conn) else SCHEMA_SQLITE)
    seed_reference_data(conn)
    conn.commit()
    return conn


def seed_reference_data(conn: sqlite3.Connection | MySQLConnection) -> None:
    for topic in TOPICS:
        payload = {**topic, "updated_at": now_iso()}
        if is_mysql(conn):
            conn.execute(
                """
                INSERT INTO topics (slug, title, description, sort_order, updated_at)
                VALUES (:slug, :title, :description, :sort_order, :updated_at)
                ON DUPLICATE KEY UPDATE
                  title = VALUES(title),
                  description = VALUES(description),
                  sort_order = VALUES(sort_order),
                  updated_at = VALUES(updated_at)
                """,
                payload,
            )
        else:
            conn.execute(
                """
                INSERT INTO topics (slug, title, description, sort_order, updated_at)
                VALUES (:slug, :title, :description, :sort_order, :updated_at)
                ON CONFLICT(slug) DO UPDATE SET
                  title = excluded.title,
                  description = excluded.description,
                  sort_order = excluded.sort_order,
                  updated_at = excluded.updated_at
                """,
                payload,
            )

    topic_ids = {row["slug"]: row["id"] for row in conn.execute("SELECT id, slug FROM topics")}
    for law in LAWS:
        payload = {**law, "topic_id": topic_ids[law["topic_slug"]], "updated_at": now_iso()}
        if is_mysql(conn):
            conn.execute(
                """
                INSERT INTO laws (
                  topic_id, slug, camara_proposicao_id, label, kind, number, year,
                  description, source_url, is_key, wealth_relevant, sort_order, updated_at
                )
                VALUES (
                  :topic_id, :slug, :camara_proposicao_id, :label, :kind, :number, :year,
                  :description, :source_url, :is_key, :wealth_relevant, :sort_order, :updated_at
                )
                ON DUPLICATE KEY UPDATE
                  topic_id = VALUES(topic_id),
                  slug = VALUES(slug),
                  camara_proposicao_id = VALUES(camara_proposicao_id),
                  label = VALUES(label),
                  kind = VALUES(kind),
                  number = VALUES(number),
                  year = VALUES(year),
                  description = VALUES(description),
                  source_url = VALUES(source_url),
                  is_key = VALUES(is_key),
                  wealth_relevant = VALUES(wealth_relevant),
                  sort_order = VALUES(sort_order),
                  updated_at = VALUES(updated_at)
                """,
                payload,
            )
        else:
            conn.execute(
                """
                INSERT INTO laws (
                  topic_id, slug, camara_proposicao_id, label, kind, number, year,
                  description, source_url, is_key, wealth_relevant, sort_order, updated_at
                )
                VALUES (
                  :topic_id, :slug, :camara_proposicao_id, :label, :kind, :number, :year,
                  :description, :source_url, :is_key, :wealth_relevant, :sort_order, :updated_at
                )
                ON CONFLICT(slug) DO UPDATE SET
                  topic_id = excluded.topic_id,
                  camara_proposicao_id = excluded.camara_proposicao_id,
                  label = excluded.label,
                  kind = excluded.kind,
                  number = excluded.number,
                  year = excluded.year,
                  description = excluded.description,
                  source_url = excluded.source_url,
                  is_key = excluded.is_key,
                  wealth_relevant = excluded.wealth_relevant,
                  sort_order = excluded.sort_order,
                  updated_at = excluded.updated_at
                """,
                payload,
            )

    law_ids = {row["slug"]: row["id"] for row in conn.execute("SELECT id, slug FROM laws")}
    for keyword in KEYWORDS:
        payload = {**keyword, "law_id": law_ids[keyword["law_slug"]], "updated_at": now_iso()}
        if is_mysql(conn):
            conn.execute(
                """
                INSERT INTO keywords (
                  law_id, slug, label, description, direction, weight,
                  wealth_relevant, sort_order, updated_at
                )
                VALUES (
                  :law_id, :slug, :label, :description, :direction, :weight,
                  :wealth_relevant, :sort_order, :updated_at
                )
                ON DUPLICATE KEY UPDATE
                  law_id = VALUES(law_id),
                  label = VALUES(label),
                  description = VALUES(description),
                  direction = VALUES(direction),
                  weight = VALUES(weight),
                  wealth_relevant = VALUES(wealth_relevant),
                  sort_order = VALUES(sort_order),
                  updated_at = VALUES(updated_at)
                """,
                payload,
            )
        else:
            conn.execute(
                """
                INSERT INTO keywords (
                  law_id, slug, label, description, direction, weight,
                  wealth_relevant, sort_order, updated_at
                )
                VALUES (
                  :law_id, :slug, :label, :description, :direction, :weight,
                  :wealth_relevant, :sort_order, :updated_at
                )
                ON CONFLICT(slug) DO UPDATE SET
                  law_id = excluded.law_id,
                  label = excluded.label,
                  description = excluded.description,
                  direction = excluded.direction,
                  weight = excluded.weight,
                  wealth_relevant = excluded.wealth_relevant,
                  sort_order = excluded.sort_order,
                  updated_at = excluded.updated_at
                """,
                payload,
            )


def list_laws_with_keywords(conn: sqlite3.Connection | MySQLConnection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
          l.*, t.slug AS topic_slug, t.title AS topic_title,
          k.id AS keyword_id, k.slug AS keyword_slug, k.label AS keyword_label,
          k.description AS keyword_description, k.direction AS keyword_direction,
          k.weight AS keyword_weight, k.wealth_relevant AS keyword_wealth_relevant,
          k.sort_order AS keyword_sort_order
        FROM laws l
        JOIN topics t ON t.id = l.topic_id
        JOIN keywords k ON k.law_id = l.id
        ORDER BY t.sort_order, l.sort_order, k.sort_order
        """
    ).fetchall()
    laws: dict[int, dict[str, Any]] = {}
    for row in rows:
        law = laws.setdefault(
            row["id"],
            {
                "id": row["id"],
                "topic_id": row["topic_id"],
                "topic_slug": row["topic_slug"],
                "topic_title": row["topic_title"],
                "slug": row["slug"],
                "camara_proposicao_id": row["camara_proposicao_id"],
                "label": row["label"],
                "kind": row["kind"],
                "number": row["number"],
                "year": row["year"],
                "description": row["description"],
                "source_url": row["source_url"],
                "is_key": bool(row["is_key"]),
                "wealth_relevant": bool(row["wealth_relevant"]),
                "sort_order": row["sort_order"],
                "keywords": [],
            },
        )
        law["keywords"].append(
            {
                "id": row["keyword_id"],
                "slug": row["keyword_slug"],
                "label": row["keyword_label"],
                "description": row["keyword_description"],
                "direction": row["keyword_direction"],
                "weight": row["keyword_weight"],
                "wealth_relevant": bool(row["keyword_wealth_relevant"]),
                "sort_order": row["keyword_sort_order"],
            }
        )
    return list(laws.values())


def list_topics(conn: sqlite3.Connection | MySQLConnection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
          t.id AS topic_id, t.slug AS topic_slug, t.title AS topic_title,
          t.description AS topic_description,
          l.id AS law_id, l.slug AS law_slug, l.camara_proposicao_id,
          l.label AS law_label, l.kind, l.number, l.year,
          l.description AS law_description, l.source_url, l.is_key,
          l.wealth_relevant AS law_wealth_relevant,
          k.id AS keyword_id, k.slug AS keyword_slug, k.label AS keyword_label,
          k.description AS keyword_description, k.direction, k.weight,
          k.wealth_relevant AS keyword_wealth_relevant
        FROM topics t
        JOIN laws l ON l.topic_id = t.id
        JOIN keywords k ON k.law_id = l.id
        ORDER BY t.sort_order, l.sort_order, k.sort_order
        """
    ).fetchall()

    topics: dict[int, dict[str, Any]] = {}
    laws_by_topic: dict[tuple[int, int], dict[str, Any]] = {}
    for row in rows:
        topic = topics.setdefault(
            row["topic_id"],
            {
                "id": row["topic_id"],
                "slug": row["topic_slug"],
                "title": row["topic_title"],
                "description": row["topic_description"],
                "laws": [],
            },
        )
        law_key = (row["topic_id"], row["law_id"])
        law = laws_by_topic.get(law_key)
        if law is None:
            law = {
                "id": row["law_id"],
                "slug": row["law_slug"],
                "camara_proposicao_id": row["camara_proposicao_id"],
                "label": row["law_label"],
                "kind": row["kind"],
                "number": row["number"],
                "year": row["year"],
                "description": row["law_description"],
                "source_url": row["source_url"],
                "is_key": bool(row["is_key"]),
                "wealth_relevant": bool(row["law_wealth_relevant"]),
                "keywords": [],
            }
            laws_by_topic[law_key] = law
            topic["laws"].append(law)
        law["keywords"].append(
            {
                "id": row["keyword_id"],
                "slug": row["keyword_slug"],
                "label": row["keyword_label"],
                "description": row["keyword_description"],
                "direction": row["direction"],
                "weight": row["weight"],
                "wealth_relevant": bool(row["keyword_wealth_relevant"]),
            }
        )
    return list(topics.values())


def upsert_politic(
    conn: sqlite3.Connection | MySQLConnection,
    *,
    camara_id: int,
    tse_sq: str,
    tse_year: int,
    tse_uf: str,
    tse_election_id: str,
    name: str,
    party: str,
    uf: str,
    birth_date: str | None,
    occupation: str,
    profile: dict[str, Any],
    wealth_total: float,
    wealth_capital: float,
    wealth_buckets: dict[str, float],
) -> int:
    payload = {
        "camara_id": camara_id,
        "tse_sq": tse_sq,
        "tse_year": tse_year,
        "tse_uf": tse_uf,
        "tse_election_id": tse_election_id,
        "name": name,
        "party": party,
        "uf": uf,
        "birth_date": birth_date,
        "occupation": occupation,
        "profile_json": as_json(profile),
        "wealth_total": wealth_total,
        "wealth_capital": wealth_capital,
        "wealth_buckets_json": as_json(wealth_buckets),
        "updated_at": now_iso(),
    }
    if is_mysql(conn):
        conn.execute(
            """
            INSERT INTO politics (
              camara_id, tse_sq, tse_year, tse_uf, tse_election_id, name, party, uf,
              birth_date, occupation, profile_json, wealth_total, wealth_capital,
              wealth_buckets_json, updated_at
            )
            VALUES (
              :camara_id, :tse_sq, :tse_year, :tse_uf, :tse_election_id, :name, :party, :uf,
              :birth_date, :occupation, :profile_json, :wealth_total, :wealth_capital,
              :wealth_buckets_json, :updated_at
            )
            ON DUPLICATE KEY UPDATE
              tse_sq = VALUES(tse_sq),
              tse_year = VALUES(tse_year),
              tse_uf = VALUES(tse_uf),
              tse_election_id = VALUES(tse_election_id),
              name = VALUES(name),
              party = VALUES(party),
              uf = VALUES(uf),
              birth_date = VALUES(birth_date),
              occupation = VALUES(occupation),
              profile_json = VALUES(profile_json),
              wealth_total = VALUES(wealth_total),
              wealth_capital = VALUES(wealth_capital),
              wealth_buckets_json = VALUES(wealth_buckets_json),
              updated_at = VALUES(updated_at)
            """,
            payload,
        )
    else:
        conn.execute(
            """
            INSERT INTO politics (
              camara_id, tse_sq, tse_year, tse_uf, tse_election_id, name, party, uf,
              birth_date, occupation, profile_json, wealth_total, wealth_capital,
              wealth_buckets_json, updated_at
            )
            VALUES (
              :camara_id, :tse_sq, :tse_year, :tse_uf, :tse_election_id, :name, :party, :uf,
              :birth_date, :occupation, :profile_json, :wealth_total, :wealth_capital,
              :wealth_buckets_json, :updated_at
            )
            ON CONFLICT(camara_id) DO UPDATE SET
              tse_sq = excluded.tse_sq,
              tse_year = excluded.tse_year,
              tse_uf = excluded.tse_uf,
              tse_election_id = excluded.tse_election_id,
              name = excluded.name,
              party = excluded.party,
              uf = excluded.uf,
              birth_date = excluded.birth_date,
              occupation = excluded.occupation,
              profile_json = excluded.profile_json,
              wealth_total = excluded.wealth_total,
              wealth_capital = excluded.wealth_capital,
              wealth_buckets_json = excluded.wealth_buckets_json,
              updated_at = excluded.updated_at
            """,
            payload,
        )
    row = conn.execute("SELECT id FROM politics WHERE camara_id = ?", (camara_id,)).fetchone()
    return int(row["id"])


def upsert_score(
    conn: sqlite3.Connection | MySQLConnection,
    *,
    politic_id: int,
    keyword_id: int,
    score_value: float | None,
    self_interest_value: float | None,
    vote_status: str,
    vote_label: str,
    stance: str | None,
    present_count: int,
    nominal_count: int,
    coverage_value: float,
    evidence: dict[str, Any],
) -> None:
    payload = {
        "politic_id": politic_id,
        "keyword_id": keyword_id,
        "score_value": score_value,
        "self_interest_value": self_interest_value,
        "vote_status": vote_status,
        "vote_label": vote_label,
        "stance": stance,
        "present_count": present_count,
        "nominal_count": nominal_count,
        "coverage_value": coverage_value,
        "evidence_json": as_json(evidence),
        "calculated_at": now_iso(),
        "updated_at": now_iso(),
    }
    if is_mysql(conn):
        conn.execute(
            """
            INSERT INTO scores (
              politic_id, keyword_id, score_value, self_interest_value, vote_status,
              vote_label, stance, present_count, nominal_count, coverage_value,
              evidence_json, calculated_at, updated_at
            )
            VALUES (
              :politic_id, :keyword_id, :score_value, :self_interest_value, :vote_status,
              :vote_label, :stance, :present_count, :nominal_count, :coverage_value,
              :evidence_json, :calculated_at, :updated_at
            )
            ON DUPLICATE KEY UPDATE
              score_value = VALUES(score_value),
              self_interest_value = VALUES(self_interest_value),
              vote_status = VALUES(vote_status),
              vote_label = VALUES(vote_label),
              stance = VALUES(stance),
              present_count = VALUES(present_count),
              nominal_count = VALUES(nominal_count),
              coverage_value = VALUES(coverage_value),
              evidence_json = VALUES(evidence_json),
              calculated_at = VALUES(calculated_at),
              updated_at = VALUES(updated_at)
            """,
            payload,
        )
    else:
        conn.execute(
            """
            INSERT INTO scores (
              politic_id, keyword_id, score_value, self_interest_value, vote_status,
              vote_label, stance, present_count, nominal_count, coverage_value,
              evidence_json, calculated_at, updated_at
            )
            VALUES (
              :politic_id, :keyword_id, :score_value, :self_interest_value, :vote_status,
              :vote_label, :stance, :present_count, :nominal_count, :coverage_value,
              :evidence_json, :calculated_at, :updated_at
            )
            ON CONFLICT(politic_id, keyword_id) DO UPDATE SET
              score_value = excluded.score_value,
              self_interest_value = excluded.self_interest_value,
              vote_status = excluded.vote_status,
              vote_label = excluded.vote_label,
              stance = excluded.stance,
              present_count = excluded.present_count,
              nominal_count = excluded.nominal_count,
              coverage_value = excluded.coverage_value,
              evidence_json = excluded.evidence_json,
              calculated_at = excluded.calculated_at,
              updated_at = excluded.updated_at
            """,
            payload,
        )


def list_politics(conn: sqlite3.Connection | MySQLConnection) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT * FROM politics ORDER BY name").fetchall()
    return [_politic_payload(row) for row in rows]


def get_scorecards(conn: sqlite3.Connection | MySQLConnection, camara_id: int | None = None) -> dict[str, Any]:
    params: tuple[Any, ...] = ()
    where = ""
    if camara_id is not None:
        where = "WHERE camara_id = ?"
        params = (camara_id,)
    politics = conn.execute(f"SELECT * FROM politics {where} ORDER BY name", params).fetchall()
    cards = [get_scorecard_for_politic(conn, row) for row in politics]
    return {"generated_at": now_iso(), "scorecards": cards}


def get_scorecard_for_politic(conn: sqlite3.Connection | MySQLConnection, politic_row: dict[str, Any]) -> dict[str, Any]:
    topics = _topics_for_politic(conn, int(politic_row["id"]))
    rows = conn.execute(
        """
        SELECT
          s.*, k.wealth_relevant AS keyword_wealth_relevant, l.id AS law_id,
          l.is_key, l.wealth_relevant AS law_wealth_relevant
        FROM scores s
        JOIN keywords k ON k.id = s.keyword_id
        JOIN laws l ON l.id = k.law_id
        WHERE s.politic_id = ?
        ORDER BY l.sort_order, k.sort_order
        """,
        (politic_row["id"],),
    ).fetchall()
    return {
        "politic": _politic_payload(politic_row),
        "summary": _summary(politic_row, rows),
        "topics": topics,
    }


def _politic_payload(row: dict[str, Any]) -> dict[str, Any]:
    wealth_total = float(row["wealth_total"] or 0)
    wealth_capital = float(row["wealth_capital"] or 0)
    return {
        "id": row["id"],
        "camara_id": row["camara_id"],
        "tse_sq": row["tse_sq"],
        "tse_year": row["tse_year"],
        "tse_uf": row["tse_uf"],
        "tse_election_id": row["tse_election_id"],
        "name": row["name"],
        "party": row["party"],
        "uf": row["uf"],
        "birth_date": row["birth_date"],
        "occupation": row["occupation"],
        "wealth_total": wealth_total,
        "wealth_capital": wealth_capital,
        "wealth_capital_pct": round(100 * wealth_capital / wealth_total) if wealth_total else 0,
        "wealth_buckets": from_json(row["wealth_buckets_json"], {}),
        "updated_at": row["updated_at"],
    }


def _score_payload(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None or row["score_id"] is None:
        return None
    return {
        "id": row["score_id"],
        "score_value": row["score_value"],
        "self_interest_value": row["self_interest_value"],
        "vote_status": row["vote_status"],
        "vote_label": row["vote_label"],
        "stance": row["stance"],
        "present_count": row["present_count"],
        "nominal_count": row["nominal_count"],
        "coverage_value": row["coverage_value"],
        "evidence": from_json(row["evidence_json"], {}),
        "calculated_at": row["calculated_at"],
    }


def _topics_for_politic(conn: sqlite3.Connection | MySQLConnection, politic_id: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
          t.id AS topic_id, t.slug AS topic_slug, t.title AS topic_title,
          t.description AS topic_description, t.sort_order AS topic_sort_order,
          l.id AS law_id, l.slug AS law_slug, l.camara_proposicao_id,
          l.label AS law_label, l.kind, l.number, l.year,
          l.description AS law_description, l.source_url, l.is_key,
          l.wealth_relevant AS law_wealth_relevant, l.sort_order AS law_sort_order,
          k.id AS keyword_id, k.slug AS keyword_slug, k.label AS keyword_label,
          k.description AS keyword_description, k.direction, k.weight,
          k.wealth_relevant AS keyword_wealth_relevant, k.sort_order AS keyword_sort_order,
          s.id AS score_id, s.score_value, s.self_interest_value, s.vote_status,
          s.vote_label, s.stance, s.present_count, s.nominal_count,
          s.coverage_value, s.evidence_json, s.calculated_at
        FROM topics t
        JOIN laws l ON l.topic_id = t.id
        JOIN keywords k ON k.law_id = l.id
        LEFT JOIN scores s ON s.keyword_id = k.id AND s.politic_id = ?
        ORDER BY t.sort_order, l.sort_order, k.sort_order
        """,
        (politic_id,),
    ).fetchall()

    topics: dict[int, dict[str, Any]] = {}
    laws_by_topic: dict[tuple[int, int], dict[str, Any]] = {}
    for row in rows:
        topic = topics.setdefault(
            row["topic_id"],
            {
                "id": row["topic_id"],
                "slug": row["topic_slug"],
                "title": row["topic_title"],
                "description": row["topic_description"],
                "laws": [],
            },
        )
        law_key = (row["topic_id"], row["law_id"])
        law = laws_by_topic.get(law_key)
        if law is None:
            law = {
                "id": row["law_id"],
                "slug": row["law_slug"],
                "camara_proposicao_id": row["camara_proposicao_id"],
                "label": row["law_label"],
                "kind": row["kind"],
                "number": row["number"],
                "year": row["year"],
                "description": row["law_description"],
                "source_url": row["source_url"],
                "is_key": bool(row["is_key"]),
                "wealth_relevant": bool(row["law_wealth_relevant"]),
                "score": None,
                "keywords": [],
            }
            laws_by_topic[law_key] = law
            topic["laws"].append(law)

        keyword_score = _score_payload(row)
        if law["score"] is None and keyword_score is not None:
            law["score"] = keyword_score
        law["keywords"].append(
            {
                "id": row["keyword_id"],
                "slug": row["keyword_slug"],
                "label": row["keyword_label"],
                "description": row["keyword_description"],
                "direction": row["direction"],
                "weight": row["weight"],
                "wealth_relevant": bool(row["keyword_wealth_relevant"]),
                "score": keyword_score,
            }
        )
    return list(topics.values())


def _summary(politic_row: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    wealth_total = float(politic_row["wealth_total"] or 0)
    wealth_capital = float(politic_row["wealth_capital"] or 0)
    by_law: dict[int, dict[str, Any]] = {}
    for row in rows:
        by_law.setdefault(row["law_id"], row)

    relevant_laws = [row for row in by_law.values() if row["law_wealth_relevant"]]
    recorded_laws = [row for row in relevant_laws if row["present_count"] > 0]
    key_law = next((row for row in by_law.values() if row["is_key"]), None)
    self_interest_rows = [
        row for row in relevant_laws
        if row["self_interest_value"] is not None and row["present_count"] > 0
    ]
    protect_count = sum(1 for row in self_interest_rows if float(row["self_interest_value"]) > 0)

    return {
        "wealth_capital_pct": round(100 * wealth_capital / wealth_total) if wealth_total else 0,
        "coverage_pct": round(100 * len(recorded_laws) / len(relevant_laws)) if relevant_laws else 0,
        "key_attendance_pct": (
            round(100 * key_law["present_count"] / key_law["nominal_count"])
            if key_law is not None and key_law["nominal_count"]
            else 0
        ),
        "self_interest_alignment_pct": (
            round(100 * protect_count / len(self_interest_rows))
            if self_interest_rows
            else None
        ),
        "self_interest_n": len(self_interest_rows),
        "relevant_laws_n": len(relevant_laws),
        "recorded_laws_n": len(recorded_laws),
    }
