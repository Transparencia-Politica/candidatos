#!/usr/bin/env python3
"""Tiny local server for the Candidato scorecard POC.
It does NOT contain any candidate data. It only:
  - serves index.html
  - proxies GET requests to the Camara / TSE open APIs (to add headers & avoid CORS)
All real data is fetched live by the browser when the page loads.
"""
import http.server, urllib.request, urllib.parse, json, os, time, threading

ALLOWED = ("dadosabertos.camara.leg.br", "divulgacandcontas.tse.jus.br")
CACHE = {}
HERE = os.path.dirname(os.path.abspath(__file__))
# Global cap on simultaneous upstream calls — bounds total load on the APIs no matter
# how many browser tabs/searches run at once (this is what prevents the throttling).
SEM = threading.Semaphore(4)

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
        if p.path in ("/", "/index.html", "/discover.html"):
            fname = "index.html" if p.path in ("/", "/index.html") else "discover.html"
            fpath = os.path.join(HERE, fname)
            if os.path.isfile(fpath):
                with open(fpath, "rb") as f:
                    return self._send(200, f.read(), "text/html; charset=utf-8")
        if p.path == "/proxy":
            url = urllib.parse.parse_qs(p.query).get("url", [""])[0]
            host = (urllib.parse.urlparse(url).hostname or "")
            if not any(host == a or host.endswith("." + a) for a in ALLOWED):
                return self._send(400, json.dumps({"error": "host not allowed", "host": host}))
            if url in CACHE:
                return self._send(200, CACHE[url])
            # retry with backoff to ride out API throttling/SSL hiccups
            last = None
            for attempt in range(5):
                try:
                    req = urllib.request.Request(url, headers={
                        "Accept": "application/json",
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36",
                        "Referer": "https://divulgacandcontas.tse.jus.br/",
                    })
                    with SEM:  # bound concurrent upstream calls
                        data = urllib.request.urlopen(req, timeout=45).read()
                    CACHE[url] = data
                    return self._send(200, data)
                except urllib.error.HTTPError as e:
                    last = e
                    if e.code == 429:  # throttled — honor Retry-After
                        wait = min(int(e.headers.get("Retry-After", "5") or 5), 30)
                        time.sleep(wait)
                    else:
                        time.sleep(0.6 * (attempt + 1))
                except Exception as e:
                    last = e
                    time.sleep(0.6 * (attempt + 1))
            return self._send(502, json.dumps({"error": str(last), "url": url}))
        return self._send(404, json.dumps({"error": "not found"}))

    def log_message(self, *a):  # quiet
        pass

if __name__ == "__main__":
    PORT = 8765
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H)
    print(f"Candidato scorecard server on http://127.0.0.1:{PORT}")
    srv.serve_forever()
