#!/usr/bin/env python3
"""Tiny local server for the Candidato scorecard POC.

It serves the static frontend and exposes DB-backed JSON APIs. The live Câmara/TSE
fetching happens in score_candidate.py so the browser reads stored scorecards.
"""
import http.server, urllib.request, urllib.parse, json, os

try:
    import db
    import score_candidate
    import senado
except ModuleNotFoundError:
    from app import db
    from app import score_candidate
    from app import senado

ALLOWED = ("dadosabertos.camara.leg.br", "divulgacandcontas.tse.jus.br")
CACHE = {}
HERE = os.path.dirname(os.path.abspath(__file__))
# Shared frontend assets (theme.css, scorecard.js) live at the repo root and are
# served at /shared/* — the source of truth that docs/shared/ is copied from.
SHARED_DIR = os.path.join(os.path.dirname(HERE), "shared")
SHARED_TYPES = {".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8"}
db.init_db().close()


def with_db(callback):
    conn = db.connect()
    try:
        return callback(conn)
    finally:
        conn.close()


def parse_json_body(handler):
    length = int(handler.headers.get("Content-Length", "0") or 0)
    if length <= 0:
        return {}
    raw = handler.rfile.read(length).decode("utf-8")
    return json.loads(raw or "{}")

class H(http.server.BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        b = body if isinstance(body, (bytes, bytearray)) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        try: self.wfile.write(b)
        except BrokenPipeError: pass

    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if p.path in ("/", "/index.html"):
            with open(os.path.join(HERE, "index.html"), "rb") as f:
                return self._send(200, f.read(), "text/html; charset=utf-8")
        if p.path.startswith("/shared/"):
            name = os.path.basename(p.path)  # strip any path-traversal segments
            ext = os.path.splitext(name)[1]
            if ext not in SHARED_TYPES:
                return self._send(404, json.dumps({"error": "not found"}))
            try:
                with open(os.path.join(SHARED_DIR, name), "rb") as f:
                    return self._send(200, f.read(), SHARED_TYPES[ext])
            except FileNotFoundError:
                return self._send(404, json.dumps({"error": "not found"}))
        if p.path == "/api/candidates/search":
            query = urllib.parse.parse_qs(p.query)
            name = (query.get("q", [""])[0] or "").strip()
            if len(name) < 2:
                return self._send(400, json.dumps({"error": "query must have at least 2 characters"}))
            try:
                candidates = score_candidate.search_deputies(name)
                return self._send(200, json.dumps({"candidates": candidates}, ensure_ascii=False))
            except Exception as e:
                return self._send(502, json.dumps({"error": str(e)}, ensure_ascii=False))
        if p.path == "/api/topics":
            payload = with_db(lambda conn: {"topics": db.list_topics(conn)})
            return self._send(200, json.dumps(payload, ensure_ascii=False))
        if p.path == "/api/politics":
            payload = with_db(lambda conn: {"politics": db.list_politics(conn)})
            return self._send(200, json.dumps(payload, ensure_ascii=False))
        if p.path == "/api/scorecards":
            query = urllib.parse.parse_qs(p.query)
            camara_id = query.get("camara_id", [None])[0]
            payload = with_db(lambda conn: db.get_scorecards(conn, int(camara_id) if camara_id else None))
            return self._send(200, json.dumps(payload, ensure_ascii=False))
        if p.path.startswith("/api/scorecards/"):
            try:
                camara_id = int(p.path.rsplit("/", 1)[-1])
            except ValueError:
                return self._send(400, json.dumps({"error": "invalid camara_id"}))
            payload = with_db(lambda conn: db.get_scorecards(conn, camara_id))
            return self._send(200, json.dumps(payload, ensure_ascii=False))
        if p.path == "/api/senators/scorecard":
            # The Senado fallback for the unified search. `senado_id` reads an already-scored
            # senator from MySQL (no re-score); `name` resolves a current senator and scores them
            # from senado roll-calls. See research/14-senado-vote-crossing.md.
            query = urllib.parse.parse_qs(p.query)
            senado_id = query.get("senado_id", [None])[0]
            if senado_id:
                payload = with_db(lambda conn: db.get_scorecards(conn, senado_id=int(senado_id)))
                if not payload["scorecards"]:
                    return self._send(404, json.dumps({"error": "senator not scored yet"}))
                payload["source"] = "cache"
                return self._send(200, json.dumps(payload, ensure_ascii=False))
            name = (query.get("name", [""])[0] or "").strip()
            if len(name) < 2:
                return self._send(400, json.dumps({"error": "name must have at least 2 characters"}))
            try:
                sen = senado.resolve_senator(name)
                senado.score_senator(senado_id=sen["senado_id"], name=sen["name"],
                                     party=sen["party"], uf=sen["uf"], database_url=db.DATABASE_URL)
                payload = with_db(lambda conn: db.get_scorecards(conn, senado_id=sen["senado_id"]))
                payload["source"] = "calculated"
                return self._send(200, json.dumps(payload, ensure_ascii=False))
            except Exception as e:
                return self._send(502, json.dumps({"error": str(e)}, ensure_ascii=False))
        if p.path == "/proxy":
            url = urllib.parse.parse_qs(p.query).get("url", [""])[0]
            host = (urllib.parse.urlparse(url).hostname or "")
            if not any(host == a or host.endswith("." + a) for a in ALLOWED):
                return self._send(400, json.dumps({"error": "host not allowed", "host": host}))
            if url in CACHE:
                return self._send(200, CACHE[url])
            try:
                req = urllib.request.Request(url, headers={
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36",
                    "Referer": "https://divulgacandcontas.tse.jus.br/",
                })
                data = urllib.request.urlopen(req, timeout=45).read()
                CACHE[url] = data
                return self._send(200, data)
            except Exception as e:
                return self._send(502, json.dumps({"error": str(e), "url": url}))
        return self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        p = urllib.parse.urlparse(self.path)
        if p.path != "/api/scorecards":
            return self._send(404, json.dumps({"error": "not found"}))
        try:
            body = parse_json_body(self)
            camara_id = int(body.get("camara_id") or 0)
            if not camara_id:
                return self._send(400, json.dumps({"error": "camara_id is required"}))
            refresh = bool(body.get("refresh"))
            if not refresh:
                existing = with_db(lambda conn: db.get_scorecards(conn, camara_id))
                if existing["scorecards"]:
                    existing["source"] = "cache"
                    return self._send(200, json.dumps(existing, ensure_ascii=False))
            score_candidate.score_camara_candidate(
                camara_id=camara_id,
                tse_year=int(body.get("tse_year") or score_candidate.DEFAULT_ELECTION["tse_year"]),
                tse_uf=body.get("tse_uf"),
                tse_election_id=body.get("tse_election_id") or score_candidate.DEFAULT_ELECTION["tse_election_id"],
                tse_cargo=int(body.get("tse_cargo") or score_candidate.DEFAULT_ELECTION["tse_cargo"]),
                tse_sq=body.get("tse_sq"),
                database_url=db.DATABASE_URL,
            )
            payload = with_db(lambda conn: db.get_scorecards(conn, camara_id))
            payload["source"] = "calculated"
            return self._send(200, json.dumps(payload, ensure_ascii=False))
        except Exception as e:
            return self._send(502, json.dumps({"error": str(e)}, ensure_ascii=False))

    def log_message(self, *a):  # quiet
        pass

if __name__ == "__main__":
    HOST = os.environ.get("CANDIDATO_HOST", "127.0.0.1")
    PORT = int(os.environ.get("CANDIDATO_PORT", "8765"))
    srv = http.server.ThreadingHTTPServer((HOST, PORT), H)
    print(f"Candidato scorecard server on http://{HOST}:{PORT}")
    srv.serve_forever()
