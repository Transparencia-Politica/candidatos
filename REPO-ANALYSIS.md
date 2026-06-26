# MCP Repo Analysis — Full Technical Reports

Two "Brazil MCP" GitHub repos (linked below) were cloned locally and analyzed in depth. They
are **not bundled** in this repository — clone them from the URLs below to inspect the source;
file paths like `src/main.py` are relative to each cloned repo.
**Neither exposes any electoral, voting, attendance, or candidate data** — both are
Brazilian *utility-data* servers (CEP / CNPJ / PIX / etc.). Their value to this project
is purely as **architectural references** for building a future `dados-eleitorais` MCP
server on top of the Câmara / Senado / TSE APIs (see `DATA-SOURCES.md`).

- Repo 1: https://github.com/impulsoxai/brazil-mcp-server — production, Python
- Repo 2: https://github.com/josenelsoncultri/josenelsoncultri-brazilinfo-mcp — prototype, TypeScript

---

# Repo 1 — `impulsoxai/brazil-mcp-server` (Python, production)

Hosted endpoint: `https://mcp.impulsoxai.com.br/mcp`

## 1. Tech Stack & Dependencies

**Language & Core Framework:**
- Python 3.11+ (strongly typed with Pydantic)
- MCP SDK: `mcp>=1.0.0` (Model Context Protocol — Anthropic standard)
- HTTP Server: `uvicorn>=0.30.0` (ASGI, production-ready)
- Web Framework: Starlette (implicit via FastMCP)

**Key Dependencies:**
- **HTTP Client:** `httpx>=0.27.0` (async-native, with built-in retry logic)
- **Validation:** `pydantic>=2.0.0` (strict type validation, JSON schema generation)
- **Database:** `sqlalchemy[asyncio]>=2.0.0`, `asyncpg>=0.30.0` (PostgreSQL with native async)
- **Migrations:** `alembic>=1.14.0` (schema versioning)
- **Browser Automation:** `playwright>=1.40.0` (for data scraping if needed)
- **Utilities:** `unidecode>=1.3.0`, `python-dotenv>=1.0.0`, `num2words>=0.5.0`

**Dev Dependencies:**
- pytest, pytest-asyncio, pytest-cov (solid async test support)
- Python version requirement enforced in pyproject.toml

**Deployment:**
- Railway (automated CI/CD via railway.json)
- Docker / Nixpacks build system

See: `pyproject.toml` (in the cloned `brazil-mcp-server` repo)

## 2. Directory & Module Structure

```
src/
├── main.py                    # Entry point: FastMCP server + middleware wiring
├── config.py                  # Env vars, API endpoints, secrets
├── scope.py                   # Request-scoped access control + tier hierarchy
│
├── tools/                     # 6 modules, 22 tools total (public tier)
│   ├── identidade.py          # CNPJ/CPF validation & lookup (5 tools)
│   ├── endereco.py            # CEP/address lookup (3 tools)
│   ├── pagamentos.py          # PIX generation, interest calculations (5 tools)
│   ├── calendario.py          # Holidays, business days (4 tools)
│   ├── utilidades.py          # Currency, phone, bank lookup (5 tools)
│   ├── agrinho.py             # Agricultural commodities & weather (3 tools, premium_t2)
│   ├── onda1/                 # 12 pure-logic tools (public tier)
│   │   ├── mensagem.py        # WhatsApp formatting
│   │   ├── calculos.py        # Discount, commission, BMI, inflation
│   │   ├── datas.py           # Age calculation, date formatting
│   │   └── validacao.py       # Email validation, secure password generation
│   └── registry.py            # Tool registration utilities
│
├── middleware/
│   ├── auth.py                # API key validation (master key bypass)
│   ├── rate_limit.py          # In-memory per-minute rate limiting
│   └── logging.py             # Structured logging
│
├── services/
│   ├── database.py            # PostgreSQL async operations (API keys, usage, commodity cache)
│   ├── usage.py               # Usage tracking + monthly reset logic
│   └── plans.py               # Plan tiers (free, premium_t1, premium_t2, master)
│
├── models/                    # SQLAlchemy ORM
│   ├── base.py                # Engine, session factory, Base class
│   ├── api_key.py             # API key model + Stripe fields
│   ├── ip_fingerprint.py      # Track IP-based key creation limits
│   ├── usage_log.py           # Usage audit log
│   └── commodity_cache.py     # Commodity prices (cached from CEPEA scraper)
│
├── utils/
│   ├── validators.py          # Math validation: CPF, CNPJ (no API calls)
│   ├── formatters.py          # Format CPF, CNPJ, CEP, phone, currency
│   ├── http_client.py         # Shared async HTTP with retry + backoff
│   ├── cache.py               # In-memory TTL cache (used by tools)
│   └── ibge.py                # IBGE code resolver for weather queries
│
├── scrapers/
│   └── commodity_scraper.py   # Daily CEPEA commodity price fetch
│
└── monitoring/
    └── alertas.py             # Telegram alert dispatcher

tests/ (8,753 lines total)
├── tools/                     # Unit tests per tool module
├── integration/               # End-to-end server tests
├── middleware/                # Auth + rate limit tests
├── utils/                     # Validator + formatter tests
└── conftest.py                # Shared pytest fixtures
```

Key files:
- `src/main.py` — Server entry point
- `src/config.py` — Configuration management
- `src/scope.py` — Access control + tier system
- `pyproject.toml` — Dependencies and build config

## 3. Complete MCP Tools List (25 total)

### Module 1: Identidade (5 tools, public)
1. `consultar_cnpj(cnpj)` — Query BrasilAPI for full company data (legal name, status, address, partners, CNAE, founding date)
2. `validar_cnpj_tool(cnpj)` — Math-only validation (no API call)
3. `validar_cpf_tool(cpf)` — Math-only validation (no API call)
4. `formatar_cpf_tool(cpf)` — Format with mask (XXX.XXX.XXX-XX)
5. `formatar_cnpj_tool(cnpj)` — Format with mask (XX.XXX.XXX/XXXX-XX)

**API Source:** BrasilAPI (`brasilapi.com.br/api/cnpj/v1/{cnpj}`)

### Module 2: Endereco (3 tools, public)
1. `buscar_endereco_por_cep(cep)` — Full address from ZIP code (BrasilAPI)
2. `buscar_ceps_por_logradouro(logradouro, cidade, uf)` — Find CEPs by street name (ViaCEP)
3. `formatar_endereco_completo(logradouro, cidade, uf, numero?, complemento?, bairro?, cep?)` — Format readable address (local)

**API Sources:** BrasilAPI (cep endpoint), ViaCEP (ws endpoint)

### Module 3: Pagamentos (5 tools, public)
1. `gerar_pix_copia_cola(chave, valor, nome, cidade, descricao?)` — Generate EMV standard PIX payload (local CRC16-CCITT)
2. `validar_chave_pix(chave)` — Validate PIX key type: CPF, CNPJ, email, phone, or UUID (local)
3. `calcular_juros_simples(principal, taxa_mensal, meses)` — Simple interest J = P × i × t (local)
4. `calcular_juros_compostos(principal, taxa_mensal, meses)` — Compound interest M = P × (1+i)^t (local)
5. `calcular_multa_atraso(valor, dias_atraso)` — Late payment penalty: 2% fine + 1%/month pro rata (local)

**API Sources:** None (all pure calculations + EMV standard generation)

### Module 4: Calendario (4 tools, public)
1. `listar_feriados_nacionais(ano)` — National Brazilian holidays (BrasilAPI with 24h cache)
2. `verificar_dia_util(data)` — Check if date is business day (excludes weekends + holidays)
3. `calcular_prazo_util(data_inicio, dias_uteis)` — Add N business days to date (local with cached holidays)
4. `proximo_dia_util(data)` — Next business day from given date (local with cached holidays)

**API Sources:** BrasilAPI (feriados endpoint) — cached for 24h

### Module 5: Utilidades (5 tools, public)
1. `converter_moeda(valor, de, para)` — Currency conversion with real-time rates (ExchangeRate-API, 5min cache)
2. `validar_telefone_br(telefone)` — Validate Brazilian phone: DDD (11-99), length, mobile digit check (local)
3. `formatar_telefone_br_tool(telefone)` — Format phone (XX) XXXXX-XXXX or (XX) XXXX-XXXX (local)
4. `buscar_banco_por_codigo(codigo)` — Look up bank by COMPE code (BrasilAPI, 1h cache)
5. `listar_ddd_estados()` — Map 67 DDDs to Brazilian states/regions (local hardcoded mapping)

**API Sources:** ExchangeRate-API (`open.er-api.com/v6/latest/{currency}`), BrasilAPI (banks endpoint)

### Module 6: Agrinho (3 tools, premium_t2 scope)
1. `get_commodity_price(commodity, estado?)` — Agricultural commodity prices: soja, milho, boi_gordo, cafe_arabica, arroz, feijao, trigo (PostgreSQL cache from CEPEA scraper, daily at 18:30)
2. `get_weather_forecast(municipio)` — 3-day forecast by municipality (INMET API, 3h cache)
3. `get_weather_alert(municipio)` — Active weather alerts (geada, seca, chuva forte, granizo) via point-in-polygon detection (INMET API, 30min cache)

**API Sources:** PostgreSQL commodity_cache (CEPEA scraper), INMET (`apiprevmet3.inmet.gov.br`)

### Module 7: Onda 1 (12 tools, public) — Pure Logic
1. `formatar_mensagem_whatsapp_tool(texto, negrito?, italico?, itens?)` — Format WhatsApp markdown
2. `gerar_link_whatsapp(telefone, mensagem?)` — Generate wa.me/ link
3. `calcular_desconto_tool(valor, desconto_percentual)` — Discount calculator
4. `calcular_comissao_tool(valor, percentual)` — Commission calculator
5. `calcular_idade(data_nascimento)` — Calculate age in years/months/days + next birthday
6. `formatar_data_br(data)` — Convert any date format to DD/MM/YYYY + weekday + spelled-out
7. `calcular_diferenca_datas(data1, data2)` — Calculate days between dates
8. `validar_email_br_tool(email)` — Email format validation + typo detection (gmail.com, hotmail.com)
9. `calcular_imc(peso_kg, altura_m)` — BMI calculator with WHO classifications
10. `calcular_reajuste_inflacao(valor, percentual_reajuste)` — Apply inflation adjustment
11. `gerar_senha_segura(tamanho?, incluir_simbolos?, incluir_numeros?, incluir_maiusculas?)` — Generate secure password with entropy calculation
12. `converter_numero_extenso(numero)` — Convert numbers to words (Portuguese)

**API Sources:** None (all pure computation)

## 4. MCP Server Wiring & Tooling

**Entry Point:** `src/main.py` (216 lines)

**Architecture:**
```
FastMCP (Anthropic SDK)
  └─ ScopedFastMCP (custom subclass)
      ├── list_tools() — filters by request scope
      └── call_tool(name, arguments) — checks access tier
          └── Middleware: AuthRateLimitMiddleware
              ├── 1. Verify x-api-key header
              ├── 2. Resolve scope (master/premium_t2/premium_t1/public)
              ├── 3. Check monthly limit
              ├── 4. Check per-minute rate limit
              ├── 5. Increment usage counter
              └── Route to ScopedFastMCP.call_tool()
```

**Tool Registration Pattern:** Each module exports a `register_tools(mcp: FastMCP)` function using decorators:
```python
@mcp.tool()
async def example_tool(param: Annotated[type, Field(description="...")]) -> str:
    """Detailed docstring for AI agent."""
    # implementation
```

Tools are registered in `main.py` (lines 52-58):
```python
identidade.register_tools(mcp)
endereco.register_tools(mcp)
pagamentos.register_tools(mcp)
calendario.register_tools(mcp)
utilidades.register_tools(mcp)
agrinho.register_tools(mcp)
register_onda1(mcp)
```

**Scope System** (`src/scope.py`):
- Uses Python `contextvars.ContextVar` for request-scoped access control
- 4-tier hierarchy: public (0) → premium_t1 (1) → premium_t2 (2) → master (3)
- Tools can be marked as premium via `register_tool_scope(name, scope)`
- `list_tools()` filters based on `request_scope.get()`
- `call_tool()` raises ToolError if scope is insufficient

**Authentication** (`src/middleware/auth.py`):
- Validates x-api-key header against PostgreSQL (or master key via env var)
- Master key (`IMPULSOX_MASTER_KEY` env var) bypasses all rate limiting
- Resolves plan tier → scope

**Rate Limiting** (`src/middleware/rate_limit.py`):
- In-memory deque-based per-minute windows
- Skipped for master key
- Checked via `verificar_rate_limit(api_key)` before tool execution
- Monthly limit checked via `verificar_limite_mensal(api_key)` against PostgreSQL

**Custom Routes** (lines 114-183):
- `/health` (GET) — health check for Railway
- `/usage` (GET) — returns usage stats for API key
- `/keys/create` (POST) — public endpoint to generate free API key
- `/` (GET) — serves landing page (HTML)

## 5. How It Runs (Local + Hosted)

**Local Development:**
```bash
cp .env.example .env
pip install -e .
python -m src.main
# Server on http://localhost:8000/mcp
```

Environment variables (`src/config.py`):
- `MCP_ENV`: "development" or "production"
- `MCP_PORT`: port (default 8000, Railway overrides with PORT env var)
- `DATABASE_URL`: PostgreSQL connection string
- `BRASIL_API_BASE`: "https://brasilapi.com.br/api" (default)
- `EXCHANGE_RATE_API_BASE`: "https://open.er-api.com/v6" (default)
- `IMPULSOX_MASTER_KEY`: secret master key (optional)
- `SENTRY_DSN`: error tracking (optional)
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`: alerts (optional)

**Production (Railway):**
1. Build: `railway.json` specifies Nixpacks builder
2. Start Command: `python -m src.main` (in Procfile)
3. Health Check: `/health` endpoint with 30s timeout
4. Restart Policy: ON_FAILURE with 3 retries
5. Database: PostgreSQL (created via Alembic migrations on startup)
6. Monitoring: Telegram alerts via `src/monitoring/alertas.py`

**Database Setup:**
- SQLAlchemy async ORM + asyncpg
- Alembic migrations in `alembic/versions/`
- Tables created on first run via `await usage.init_db()` in main
- Models: ApiKey, IpFingerprint, UsageLog, CommodityCache

## 6. Test Setup & Coverage

- **Framework:** pytest + pytest-asyncio (auto mode)
- **Test Count:** ~22 test files, 8,753 total LOC
- **Categories:** unit tests per tool module (`tests/tools/`), middleware tests (auth), integration (`tests/integration/`: server, edge cases, robustez, avancado, final, profundidade, cobertura, agrinho, seguranca_cultural, producao), auth & scope tests, utils tests (`test_ibge.py`)
- **Fixtures** (`conftest.py`): `cpf_valido`="52998224725", `cpf_invalido`="11111111111", `cnpj_valido`="11222333000181", `cnpj_invalido`="11111111000111"
- **Config:** `asyncio_mode = "auto"`, `testpaths = ["tests"]`

## 7. Electoral/Political/Government Data
**Result: NONE FOUND.** Grep for `eleitor`, `voto`, `governo`, `legislativo`, `deputado`,
`senador` → no matches. Purely a business/logistics/agriculture utilities server.

## 8. Code Quality

**Strengths:** clean architecture (tools → services → models → middleware), strong error
handling (Portuguese messages with "Dica:" hints, cached fallbacks), async-first
(contextvars, httpx, SQLAlchemy async), security (API key + rate limiting + IP-based
creation limits), good docs (CLAUDE.md 11KB, per-tool docstrings), comprehensive tests,
IaC deployment.

**Weaknesses:** retry logic could be a decorator; commodity scraper depends on external
CEPEA script not in repo; no OpenAPI (MCP native schema); stderr logging by design;
hardcoded cache TTLs.

**Score: 8.5/10 — production-ready, exemplary MCP reference.**

Key reusable pattern:
```python
class ScopedFastMCP(FastMCP):
    async def list_tools(self):
        tools = await super().list_tools()
        scope = request_scope.get()
        return [t for t in tools if is_tool_allowed(t.name, scope)]

    async def call_tool(self, name, arguments):
        scope = request_scope.get()
        if not is_tool_allowed(name, scope):
            raise ToolError(f"Premium tool '{name}'...")
        return await super().call_tool(name, arguments)
```

**Summary table:**

| Aspect | Finding |
|---|---|
| Language | Python 3.11+ (async-first) |
| Framework | FastMCP (Anthropic MCP SDK) |
| HTTP | Uvicorn + Starlette |
| Database | PostgreSQL + SQLAlchemy async |
| Tools | 25 total (22 public, 3 premium) across 6 modules |
| APIs | BrasilAPI, ViaCEP, ExchangeRate-API, INMET, CEPEA |
| Auth | API key + master key + tier-based scope |
| Rate Limit | Per-minute (in-memory) + monthly (PostgreSQL) |
| Deployment | Railway (automated, health checks) |
| Tests | 22 files, ~8,753 LOC |
| Electoral Data | None (confirmed) |
| Code Quality | 8.5/10 |

---

# Repo 2 — `josenelsoncultri/josenelsoncultri-brazilinfo-mcp` (TypeScript, prototype)

## 1. Tech Stack & Dependencies

**Language & Runtime:** TypeScript (strict mode), Node.js v24+ with ES2022 target

**Core Dependencies:**
- `@modelcontextprotocol/sdk@^1.29.0` — MCP Server framework (only core dependency)
- `zod@^4.4.3` — Runtime schema validation with TypeScript inference
- `tsx@^4.22.3` — TypeScript executor (direct TS execution without build step)
- `@types/node@^25.9.1` — Node.js type definitions

**Config:**
- `tsconfig.json` — strict TypeScript (strict mode, noEmit, isolatedModules)
- `"type": "module"` — ESM
- No external data/weather/polling APIs beyond ViaCEP

## 2. Directory & Module Structure

```
/src
├── index.ts                          # Entry point - stdio transport setup (14 lines)
├── domain/
│   ├── base.ts                       # Base response schema (6 lines)
│   └── zip_code.ts                   # ZipCodeQuery/ZipCodeInfo/ZipCodeResponse schemas (26 lines)
├── infrastructure/
│   ├── service.ts                    # ServiceCollection dependency container (14 lines)
│   └── clients/
│       └── viacep_client.ts          # ViaCEP API client (11 lines)
└── mcp/
    ├── server.ts                     # MCP server instantiation & tool registration (13 lines)
    └── tools/
        └── search_zip_code.ts        # Tool definition & handler (40 lines)

/tests
├── helpers.ts                        # Test client factory (22 lines)
└── tools/
    └── viacep.test.ts                # Integration tests (45 lines)

Total: 120 LOC (src) + 67 LOC (tests)
```

Layers: **Domain** (Zod schemas) / **Infrastructure** (API clients, DI) / **MCP** (tool
registration + handlers). Clear separation, no circular dependencies.

## 3. MCP Tools Exposed

**LIVE (1 tool):**
- **`search_zip_code`** — Queries Brazilian postal code (CEP) info.
  - Input: `ZipCodeQuerySchema` — `zip_code: string` (optional)
  - Output: `cep`, `logradouro`, `complemento`, `bairro`, `localidade`, `uf`, `estado`, `regiao`, `ibge`
  - External API: ViaCEP (`https://viacep.com.br/ws/{zipcode}/json`)
  - Registered: `src/mcp/server.ts` lines 9-15; handler: `src/mcp/tools/search_zip_code.ts` lines 16-39

**PLANNED (not implemented):**
- Company Registration Search — README marks it "🔄 Em desenvolvimento" but there is
  **zero implementation** (no source, schemas, or placeholder code).

## 4. Server Wiring & Entry Point

```
src/index.ts (executable via #! tsx shebang)
  → new StdioServerTransport()
  → src/mcp/server.ts: new McpServer({ name, version: "1.0.0" })
  → registerSearchZipCodeTool(server, serviceCollection)
  → ServiceCollection → ViaCepClient → fetch(https://viacep.com.br)
```

- Each tool is a `registerXTool(server, services)` function calling `server.registerTool()`
- Handler is async, returns content array + structuredContent; errors wrapped with `isError: true`
- Single `ServiceCollection` instance instantiates clients on-demand (DI)

## 5. How To Run / Config / Env

- Install: `npm install`
- Production: `npm start` → `node src/index.ts`
- Dev: `npm run dev` → `node --watch --inspect src/index.ts`
- Test: `npm test` → `node --test tests/**/*.test.ts`
- MCP inspect: `npm run mcp:inspect`
- Build: `npm run build` → chmod 755 on `src/index.ts`
- VSCode: `.vscode/mcp.json` → `node --experimental-strip-types ./src/index.ts`

**Environment variables: NONE.** No `process.env` calls. ViaCEP endpoint hardcoded.
All config is compile-time via tsconfig.

## 6. Tests

- Framework: Node native test runner (`node:test`), no external library
- File: `tests/tools/viacep.test.ts` — 2 integration cases
  1. Valid zip `14405-000` → validates `logradouro`, `localidade`
  2. Single-zip city `37993000` → tests empty neighborhood/street
- Client factory (`tests/helpers.ts`) spawns server as subprocess via `StdioClientTransport`, `--experimental-strip-types`
- Happy path only; no invalid input / network failure / malformed response tests
- ~56% test-to-source ratio by LOC

## 7. Electoral / Political / Legislative Data
**Verdict: NONE.** Searches for electoral/political/legislative/government/representative/
parliament/senator/deputy/congress (and PT equivalents) returned zero across source.
Purely postal/geographic (zip codes + planned company registration).

## 8. Code Quality

**Strengths:** excellent layer separation (domain/infrastructure/mcp); strict TypeScript +
Zod runtime validation; clean, minimal, single-responsibility; modern tooling (ESM, node
test runner, tsx); great MCP-structure template.

**Weaknesses:**
- Minimal client error handling (`viacep_client.ts` has no try-catch, no HTTP status check, no JSON validation → unhandled exceptions on network errors/404/500/malformed)
- Happy-path-only tests
- No logging/observability
- Response typed as `response.json() as unknown as ZipCodeInfo` — not schema-validated (could silently accept invalid data)
- Only 1 of 2 advertised features exists

**Maturity:** EARLY PROTOTYPE / reference implementation. Single commit (May 23, 2026).
Good architecture, incomplete edge-case handling.

**Score: 7.5/10** (Architecture 9, Type Safety 9, Error Handling 5, Test Coverage 4, Docs 8).

**Key file paths:**

| Purpose | Path |
|---|---|
| Entry point | `src/index.ts` |
| Server setup | `src/mcp/server.ts` |
| Zip code tool | `src/mcp/tools/search_zip_code.ts` |
| ViaCEP client | `src/infrastructure/clients/viacep_client.ts` |
| Domain schemas | `src/domain/zip_code.ts` |
| Service container | `src/infrastructure/service.ts` |
| Integration tests | `tests/tools/viacep.test.ts` |
| MCP VSCode config | `.vscode/mcp.json` |

---

# Combined Verdict

| | `brazil-mcp-server` | `brazilinfo-mcp` |
|---|---|---|
| Language | Python (FastMCP) | TypeScript (MCP SDK) |
| Maturity | Production, 25 tools, deployed | Prototype, 1 tool |
| Useful data for Candidato | None (CNPJ/CEP/PIX/agri) | None (CEP only) |
| Value as reference | **High** — auth, scope tiers, caching, tests | Medium — clean minimal TS template |

**Bottom line:** neither ships electoral, voting, attendance, or candidate data — they are
Brazilian utility-data servers. Their only value here is architectural:

- Build the elections MCP server in **Python** → copy `brazil-mcp-server` patterns
  (ScopedFastMCP tiers, middleware, async httpx + cache, test layout).
- Build it in **TypeScript** → `brazilinfo-mcp` is a clean skeleton to fork; add real data
  + error handling yourself.

The actual electoral data must come from the sources in `DATA-SOURCES.md`
(Câmara / Senado Dados Abertos, TSE, Base dos Dados, Basômetro / Radar Parlamentar).
