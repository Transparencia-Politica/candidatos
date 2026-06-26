#!/usr/bin/env python3
"""Tiny local server for the Candidato scorecard POC.

It serves the static frontend and exposes DB-backed JSON APIs. The live Câmara/TSE
fetching happens in score_candidate.py so the browser reads stored scorecards.
"""
import http.server, urllib.request, urllib.parse, json, os

try:
    import db
except ModuleNotFoundError:
    from app import db

ALLOWED = ("dadosabertos.camara.leg.br", "divulgacandcontas.tse.jus.br")
CACHE = {}
HERE = os.path.dirname(os.path.abspath(__file__))
db.init_db().close()


def with_db(callback):
    conn = db.connect()
    try:
        return callback(conn)
    finally:
        conn.close()

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

    def log_message(self, *a):  # quiet
        pass

if __name__ == "__main__":
    HOST = os.environ.get("CANDIDATO_HOST", "127.0.0.1")
    PORT = int(os.environ.get("CANDIDATO_PORT", "8765"))
    srv = http.server.ThreadingHTTPServer((HOST, PORT), H)
    print(f"Candidato scorecard server on http://{HOST}:{PORT}")
    srv.serve_forever()
