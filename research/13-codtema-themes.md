# Câmara `codTema` — the 32 policy themes (reference)

*Compiled 2026-06-27, fetched live from `GET /referencias/proposicoes/codTema`. This is the
Câmara's **official closed list** of policy themes. Each proposição is tagged with one or more of
these. We use them as a topic's discovery config (`topics.cod_temas`) — see
[how to add a topic](../README.md). A bill can carry several themes (read a bill's themes, with a
`relevancia` score, from `/proposicoes/{id}/temas`).*

| cod | Theme | What it covers (what bills fall under it) |
|----:|-------|--------------------------------------------|
| 34 | Administração Pública | Public administration: civil service, public-sector careers/salaries, agencies, procurement, transparency, administrative organization. |
| 35 | Arte, Cultura e Religião | Culture, the arts, heritage, cultural funding/incentives, religion. |
| 37 | Comunicações | Telecom, broadcasting, internet/spectrum, press, postal services, media concessions. |
| 39 | Esporte e Lazer | Sport, leisure, athletes, sporting events, sport funding. |
| 40 | **Economia** | The economy broadly: macroeconomic policy, money/credit, prices, competition, **taxation of economic activity** — a secondary home for tax bills. |
| 41 | Cidades e Desenvolvimento Urbano | Cities, urban planning/policy, housing, sanitation, urban mobility infrastructure. |
| 42 | Direito Civil e Processual Civil | Civil law & civil procedure: contracts, family, property, civil liability, civil courts. |
| 43 | Direito Penal e Processual Penal | Criminal law & procedure: crimes, penalties, policing powers, criminal courts. |
| 44 | Direitos Humanos e Minorias | Human rights, minorities, racial/gender/LGBT+ rights, persons with disabilities, children/elderly. |
| 46 | Educação | Education at all levels: schools/universities, curriculum, funding (FUNDEB), teachers, student policy. |
| 48 | Meio Ambiente e Desenvolvimento Sustentável | Environment & sustainability: conservation, pollution, climate, forests, environmental licensing. |
| 51 | Estrutura Fundiária | Land structure: agrarian reform, land tenure/titling, rural/indigenous/quilombola land. |
| 52 | Previdência e Assistência Social | Pensions & social assistance: social security, benefits (BPC, Bolsa Família), **social contributions**. |
| 53 | Processo Legislativo e Atuação Parlamentar | The legislative process itself: house rules, parliamentary activity, mandates, internal procedure. |
| 54 | Energia, Recursos Hídricos e Minerais | Energy, water resources, mining/minerals: electricity, oil & gas, royalties, water/mineral rights. |
| 55 | Relações Internacionais e Comércio Exterior | Foreign affairs & foreign trade: treaties, diplomacy, tariffs, trade agreements. |
| 56 | Saúde | Health: SUS, public health, medicines, sanitary regulation (ANVISA), health professions. |
| 57 | Defesa e Segurança | Defense & public security: armed forces, police, public safety, arms, borders. |
| 58 | Trabalho e Emprego | Labor & employment: labor law, wages, unions, workplace safety, employment programs. |
| 60 | Turismo | Tourism: sector promotion, tourism infrastructure/incentives. |
| 61 | Viação, Transporte e Mobilidade | Roads, transport & mobility: highways, ports, airports, transit, vehicle/traffic rules. |
| 62 | Ciência, Tecnologia e Inovação | Science, technology & innovation: research, R&D incentives, digital/innovation policy. |
| 64 | Agricultura, Pecuária, Pesca e Extrativismo | Agriculture, livestock, fishing, extractivism: rural credit, agricultural policy, food production. |
| 66 | Indústria, Comércio e Serviços | Industry, commerce & services: business regulation, sector incentives, trade/services rules. |
| 67 | Direito e Defesa do Consumidor | Consumer law & protection: consumer rights, product/service standards, abusive practices. |
| 68 | **Direito Constitucional** | Constitutional law: **PECs (constitutional amendments)** and constitutional rules — where **tax-reform PECs** live. |
| 70 | **Finanças Públicas e Orçamento** | Public finance & budget: **the tax system, taxation, budgets, credits, public debt, fiscal rules** — the **primary home of tax bills**. |
| 72 | Homenagens e Datas Comemorativas | Honors & commemorative dates: naming things, official dates, tributes (rarely substantive). |
| 74 | Política, Partidos e Eleições | Politics, parties & elections: electoral law, party rules, campaign finance, the political system. |
| 76 | Direito e Justiça | Law & justice: the judiciary, courts' organization, legal professions, justice administration. |
| 85 | Ciências Exatas e da Terra | Exact & earth sciences (academic classification; rarely a legislative driver). |
| 86 | Ciências Sociais e Humanas | Social sciences & humanities (academic classification; rarely a legislative driver). |

## Picking `cod_temas` for a topic

- A narrow topic (e.g. **"Tributação de riqueza"**) has **no dedicated theme** — taxation lives
  inside the broad fiscal themes. Curate the *inclusive* set: **`70` Finanças Públicas** (primary),
  **`40` Economia** (secondary), **`68` Direito Constitucional** (for tax-reform PECs). That's the
  seeded `tributacao-da-riqueza` config.
- A broad topic that **is** a theme (e.g. **"Meio Ambiente"** → `[48]`, **"Saúde"** → `[56]`) maps
  to a single `codTema` cleanly.
- **Trade-off:** the themes are coarse (only 32). A topic's `cod_temas` net catches *all* its laws
  but also unrelated bills in the same theme (e.g. `70` includes budgets/credits, not just tax).
  Accept the breadth, or add a later narrowing pass (keyword/ementa filter). See
  [`09-topic-to-law-discovery.md`](09-topic-to-law-discovery.md).
