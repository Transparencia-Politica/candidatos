#!/usr/bin/env python3
"""Bulk-scan the sitting Congress in parallel: enumerate every deputy + senator, score each.

This is the batch counterpart to on-demand single-politician scoring. It walks the two official
rosters and runs the *same* per-politician scoring used by the UI (so every result is identical to
scoring that person by hand), but across a thread pool — the work is network-bound, so threads
collapse the wall time roughly linearly with `--workers`.

How the crossing works (what we actually need from each roster entry):
  - Deputies — the Câmara `/deputados` list is **paginated** (`pagina`/`itens`); with no `itens`
    a single page returns the whole sitting roster (≈512). Each entry's `id` IS the join key into
    the cached roll-call votes (`votes.deputy_id`), so the vote crossing is a pure DB lookup — no
    extra fetch. The entry's `siglaUf` is passed as the TSE UF so scoring skips UF inference.
  - Senators — `/senador/lista/atual` is a single list of 81; each `CodigoParlamentar` is the join
    key into the cached Senado votes.

Concurrency safety: each scoring opens its own DB connection and writes only its own politic/score
rows, so workers don't contend. The schema/seed is created ONCE up front; workers run with
`init=False` so N threads never re-run the seed's upserts and deadlock. The TSE candidate list is
memoized per UF and pre-warmed before the pool, so 27 UF lists are fetched once, not per worker.

Learning the rate limits (we don't know the APIs' hard limits — so we measure them): every HTTP
request flows through `score_candidate.fetch_json`, which we instrument via `REQUEST_HOOK`. Each
request is written to a JSONL telemetry log with elapsed time, observed concurrency, rolling req/s,
status, latency, and any `Retry-After`; every 429/5xx prints a loud warning. Start at low `--workers`,
watch for the first 429, and that tells you where the API pushes back. `fetch_json` honors
`Retry-After`, backs off exponentially with jitter, and respects `HTTPS_PROXY` (urllib reads it from
the environment) — so adding a rotating proxy is a config change, not a code change.

Prerequisite: the vote cache (roll_calls/votes) must already be built — this job *crosses* against
it. Câmara cache: `ingest.ingest_all` (or `--ingest-cache`). Senado cache: built once here.
See research/15-bulk-roster-scan.md.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Iterator

try:
    import db
    import ingest
    import score_candidate as sc
    import senado
except ModuleNotFoundError:
    from app import db
    from app import ingest
    from app import score_candidate as sc
    from app import senado


class Telemetry:
    """Thread-safe sink for `score_candidate.REQUEST_HOOK`. Records every HTTP attempt so a bulk run
    can *learn* the APIs' throttling: counts by status/host, rolling req/s, observed concurrency, and
    a JSONL line per request. Loud on 429/5xx so the first sign of pushback is impossible to miss."""

    def __init__(self, path: str | None, log: Callable[[str], None]):
        self.log = log
        self.lock = threading.Lock()
        self.fh = open(path, "w", encoding="utf-8") if path else None
        self.t0 = time.monotonic()
        self.total = 0
        self.errors = 0
        self.r429 = 0
        self.inflight = 0          # scoring jobs currently running — a proxy for real concurrency
        self.by_status: dict[Any, int] = {}
        self.by_host: dict[str, int] = {}

    def job_enter(self) -> None:
        with self.lock:
            self.inflight += 1

    def job_exit(self) -> None:
        with self.lock:
            self.inflight -= 1

    def on_request(self, ev: dict[str, Any]) -> None:
        warn = None
        with self.lock:
            self.total += 1
            status = ev.get("status")
            self.by_status[status] = self.by_status.get(status, 0) + 1
            host = ev.get("host", "")
            self.by_host[host] = self.by_host.get(host, 0) + 1
            if status == 429:
                self.r429 += 1
            if ev.get("error"):
                self.errors += 1
            elapsed = time.monotonic() - self.t0
            rps = self.total / elapsed if elapsed > 0 else 0.0
            if self.fh:
                self.fh.write(json.dumps(
                    {"t": round(elapsed, 2), "concurrency": self.inflight, "rps": round(rps, 2), **ev},
                    ensure_ascii=False) + "\n")
                self.fh.flush()
            if status == 429:
                warn = (f"  ⚠ 429 THROTTLED by {host} — {self.total} reqs in, {rps:.1f} req/s, "
                        f"concurrency≈{self.inflight}, Retry-After={ev.get('retry_after')}")
            elif status in (500, 502, 503, 504):
                warn = f"  ⚠ {status} from {host} (req #{self.total}, {rps:.1f} req/s)"
        if warn:
            self.log(warn)

    def summary(self) -> dict[str, Any]:
        elapsed = time.monotonic() - self.t0
        return {
            "requests": self.total,
            "elapsed_s": round(elapsed, 1),
            "req_per_s": round(self.total / elapsed, 2) if elapsed > 0 else 0.0,
            "http_429": self.r429,
            "errors": self.errors,
            "by_status": self.by_status,
            "by_host": self.by_host,
        }

    def close(self) -> None:
        if self.fh:
            self.fh.close()


def iter_deputies(
    *, pages: int | None = 1, itens: int | None = None, pause: float = 0.0,
    fetch: Callable[[str], dict[str, Any]] = sc.fetch_json,
) -> Iterator[dict[str, Any]]:
    """Yield current deputies by following the Câmara `/deputados` pagination.

    Stops after `pages` pages (None = all pages, until no `rel:next` link). `itens` is the page
    size; **None means a whole page** — the Câmara default returns the entire sitting roster (≈512)
    in one page, so `pages=1, itens=None` is "the whole page = everyone". Pure HTTP against Câmara
    — needs no DB — so the pager can be smoke-tested in isolation.
    """
    itens_q = f"&itens={itens}" if itens else ""
    url = f"{sc.CAMARA}/deputados?ordem=ASC&ordenarPor=nome{itens_q}&pagina=1"
    page = 0
    while url:
        page += 1
        payload = fetch(url)
        for d in payload.get("dados", []):
            yield {
                "camara_id": d.get("id"),
                "name": d.get("nome"),
                "party": d.get("siglaPartido"),
                "uf": d.get("siglaUf"),
            }
        if pages is not None and page >= pages:
            return
        url = next((l.get("href") for l in payload.get("links", []) if l.get("rel") == "next"), None)
        if url and pause:
            time.sleep(pause)


def _camara_cache_count(database_url: str | None) -> int:
    conn = db.connect(database_url)
    try:
        row = conn.execute("SELECT COUNT(*) AS n FROM roll_calls WHERE house = 'camara'").fetchone()
        return int(row["n"]) if row else 0
    finally:
        conn.close()


def _prewarm_tse_lists(ufs: list[str], cargo: int, log: Callable[[str], None]) -> None:
    """Fetch each distinct UF's TSE candidate list once (sequentially), so the per-worker lookups
    all hit the warm `_tse_listar` cache — turning ≈len(roster) list calls into ≈len(UFs)."""
    e = sc.DEFAULT_ELECTION
    for uf in ufs:
        try:
            sc._tse_listar(e["tse_year"], uf, e["tse_election_id"], cargo)
        except Exception as exc:
            log(f"  (TSE list prewarm {uf} failed: {exc})")


def _retry_on_deadlock(fn: Callable[[], Any], tries: int = 3) -> Any:
    """Retry a unit of work on an InnoDB deadlock (MySQL 1213). With N concurrent writers, two
    transactions occasionally pick row locks in opposite order and one is chosen as the victim —
    a transient, by-design condition that just needs a re-run. Observed once in a 512-deputy run."""
    for attempt in range(1, tries + 1):
        try:
            return fn()
        except Exception as exc:
            if "Deadlock" in str(exc) and attempt < tries:
                time.sleep(0.3 * attempt + random.uniform(0, 0.3))
                continue
            raise


def _run_pool(items, work, workers: int) -> None:
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(work, i, it) for i, it in enumerate(items)]
        for fut in as_completed(futures):
            fut.result()  # `work` catches per-item errors; this only surfaces real bugs


def scan_deputies(
    *, pages: int | None = 1, itens: int | None = None, workers: int = 5, pause: float = 0.35,
    database_url: str | None = None, telemetry: Telemetry | None = None,
    log: Callable[[str], None] = print,
) -> dict[str, Any]:
    """Score every deputy across `pages` pages of the Câmara roster, concurrently. Per-deputy errors
    are caught so one unresolved TSE match never aborts the run."""
    if _camara_cache_count(database_url) == 0:
        log("  ⚠ Câmara vote cache is EMPTY — every deputy will score AUSENTE. "
            "Build it first with --ingest-cache.")
    deputies = [d for d in iter_deputies(pages=pages, itens=itens, pause=pause) if d["camara_id"]]
    total = len(deputies)
    log(f"  {total} deputies · {workers} workers")
    _prewarm_tse_lists(sorted({d["uf"] for d in deputies if d["uf"]}),
                       sc.DEFAULT_ELECTION["tse_cargo"], log)

    results = {"house": "camara", "scored": 0, "failed": 0, "errors": []}
    rlock = threading.Lock()

    def work(_idx: int, dep: dict[str, Any]) -> None:
        if telemetry:
            telemetry.job_enter()
        t0 = time.monotonic()
        try:
            _retry_on_deadlock(lambda: sc.score_camara_candidate(
                camara_id=dep["camara_id"], tse_uf=dep["uf"],
                database_url=database_url, pause=pause, init=False,
            ))
            dt = time.monotonic() - t0
            with rlock:
                results["scored"] += 1
                n = results["scored"] + results["failed"]
                log(f"  ✓ [{n}/{total}] {dep['name']} ({dep['party']}-{dep['uf']}) {dt:.1f}s")
        except Exception as exc:
            with rlock:
                results["failed"] += 1
                n = results["scored"] + results["failed"]
                results["errors"].append({"camara_id": dep["camara_id"], "name": dep["name"], "error": str(exc)})
                log(f"  ✗ [{n}/{total}] {dep['name']} ({dep['party']}-{dep['uf']}): {exc}")
        finally:
            if telemetry:
                telemetry.job_exit()

    _run_pool(deputies, work, workers)
    return results


def scan_senators(
    *, workers: int = 5, database_url: str | None = None, telemetry: Telemetry | None = None,
    log: Callable[[str], None] = print,
) -> dict[str, Any]:
    """Score every sitting senator concurrently. Builds the Senado roll-call package ONCE
    (sequentially), then scores each senator from that cache (`build_package=False`)."""
    conn = db.init_db(database_url)
    try:
        log("  Building Senado package once for the seeded laws...")
        senado.build_senado_package(conn, log=lambda m: log(f"  {m}"))
    finally:
        conn.close()

    senators = senado.list_current_senators()
    total = len(senators)
    log(f"  {total} senators · {workers} workers")
    results = {"house": "senado", "scored": 0, "failed": 0, "errors": []}
    rlock = threading.Lock()

    def work(_idx: int, s: dict[str, Any]) -> None:
        if telemetry:
            telemetry.job_enter()
        t0 = time.monotonic()
        try:
            _retry_on_deadlock(lambda: senado.score_senator(
                senado_id=s["senado_id"], name=s["name"], party=s["party"], uf=s["uf"],
                database_url=database_url, build_package=False, init=False,
            ))
            dt = time.monotonic() - t0
            with rlock:
                results["scored"] += 1
                n = results["scored"] + results["failed"]
                log(f"  ✓ [{n}/{total}] {s['name']} ({s['party']}-{s['uf']}) {dt:.1f}s")
        except Exception as exc:
            with rlock:
                results["failed"] += 1
                n = results["scored"] + results["failed"]
                results["errors"].append({"senado_id": s["senado_id"], "name": s["name"], "error": str(exc)})
                log(f"  ✗ [{n}/{total}] {s['name']}: {exc}")
        finally:
            if telemetry:
                telemetry.job_exit()

    _run_pool(senators, work, workers)
    return results


def run(args: argparse.Namespace) -> int:
    log = lambda m: print(m, flush=True)

    # Create schema + seed reference data ONCE, before any worker runs (workers use init=False).
    db.init_db(args.db).close()

    if args.ingest_cache:
        log("Building Câmara vote cache (ingest.ingest_all)...")
        conn = db.init_db(args.db)
        try:
            ingest.ingest_all(conn, pause=args.pause, log=log)
        finally:
            conn.close()

    telemetry = Telemetry(args.telemetry_log, log)
    sc.REQUEST_HOOK = telemetry.on_request
    log(f"Telemetry → {args.telemetry_log} (every request; 429/5xx warn inline)")

    reports = []
    try:
        if not args.no_deputies:
            log(f"== Deputies: {args.pages or 'all'} page(s) × {args.itens or 'whole'} per page ==")
            reports.append(scan_deputies(
                pages=args.pages, itens=args.itens, workers=args.workers, pause=args.pause,
                database_url=args.db, telemetry=telemetry, log=log,
            ))
        if args.senators:
            log("== Senators (full roster) ==")
            reports.append(scan_senators(
                workers=args.workers, database_url=args.db, telemetry=telemetry, log=log,
            ))
    finally:
        sc.REQUEST_HOOK = None
        telemetry.close()

    log("\n== Summary ==")
    for r in reports:
        log(f"  {r['house']}: {r['scored']} scored, {r['failed']} failed")
        for e in r["errors"]:
            log(f"     - {e['name']}: {e['error']}")
    s = telemetry.summary()
    log(f"  HTTP: {s['requests']} requests in {s['elapsed_s']}s = {s['req_per_s']} req/s · "
        f"429s: {s['http_429']} · errors: {s['errors']}")
    log(f"  by status: {s['by_status']}")
    log(f"  by host:   {s['by_host']}")
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--db", default=db.DATABASE_URL, help="Database URL; defaults to DATABASE_URL")
    p.add_argument("--pages", type=int, default=1,
                   help="Câmara roster pages to scan (default 1). Use 0 for ALL pages.")
    p.add_argument("--itens", type=int, default=None,
                   help="Deputies per page. Default = a WHOLE page (Câmara returns all ≈512 in page 1).")
    p.add_argument("--workers", type=int, default=5,
                   help="Concurrent scoring workers (default 5). Raise to go faster; lower if you see 429s.")
    p.add_argument("--pause", type=float, default=0.35, help="Seconds between API calls inside one scoring run")
    p.add_argument("--telemetry-log", default="/tmp/scan_telemetry.jsonl",
                   help="JSONL request log (one line per HTTP attempt) for learning the rate limits")
    p.add_argument("--no-deputies", action="store_true", help="Skip the deputy scan")
    p.add_argument("--senators", action="store_true", help="Also scan all senators")
    p.add_argument("--ingest-cache", action="store_true",
                   help="Build the Câmara vote cache first (heavy). Off by default — the scan assumes laws are downloaded.")
    return p


if __name__ == "__main__":
    a = parser().parse_args()
    if a.pages == 0:
        a.pages = None  # all pages
    sys.exit(run(a))
