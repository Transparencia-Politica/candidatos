/* Shared scorecard rendering + theme toggle for both pages (live app + GitHub Pages).
   SOURCE OF TRUTH: candidatos/shared/. docs/shared/ is a generated copy — do not edit it.

   Exposes globals (no module system) for rendering, filters, theme, and language controls. */

const BRL = n => 'R$ ' + Number(n || 0).toLocaleString('pt-BR', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2
});
const COLORS = ['#0f766e', '#b45309', '#2563eb', '#7c3aed', '#be123c'];
const el = id => document.getElementById(id);
const pct = value => value === null || value === undefined ? '—' : `${value}%`;
const slugify = (name, id) => 'c-' + id + '-' + String(name || '').toLowerCase()
  .normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

const I18N = {
  pt: {
    langName: 'Português',
    langToggle: 'EN',
    langTitle: 'Switch to English',
    pageTitleStatic: 'Candidato · Scorecards',
    pageSubtitleStatic: 'Como deputados(as) e senadores(as) votaram nas leis de tributação da riqueza: tributação progressiva ou proteção da concentração. Snapshot público, sem servidor.',
    pageTitleLive: 'Candidato · Scorecard',
    pageSubtitleLive: 'Busque um(a) deputado(a) ou senador(a), calcule se os votos caminham para tributação progressiva ou proteção da concentração, e leia o resultado armazenado em MySQL.',
    snapshotBadge: 'snapshot',
    mysqlBadge: 'MySQL API',
    filtersTitle: 'Filtros',
    filtersSubtitle: 'buscar, ordenar e combinar critérios',
    detailBack: '← Voltar à busca',
    loadingScorecards: 'Carregando scorecards…',
    capitalWealth: 'patrimônio em capital',
    lawCoverage: 'cobertura de leis relevantes',
    confidence: 'confiança da leitura',
    confidenceTip: 'Percentual ponderado das leis relevantes em que há voto registrado. Leis centrais para tributação da riqueza pesam mais; ausência reduz confiança, não vira automaticamente posição política.',
    progressiveTaxation: 'tributação progressiva',
    progressiveTip: 'Pontuação ponderada dos votos registrados em leis de tributação da riqueza. 100% significa caminhar na direção de uma carga tributária mais progressiva; 0% significa proteger a concentração de riqueza.',
    keyProjectAttendance: 'presença no projeto-chave',
    assetExposure: 'exposição patrimonial ao tema',
    assetExposureTip: 'Leitura contextual: só aparece quando o patrimônio declarado tem bens parecidos com a base tributada pela lei. Não muda a pergunta principal, que é se o voto favorece tributação progressiva ou proteção da concentração de riqueza.',
    govAligned: 'alinhado ao Governo',
    govAlignedTip: 'Em cada votação, o líder do Governo orienta como a base deve votar — é o "voto do Governo". Este é o % de votos em que o(a) parlamentar seguiu essa orientação.',
    oppAligned: 'alinhado à Oposição',
    oppAlignedTip: 'O mesmo para a Oposição: o % de votos em que o(a) parlamentar seguiu a orientação de voto dos líderes de oposição.',
    declaredWealth: 'Patrimônio declarado',
    wealthUnavailableTitle: 'Declaração de bens não disponível para este(a) parlamentar.',
    wealthUnavailableBody: 'O patrimônio é puxado da base de candidaturas do TSE, que aqui só está mapeada para a eleição de <b>2022</b>. Senadores cumprem mandato de <b>8 anos escalonado</b>, então quem foi eleito em <b>2018</b> ainda não tem os bens coletados por esta fonte. Isso é uma <b>limitação da fonte de dados</b> — não significa que a pessoa não tenha patrimônio. O score baseado em votos nominais não é afetado.',
    capitalShare: pct => `${pct}% em ações/participações ou exterior`,
    noStoredAssets: 'Sem bens armazenados.',
    lawsVotes: 'Leis, palavras-chave e votos armazenados',
    law: 'Lei',
    topic: 'Tópico',
    vote: 'Voto',
    attendance: 'Presença',
    key: 'chave',
    notEvaluated: 'não avaliado',
    notEvaluatedTitle: 'Esta lei foi adicionada depois deste scorecard — recalcule o candidato (Buscar) para avaliá-la. Não significa ausência.',
    contextNoScore: 'Contexto: não move o score',
    yesProgressive: 'SIM = tributação progressiva',
    yesConcentration: 'SIM = protege concentração',
    mixedDirection: 'Direção mista por palavra-chave',
    context: 'contexto',
    central: 'central',
    support: 'apoio',
    veryHigh: 'muito alto',
    high: 'alto',
    moderate: 'moderado',
    low: 'baixo',
    adjusted: 'ajustado',
    criteriaTitle: interactive => interactive ? 'Critérios e Pesos' : 'Critérios e pesos',
    criteriaSubtitle: interactive => interactive ? 'ajustar o argumento' : 'ver como pontuamos',
    criteriaIntro: uniformDir => `Este voto caminhou para <b>tributação mais progressiva</b> ou para <b>proteger a concentração de riqueza</b>? A inspiração em Zucman prioriza grandes fortunas, offshore, fundos exclusivos, dividendos e imposto mínimo sobre alta renda.${uniformDir ? ` Nestes critérios, um voto <b>${uniformDir}</b>; o` : ' O'} <b>peso</b> ajusta quanto cada lei conta.`,
    centralLegend: '<b>central</b> — sinal direto da tese',
    supportLegend: '<b>apoio</b> — reforça a tese',
    adjustWeightsRule: 'Ajuste os pesos e clique em <b>Aplicar</b> para atualizar o grid.',
    weightDefinesRule: 'O peso define quanto cada lei conta no cálculo.',
    changedWeights: '<span class="pulse"></span>Pesos alterados — clique em aplicar para atualizar o grid.',
    defaultWeights: 'Pesos padrão aplicados ao grid.',
    resetWeights: 'Resetar pesos',
    applyWeights: 'Aplicar pesos',
    officialSource: 'fonte oficial',
    sources: 'Fontes: ',
    contextWhy: (count, label) => `Por que ${count > 1 ? 'estas leis não entram' : `a ${label} não entra`} no score?`,
    contextNote: (items, plural, sources) => `Este recorte, inspirado em Zucman, mede tributação de <b>riqueza e renda de capital</b>. ${items} Fica${plural ? 'm' : ''} registrada${plural ? 's' : ''} como contexto, sem mover o score.${sources ? ` <span class="rub-note-src">${sources}</span>` : ''}`,
    methodTitle: 'Como o score é calculado',
    methodBody: 'Para cada palavra-chave associada a uma lei, a direção indica o que um voto <code>Sim</code> representa. <code>+1</code> significa avançar a tese, <code>-1</code> significa bloquear a tese, e <code>0</code> é contexto sem direção de riqueza. <code>Abstenção</code>, <code>Obstrução</code> e <code>Artigo 17</code> são evidência registrada neutra. <code>AUSENTE</code> e leis sem votação nominal reduzem cobertura/confiança, mas não viram posição política.',
    methodWarn: 'Ausência continua sendo ausência: o banco guarda presença, cobertura e evidência separadamente para evitar transformar dado faltante em intenção.',
    opinionPositive: 'Vota por tributação progressiva',
    opinionNegative: 'Protege concentração de riqueza',
    opinionMixed: 'Voto dividido',
    howMeasured: 'Como medimos',
    opinionInfoBody: '<b>Como medimos.</b> Em cada lei sobre tributação da riqueza, um voto a favor da tributação progressiva conta positivo: desloca a carga para grandes fortunas, renda de capital, dividendos, offshore ou estruturas de alta renda. Um voto contra conta negativo: preserva a concentração de riqueza e as formas de pagar menos imposto. Ausência reduz a <b>confiança da leitura</b>, mas não vira posição política. Leis sem votação nominal e a reforma do consumo, sem direção de riqueza, ficam de fora. A % é a média ponderada dos votos registrados. É <b>uma lente</b>, não um veredito — a matemática está aberta.',
    noProgressiveVotes: 'Tributação progressiva: sem votos suficientes para medir.',
    consideredLaws: n => `tributação progressiva · ${n} lei(s) considerada(s)`,
    protectsConcentration: 'protege concentração',
    progressiveEnd: 'tributação progressiva',
    legendText: 'A <b>%</b> mede se o voto caminhou para <b>tributação progressiva</b> ou para <b>proteção da concentração de riqueza</b> — <b class="op-nao-ink">0% = protege concentração</b> · <b class="op-sim-ink">100% = tributação progressiva</b>.',
    opinionTitle: (label, pct) => `${label} — ${pct}% em tributação progressiva (0% protege concentração · 100% tributa riqueza)`,
    wealthUnknown: 'patrimônio —',
    noCandidates: 'Nenhum candidato no banco corresponde — use <b>Buscar</b> para procurar um nome novo (Câmara → Senado).',
    filterNamePlaceholder: 'Buscar por nome…',
    filterNameTip: 'Filtra a lista pelo nome do(a) parlamentar. Ignora acentos e maiúsculas/minúsculas.',
    house: 'Casa',
    houseTip: 'Câmara mostra os(as) deputados(as); Senado, os(as) senadores(as); Todas, os dois.',
    all: 'Todas',
    sort: 'Ordenar',
    sortTip: 'Ordena por nome ou pelo patrimônio declarado. Quem não tem patrimônio conhecido vai para o fim.',
    sortName: 'Nome (A→Z)',
    sortWealthDesc: 'Patrimônio (maior→menor)',
    sortWealthAsc: 'Patrimônio (menor→maior)',
    party: 'Partido',
    partyTip: 'Mostra só parlamentares dos partidos marcados. Clique para marcar vários.',
    uf: 'UF',
    ufTip: 'Mostra só parlamentares dos estados (UF) marcados. Clique para marcar vários.',
    wealth: 'Patrimônio',
    wealthTip: 'Faixa de patrimônio declarado no TSE (R$). "Incluir desconhecido" mantém quem não teve a declaração localizada (mostrado como —).',
    minMoney: 'mín R$',
    maxMoney: 'máx R$',
    includeUnknown: 'incluir desconhecido',
    progressivePct: 'Progressiva %',
    progressivePctTip: 'Faixa do score de tributação progressiva: 0 = protege concentração de riqueza, 100 = tributa riqueza de forma mais progressiva. Quem não tem score fica de fora.',
    progressiveScale: '0 = protege concentração · 100 = tributação progressiva',
    voteFilterTip: 'Filtra por como votou numa lei específica: SIM, NÃO ou AUSENTE naquela votação.',
    anyLaw: 'qualquer lei',
    anyVote: 'qualquer voto',
    votedYes: 'votou SIM',
    votedNo: 'votou NÃO',
    govMin: 'Gov. mín %',
    govMinTip: 'Em cada votação, o líder do Governo orienta como a base deve votar — é o "voto do Governo". O alinhamento é o % de votos em que o(a) parlamentar seguiu essa orientação. Este filtro mostra só quem fica no mínimo escolhido ou acima.',
    clearFilters: 'Limpar filtros',
    loadingEmpty: 'Nenhum scorecard disponível neste snapshot.',
    loadError: err => `Erro ao carregar os dados: ${err}`,
    snapshotFooter: (n, when) => `Snapshot estático · ${n} parlamentares · gerado em ${when}`,
    searchTab: 'Busca',
    selectedTab: 'Selecionado',
    liveSearchPlaceholder: 'Filtre a grade ou digite um nome novo…',
    searchButton: 'Buscar',
    randomCached: '🎲 No banco',
    randomCachedTitle: 'Abre um candidato já no banco',
    randomNew: '🎲 Novo',
    randomNewTitle: 'Sorteia um deputado novo e calcula o score',
    liveGridHint: 'A grade mostra quem já está no banco — digite para filtrar. Clique em <b>Buscar</b> para procurar um nome novo (Câmara → Senado).',
  },
  en: {
    langName: 'English',
    langToggle: 'PT',
    langTitle: 'Trocar para português',
    pageTitleStatic: 'Candidato · Scorecards',
    pageSubtitleStatic: 'How deputies and senators voted on wealth-tax laws: progressive taxation or protection of concentration. Public snapshot, no server.',
    pageTitleLive: 'Candidato · Scorecard',
    pageSubtitleLive: 'Search for a deputy or senator, calculate whether votes move toward progressive taxation or protection of concentration, and read the result stored in MySQL.',
    snapshotBadge: 'snapshot',
    mysqlBadge: 'MySQL API',
    filtersTitle: 'Filters',
    filtersSubtitle: 'search, sort, and combine criteria',
    detailBack: '← Back to search',
    loadingScorecards: 'Loading scorecards…',
    capitalWealth: 'capital assets',
    lawCoverage: 'relevant-law coverage',
    confidence: 'reading confidence',
    confidenceTip: 'Weighted share of relevant laws with a recorded vote. Core wealth-tax laws weigh more; absence reduces confidence, it does not automatically become a political stance.',
    progressiveTaxation: 'progressive taxation',
    progressiveTip: 'Weighted score from recorded votes on wealth-tax laws. 100% means moving toward a more progressive tax burden; 0% means protecting wealth concentration.',
    keyProjectAttendance: 'key-project attendance',
    assetExposure: 'asset exposure to the topic',
    assetExposureTip: 'Contextual reading: shown only when declared assets resemble the tax base affected by the law. It does not change the main question: whether the vote favors progressive taxation or protection of wealth concentration.',
    govAligned: 'aligned with Government',
    govAlignedTip: 'In each roll call, the Government leader recommends how the coalition should vote. This is the share of votes where the parliamentarian followed that recommendation.',
    oppAligned: 'aligned with Opposition',
    oppAlignedTip: 'Same for the Opposition: the share of votes where the parliamentarian followed opposition leaders’ recommendation.',
    declaredWealth: 'Declared assets',
    wealthUnavailableTitle: 'Declared assets are not available for this parliamentarian.',
    wealthUnavailableBody: 'Assets come from the TSE candidacy database, which is currently mapped here only for the <b>2022</b> election. Senators serve staggered <b>8-year</b> terms, so people elected in <b>2018</b> may not have asset data collected from this source yet. This is a <b>data-source limitation</b> — it does not mean the person has no assets. The roll-call vote score is not affected.',
    capitalShare: pct => `${pct}% in shares/ownership interests or foreign assets`,
    noStoredAssets: 'No stored assets.',
    lawsVotes: 'Stored laws, keywords, and votes',
    law: 'Law',
    topic: 'Topic',
    vote: 'Vote',
    attendance: 'Attendance',
    key: 'key',
    notEvaluated: 'not evaluated',
    notEvaluatedTitle: 'This law was added after this scorecard was computed — recalculate the candidate (Search) to evaluate it. It does not mean absence.',
    contextNoScore: 'Context: does not move the score',
    yesProgressive: 'YES = progressive taxation',
    yesConcentration: 'YES = protects concentration',
    mixedDirection: 'Mixed direction by keyword',
    context: 'context',
    central: 'core',
    support: 'support',
    veryHigh: 'very high',
    high: 'high',
    moderate: 'moderate',
    low: 'low',
    adjusted: 'adjusted',
    criteriaTitle: () => 'Criteria and Weights',
    criteriaSubtitle: interactive => interactive ? 'adjust the argument' : 'see how we score',
    criteriaIntro: uniformDir => `Did this vote move toward <b>more progressive taxation</b> or toward <b>protecting wealth concentration</b>? The Zucman-inspired lens prioritizes large fortunes, offshore assets, exclusive funds, dividends, and minimum taxation on high incomes.${uniformDir ? ` Under these criteria, a vote <b>${uniformDir}</b>; the` : ' The'} <b>weight</b> adjusts how much each law counts.`,
    centralLegend: '<b>core</b> — direct signal for the thesis',
    supportLegend: '<b>support</b> — reinforces the thesis',
    adjustWeightsRule: 'Adjust weights and click <b>Apply</b> to update the grid.',
    weightDefinesRule: 'Weight defines how much each law counts in the calculation.',
    changedWeights: '<span class="pulse"></span>Weights changed — click apply to update the grid.',
    defaultWeights: 'Default weights applied to the grid.',
    resetWeights: 'Reset weights',
    applyWeights: 'Apply weights',
    officialSource: 'official source',
    sources: 'Sources: ',
    contextWhy: (count, label) => `Why ${count > 1 ? 'these laws do not enter' : `${label} does not enter`} the score?`,
    contextNote: (items, plural, sources) => `This Zucman-inspired slice measures taxation of <b>wealth and capital income</b>. ${items} It stays recorded as context, without moving the score.${sources ? ` <span class="rub-note-src">${sources}</span>` : ''}`,
    methodTitle: 'How the score is calculated',
    methodBody: 'For each keyword attached to a law, the direction says what a <code>Yes</code> vote represents. <code>+1</code> means advancing the thesis, <code>-1</code> means blocking it, and <code>0</code> is wealth-neutral context. <code>Abstention</code>, <code>Obstruction</code>, and <code>Article 17</code> are recorded neutral evidence. <code>ABSENT</code> and laws without nominal roll calls reduce coverage/confidence, but do not become a political position.',
    methodWarn: 'Absence remains absence: the database stores attendance, coverage, and evidence separately to avoid turning missing data into intent.',
    opinionPositive: 'Votes for progressive taxation',
    opinionNegative: 'Protects wealth concentration',
    opinionMixed: 'Mixed vote',
    howMeasured: 'How we measure',
    opinionInfoBody: '<b>How we measure.</b> In each wealth-tax law, a vote for progressive taxation counts positive: it shifts the burden toward large fortunes, capital income, dividends, offshore assets, or high-income structures. A vote against counts negative: it preserves wealth concentration and ways to pay less tax. Absence reduces <b>reading confidence</b>, but does not become a political stance. Laws without nominal roll calls and consumption-tax reform, with no wealth direction, stay out. The % is the weighted average of recorded votes. It is <b>a lens</b>, not a verdict — the math is open.',
    noProgressiveVotes: 'Progressive taxation: not enough votes to measure.',
    consideredLaws: n => `progressive taxation · ${n} law(s) considered`,
    protectsConcentration: 'protects concentration',
    progressiveEnd: 'progressive taxation',
    legendText: 'The <b>%</b> measures whether the vote moved toward <b>progressive taxation</b> or toward <b>protecting wealth concentration</b> — <b class="op-nao-ink">0% = protects concentration</b> · <b class="op-sim-ink">100% = progressive taxation</b>.',
    opinionTitle: (label, pct) => `${label} — ${pct}% progressive taxation (0% protects concentration · 100% taxes wealth)`,
    wealthUnknown: 'assets —',
    noCandidates: 'No stored candidate matches — use <b>Search</b> to look for a new name (Câmara → Senado).',
    filterNamePlaceholder: 'Search by name…',
    filterNameTip: 'Filters the list by parliamentarian name. Ignores accents and case.',
    house: 'House',
    houseTip: 'Câmara shows deputies; Senado shows senators; All shows both.',
    all: 'All',
    sort: 'Sort',
    sortTip: 'Sorts by name or declared assets. People without known assets go to the end.',
    sortName: 'Name (A→Z)',
    sortWealthDesc: 'Assets (high→low)',
    sortWealthAsc: 'Assets (low→high)',
    party: 'Party',
    partyTip: 'Shows only parliamentarians from selected parties. Click to select several.',
    uf: 'State',
    ufTip: 'Shows only parliamentarians from selected states. Click to select several.',
    wealth: 'Assets',
    wealthTip: 'Declared-asset range in the TSE data (R$). “Include unknown” keeps people whose declaration was not found (shown as —).',
    minMoney: 'min R$',
    maxMoney: 'max R$',
    includeUnknown: 'include unknown',
    progressivePct: 'Progressive %',
    progressivePctTip: 'Progressive-taxation score range: 0 = protects wealth concentration, 100 = taxes wealth more progressively. People without a score stay out.',
    progressiveScale: '0 = protects concentration · 100 = progressive taxation',
    voteFilterTip: 'Filters by how the person voted on a specific law: YES, NO, or ABSENT in that roll call.',
    anyLaw: 'any law',
    anyVote: 'any vote',
    votedYes: 'voted YES',
    votedNo: 'voted NO',
    govMin: 'Gov. min %',
    govMinTip: 'In each roll call, the Government leader recommends how the coalition should vote. Alignment is the share of votes where the parliamentarian followed that recommendation. This filter shows only people at or above the chosen minimum.',
    clearFilters: 'Clear filters',
    loadingEmpty: 'No scorecards are available in this snapshot.',
    loadError: err => `Error loading data: ${err}`,
    snapshotFooter: (n, when) => `Static snapshot · ${n} parliamentarians · generated at ${when}`,
    searchTab: 'Search',
    selectedTab: 'Selected',
    liveSearchPlaceholder: 'Filter the grid or type a new name…',
    searchButton: 'Search',
    randomCached: '🎲 Stored',
    randomCachedTitle: 'Open a candidate already in the database',
    randomNew: '🎲 New',
    randomNewTitle: 'Pick a new deputy and calculate the score',
    liveGridHint: 'The grid shows people already in the database — type to filter. Click <b>Search</b> to look for a new name (Câmara → Senado).',
  }
};

const LANG_KEY = 'candidato-lang';
function currentLang(){
  try{
    const saved = localStorage.getItem(LANG_KEY);
    if(saved === 'en' || saved === 'pt') return saved;
  }catch(e){}
  return 'pt';
}
function tr(key, ...args){
  const dict = I18N[currentLang()] || I18N.pt;
  const value = dict[key] ?? I18N.pt[key] ?? key;
  return typeof value === 'function' ? value(...args) : value;
}
function setLang(lang){
  try{ localStorage.setItem(LANG_KEY, lang); }catch(e){}
  document.documentElement.lang = lang === 'en' ? 'en' : 'pt-br';
}
function applyStaticTranslations(){
  document.documentElement.lang = currentLang() === 'en' ? 'en' : 'pt-br';
  for(const node of document.querySelectorAll('[data-i18n]')){
    node.innerHTML = tr(node.dataset.i18n);
  }
  for(const node of document.querySelectorAll('[data-i18n-title]')){
    node.setAttribute('title', tr(node.dataset.i18nTitle));
  }
  for(const node of document.querySelectorAll('[data-i18n-placeholder]')){
    node.setAttribute('placeholder', tr(node.dataset.i18nPlaceholder));
  }
}

const ZUCMAN_ARGUMENTS = {
  pt: {
    'igf-grandes-fortunas': 'Taxa diretamente o estoque de grandes fortunas. É o sinal mais próximo da tese de tributar riqueza concentrada.',
    'pl-4173-2023': 'Ataca estruturas usadas por alta renda e grande patrimônio: offshore e fundos exclusivos.',
    'pl-1087-2025': 'Cria imposto mínimo sobre altas rendas e alcança grandes fluxos de lucros e dividendos.',
    'pl-2337-2021': 'Tributa dividendos, uma forma central de renda de capital que favorece quem vive de propriedade e empresa.',
    'pec-45-2019': 'Entra só como contexto fiscal. Reforma consumo, mas não mede diretamente tributação de riqueza.'
  },
  en: {
    'igf-grandes-fortunas': 'Directly taxes the stock of large fortunes. This is the closest signal to the thesis of taxing concentrated wealth.',
    'pl-4173-2023': 'Targets structures used by high income and large wealth: offshore assets and exclusive funds.',
    'pl-1087-2025': 'Creates a minimum tax on high incomes and reaches large flows of profits and dividends.',
    'pl-2337-2021': 'Taxes dividends, a central form of capital income that favors people who live from ownership and business income.',
    'pec-45-2019': 'Only enters as fiscal context. It reforms consumption taxes, but does not directly measure wealth taxation.'
  }
};

function chipClass(score){
  const status = score?.vote_status || '';
  if(status.includes('sim')) return 'c-sim';
  if(status.includes('nao') || status.includes('não')) return 'c-nao';
  if(status.includes('misto')) return 'c-mix';
  return 'c-aus';
}

function identityHtml(card){
  const p = card.politic;
  // Senators come from the Senado (no Câmara/TSE candidate ids); deputies show the full id line.
  const idLine = p.house === 'senado'
    ? `Senado ${p.senado_id}`
    : `Câmara ${p.camara_id} · TSE ${p.tse_year}/${p.tse_uf} · SQ ${p.tse_sq}`;
  return `<div class="identity">
    <div class="avatar">${(p.name || '?').slice(0,1)}</div>
    <div>
      <div class="name">${p.name}</div>
      <div class="muted">${p.party || '—'} · ${p.uf || '—'} · ${p.occupation || '—'}</div>
      <div class="muted">${idLine}</div>
    </div>
  </div>`;
}

// Wealth is "known" when we matched a TSE candidacy (tse_sq). Deputies always have it; senators
// have it only when resolved (currently 2022-elected). Unresolved -> show '—'/a note, never a
// misleading R$ 0,00 that reads as "declared nothing".
const wealthKnown = p => p.tse_sq != null && p.tse_sq !== '';

function metricsHtml(card){
  const s = card.summary;
  const known = wealthKnown(card.politic);
  // Gov/Oposição alignment is genuinely absent for senators (the Senado /votacao feed has no
  // party line); the wealth metrics fall back to '—' only when the TSE candidacy wasn't found.
  const metrics = [
    [known ? pct(s.wealth_capital_pct) : '—', tr('capitalWealth')],
    [pct(s.coverage_pct), tr('lawCoverage')],
    [pct(s.confidence_pct), tr('confidence'), tr('confidenceTip')],
    [pct(s.pro_redistribution_score), tr('progressiveTaxation'), tr('progressiveTip')],
    [pct(s.key_attendance_pct), tr('keyProjectAttendance')],
    [!known || s.self_interest_alignment_score === null ? '—' : pct(s.self_interest_alignment_score), tr('assetExposure'), tr('assetExposureTip')],
    [s.gov_alignment_pct === null || s.gov_alignment_pct === undefined ? '—' : pct(s.gov_alignment_pct), tr('govAligned'), tr('govAlignedTip')],
    [s.opp_alignment_pct === null || s.opp_alignment_pct === undefined ? '—' : pct(s.opp_alignment_pct), tr('oppAligned'), tr('oppAlignedTip')]
  ];
  return `<section class="metrics">${
    metrics.map(([n,l,tip]) => `<div class="metric"><div class="n">${n}</div><div class="l">${l}${tip ? ' ' + filterInfo(tip) : ''}</div></div>`).join('')
  }</section>`;
}

function wealthHtml(card){
  const p = card.politic;
  if(!wealthKnown(p)){
    return `<section class="panel"><h2>${tr('declaredWealth')}</h2>
      <div class="note"><b>${tr('wealthUnavailableTitle')}</b><br>${tr('wealthUnavailableBody')}</div></section>`;
  }
  const rows = Object.entries(p.wealth_buckets || {})
    .filter(([,v]) => Number(v) > 0)
    .sort((a,b) => b[1] - a[1])
    .map(([label,value], i) => {
      const share = p.wealth_total ? (100 * value / p.wealth_total) : 0;
      return `<div class="row">
        <div>${label}<div class="bar"><i style="width:${share.toFixed(1)}%;background:${COLORS[i % COLORS.length]}"></i></div></div>
        <div style="text-align:right;white-space:nowrap">${BRL(value)}<br><span class="muted">${share.toFixed(1)}%</span></div>
      </div>`;
    }).join('');
  return `<section class="panel"><h2>${tr('declaredWealth')}</h2>
    <div class="wealth-grid">
      <div><div class="big">${BRL(p.wealth_total)}</div><div class="muted">${tr('capitalShare', p.wealth_capital_pct)}</div></div>
      <div>${rows || `<span class="muted">${tr('noStoredAssets')}</span>`}</div>
    </div></section>`;
}

function votesHtml(card){
  const rows = [];
  for(const topic of card.topics){
    for(const law of topic.laws){
      const score = law.score;
      // A law added after this scorecard was computed has no score yet — say so plainly
      // ('não avaliado' + tooltip) instead of an ambiguous 'sem score' that reads like an absence.
      const voteCell = score
        ? `<span class="chip ${chipClass(score)}">${score.vote_label}</span>`
        : `<span class="chip c-na" title="${tr('notEvaluatedTitle')}">${tr('notEvaluated')}</span>`;
      rows.push(`<tr>
        <td><b>${law.label}</b><br><span class="muted">${law.description}</span>
          <div class="keywords">${law.keywords.map(k => `<span class="keyword">${k.label}</span>`).join('')}</div></td>
        <td>${topic.title}${law.is_key ? `<br><span class="chip c-mix">${tr('key')}</span>` : ''}</td>
        <td>${voteCell}</td>
        <td>${score ? `${score.present_count}/${score.nominal_count}` : '—'}</td>
      </tr>`);
    }
  }
  return `<section class="panel"><h2>${tr('lawsVotes')}</h2>
    <table><thead><tr><th>${tr('law')}</th><th>${tr('topic')}</th><th>${tr('vote')}</th><th>${tr('attendance')}</th></tr></thead>
    <tbody>${rows.join('')}</tbody></table></section>`;
}

function lawWeight(law){
  return (law.keywords || []).reduce((max, k) => Math.max(max, Math.abs(Number(k.weight || 0))), 0);
}

function lawDirectionLabel(law){
  const directional = (law.keywords || []).filter(k => Number(k.direction) !== 0);
  if(!directional.length) return tr('contextNoScore');
  if(directional.every(k => Number(k.direction) > 0)) return tr('yesProgressive');
  if(directional.every(k => Number(k.direction) < 0)) return tr('yesConcentration');
  return tr('mixedDirection');
}

function lawRole(law){
  if(!law.wealth_relevant || !lawSignalWeight(law)) return 'contexto';
  if(law.is_key) return 'central';
  return 'apoio';
}

function weightLabel(weight){
  const w = Math.abs(weight);
  if(w >= 1.5) return tr('veryHigh');
  if(w >= 1.25) return tr('high');
  if(w >= 0.75) return tr('moderate');
  if(w > 0) return tr('low');
  return '—';
}

// Bar fill is proportional to |weight| against a fixed reference so laws are visually comparable
// across rows and cards; clamp so a hand-raised weight can't overflow the track.
const WEIGHT_BAR_REF = 2.0;
const weightBarPct = weight => Math.min(100, Math.round(Math.abs(weight) / WEIGHT_BAR_REF * 100));

// SVG glyphs for the two rare per-law actions (invert sign / reset to default).
const ICON_FLIP = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="M7 10l-3 3 3 3M4 13h11M17 14l3-3-3-3M20 11H9"/></svg>';
const ICON_RESET = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/></svg>';

function rubricRows(topics){
  const seen = new Set(), rows = [];
  for(const topic of (topics || [])) for(const law of (topic.laws || [])){
    if(seen.has(law.slug)) continue;
    seen.add(law.slug);
    const keywords = (law.keywords || []).map(k => k.label).join(', ');
    const weight = lawWeight(law);
    rows.push({ topic, law, keywords, weight, role: lawRole(law) });
  }
  return rows.sort((a, b) => {
    const roleOrder = {central: 0, apoio: 1, contexto: 2};
    return (roleOrder[a.role] ?? 9) - (roleOrder[b.role] ?? 9) || b.weight - a.weight;
  });
}

function rubricArgument(law){
  return ZUCMAN_ARGUMENTS[currentLang()]?.[law.slug] || ZUCMAN_ARGUMENTS.pt[law.slug] || law.description || (currentLang() === 'en'
    ? 'Law selected for these topic criteria.'
    : 'Lei escolhida para estes critérios temáticos.');
}

// Weight module (right side of each scored row). Interactive mode keeps the DOM contract the
// roster handlers depend on: [data-law-weight] wrapper + [data-default-weight] and the
// data-weight-delta / -flip / -reset buttons. `applyWeightChange` reads the attributes, not the
// rendered number, so the displayed value is presentation-only.
function weightModuleHtml(law, weight, current, role, interactive){
  const flipped = current < 0;                         // ± turned this into a "protege concentração" sim
  const adjusted = Number(current.toFixed(2)) !== Number(weight.toFixed(2));
  const tone = flipped ? 'nao' : role;                 // rose when the sign was inverted, else role color
  const qualifier = adjusted ? tr('adjusted') : weightLabel(current);
  const scale = `<div class="wmod-scale"><div class="wmod-bar"><i class="${tone}" style="width:${weightBarPct(current)}%"></i></div>
    <span class="wmod-q${adjusted ? ' adj' : ''}">${qualifier}</span></div>`;
  if(!interactive){
    return `<div class="wmod wmod-static">
      <div class="wmod-staticval">${current.toFixed(2)}</div>${scale}</div>`;
  }
  return `<div class="wmod" data-law-weight="${law.slug}" data-default-weight="${weight}">
    <div class="wrow">
      <div class="stepper">
        <button type="button" data-weight-delta="-0.25" title="${currentLang() === 'en' ? 'Decrease weight' : 'Diminuir peso'}">−</button>
        <span class="mid">${current.toFixed(2)}</span>
        <button type="button" data-weight-delta="0.25" title="${currentLang() === 'en' ? 'Increase weight' : 'Aumentar peso'}">+</button>
      </div>
      <button type="button" class="wicon" data-weight-flip title="${currentLang() === 'en' ? 'Invert sign' : 'Inverter sinal'}">${ICON_FLIP}</button>
      <button type="button" class="wicon" data-weight-reset title="${currentLang() === 'en' ? 'Back to default' : 'Voltar ao padrão'}">${ICON_RESET}</button>
    </div>${scale}</div>`;
}

function scoringRubricHtml(topics, options = {}){
  const rows = rubricRows(topics);
  if(!rows.length) return '';
  const overrides = options.weightOverrides || {};
  const interactive = Boolean(options.interactive);
  const hasDraftChanges = Boolean(options.hasDraftChanges);
  const title = tr('criteriaTitle', interactive);
  const currentWeight = law => Object.prototype.hasOwnProperty.call(overrides, law.slug)
    ? Number(overrides[law.slug]) : lawWeight(law);

  // A law scores iff it has a directional keyword (lawSignalWeight > 0). That is the same predicate
  // used to decide whether a control renders — so we use it to both split rows and build the note,
  // guaranteeing the note lists exactly the laws we dropped from the interactive list.
  const scored = rows.filter(r => lawSignalWeight(r.law));
  const contexto = rows.filter(r => !lawSignalWeight(r.law));

  // Direction ("SIM = tributação progressiva" etc.) is stated once above the list only when every
  // scored law agrees; otherwise it stays per-row so a non-progressiva/mixed law is never mislabeled.
  const dirLabels = [...new Set(scored.map(r => lawDirectionLabel(r.law)))];
  const uniformDir = dirLabels.length === 1 ? dirLabels[0] : null;

  const scoredHtml = scored.map(({law, keywords, role}) => {
    const safeRole = role === 'contexto' ? 'apoio' : role;   // a scoring law is never "contexto"
    const current = currentWeight(law);
    const dirNote = uniformDir ? '' :
      `<span class="rlaw-dir"><span class="arrow">→</span> ${lawDirectionLabel(law)}</span>`;
    return `<div class="rlaw">
      <div>
        <div class="rlaw-head">
          <span class="rdot ${safeRole}"></span>
          <span class="rlaw-name">${law.label}</span>
          <span class="rlaw-sub">${keywords || law.description || ''}</span>${dirNote}
        </div>
        <p class="rlaw-body">${rubricArgument(law)}${law.source_url
          ? `<a class="rlaw-src" href="${law.source_url}" target="_blank" rel="noopener">${tr('officialSource')}</a>` : ''}</p>
      </div>
      ${weightModuleHtml(law, lawWeight(law), current, safeRole, interactive)}
    </div>`;
  }).join('');

  // Documented exclusion: instead of a dead, un-adjustable row, list context-only laws with the
  // reason they don't move the score, linking each law's own official source.
  const contextoSources = contexto.filter(c => c.law.source_url).map(({law}) =>
    `<a class="rlaw-src" href="${law.source_url}" target="_blank" rel="noopener">${contexto.length > 1 ? law.label : tr('officialSource')}</a>`);
  const contextItems = contexto.map(({law, keywords}) => `${law.label}${keywords ? ` (${keywords})` : ''} — ${rubricArgument(law)}`).join(' ');
  const contextSources = contextoSources.length ? `${contexto.length > 1 ? tr('sources') : ''}${contextoSources.join(', ')}` : '';
  const contextoHtml = contexto.length ? `<div class="rub-note">
      <b>${tr('contextWhy', contexto.length, contexto[0].law.label)}</b>
      ${tr('contextNote', contextItems, contexto.length > 1, contextSources)}
    </div>` : '';

  const legend = `<div class="rub-legend">
      <span class="lg"><span class="dot central"></span> ${tr('centralLegend')}</span>
      <span class="sep"></span>
      <span class="lg"><span class="dot apoio"></span> ${tr('supportLegend')}</span>
      <span class="lg rule" style="margin-left:auto">${interactive
        ? tr('adjustWeightsRule')
        : tr('weightDefinesRule')}</span>
    </div>`;

  const footer = interactive ? `<div class="rub-foot">
      <span class="status${hasDraftChanges ? ' dirty' : ''}">${hasDraftChanges
        ? tr('changedWeights')
        : tr('defaultWeights')}</span>
      <button class="secondary" type="button" data-weight-reset-all>${tr('resetWeights')}</button>
      <button class="primary" type="button" data-weight-apply>${tr('applyWeights')}</button>
    </div>` : '';

  return `<details class="panel collapse-panel rubric-panel"${options.collapseKey ? ` data-collapse-key="${options.collapseKey}"` : ''}>
    <summary><span>${title}</span><span class="muted">${tr('criteriaSubtitle', interactive)}</span></summary>
    <div class="rubric2">
      <p class="rub-intro">${tr('criteriaIntro', uniformDir)}</p>
      ${legend}
      ${scoredHtml}
      ${contextoHtml}
      ${footer}
    </div>
  </details>`;
}

function methodHtml(){
  return `<section class="panel">
    <h2>${tr('methodTitle')}</h2>
    <p>${tr('methodBody')}</p>
    <div class="note warn">${tr('methodWarn')}</div>
  </section>`;
}

/* ---- Opinion score: protege concentração ◄──► tributação progressiva ----
   Our default lens. For each wealth-distribution law, the sign of score_value says direction:
   progressive taxation versus protection of wealth concentration. The current keyword weights
   say how much that law should count. */

function lawSignalWeight(law){
  let weight = 0;
  for(const k of (law.keywords || [])){
    if(Number(k.direction) !== 0) weight = Math.max(weight, Math.abs(Number(k.weight || 1)));
  }
  return weight;
}

function effectiveLawWeight(law, weightOverrides){
  const base = lawSignalWeight(law);
  if(!base) return 0;
  if(weightOverrides && Object.prototype.hasOwnProperty.call(weightOverrides, law.slug)){
    const custom = Number(weightOverrides[law.slug]);
    return Number.isFinite(custom) ? custom : base;
  }
  return base;
}

function clamp(value, min, max){
  return Math.max(min, Math.min(max, value));
}

function lawAlignmentUnit(law){
  const weight = lawSignalWeight(law);
  const score = law.score;
  if(!weight || !score || score.score_value == null) return null;
  return clamp(Number(score.score_value), -weight, weight) / weight;
}

function opinionScore(card, weightOverrides){
  let sum = 0, totalWeight = 0, n = 0;
  for(const t of (card.topics || [])) for(const law of (t.laws || [])){
    // Only wealth-distribution laws with a real direction count (skips PEC 45 / direction 0).
    const weight = effectiveLawWeight(law, weightOverrides);
    if(!weight) continue;
    const unit = lawAlignmentUnit(law);
    if(unit !== null){
      sum += unit * weight; totalWeight += Math.abs(weight); n++;
    }   // present: positive (progressive) / negative (concentration) / 0 (abstenção)
    // Absences and 'sem-votacao-nominal' stay out of the score; confidence shows missing evidence.
  }
  if(!totalWeight) return null;                  // no relevant roll-calls in their term — can't read
  const alignment = sum / totalWeight;           // [-1, +1]
  const pct = Math.round((alignment + 1) / 2 * 100);  // 0 = protege concentração, 100 = tributação progressiva
  let label, tone;
  if(pct >= 60){ tone = 'sim'; label = tr('opinionPositive'); }
  else if(pct <= 40){ tone = 'nao'; label = tr('opinionNegative'); }
  else { tone = 'mix'; label = tr('opinionMixed'); }
  return { pct, alignment, n, label, tone };
}

// The ⓘ explainer — pure <details> so it works in both shells with no JS wiring.
function opinionInfo(){
  return `<details class="opinfo"><summary title="${tr('howMeasured')}">ⓘ</summary>
    <div class="opinfo-body">${tr('opinionInfoBody')}</div></details>`;
}

// Slim opinion row for the profile: label + % + meter + ⓘ.
function opinionHtml(card, weightOverrides){
  const o = opinionScore(card, weightOverrides);
  if(!o){
    return `<section class="panel opinion-panel"><div class="opinion-head">
      <span class="muted">${tr('noProgressiveVotes')}</span>${opinionInfo()}
      </div></section>`;
  }
  return `<section class="panel opinion-panel">
    <div class="opinion-head">
      <span class="opinion-pct op-${o.tone}">${o.pct}%</span>
      <div><div class="opinion-label">${o.label}</div>
        <div class="muted">${tr('consideredLaws', o.n)}</div></div>
      ${opinionInfo()}
    </div>
    <div class="opmeter"><i class="op-${o.tone}" style="width:${o.pct}%"></i></div>
    <div class="opmeter-ends"><span>${tr('protectsConcentration')}</span><span>${tr('progressiveEnd')}</span></div>
  </section>`;
}

// Slim legend explaining what the % means at each end — sits above the roster grid.
function opinionLegendHtml(){
  return `<div class="opinion-legend">
    <span class="oleg-bar" aria-hidden="true"></span>
    <span class="oleg-text">${tr('legendText')}</span>
  </div>`;
}

// Full scorecard body for one candidate (identity + opinion + metrics + wealth + votes + method).
function cardBodyHtml(card, options = {}){
  const weightOverrides = options.weightOverrides || {};
  return `<section class="panel">${identityHtml(card)}</section>`
    + opinionHtml(card, weightOverrides) + metricsHtml(card) + scoringRubricHtml(card.topics, { weightOverrides })
    + wealthHtml(card) + votesHtml(card) + methodHtml();
}

// Profile body for a non-legislator (President/governor) from a curated TSE profile. These have
// NO vote scorecard — they don't vote in Congress — so we show identity + declared wealth + an
// explicit note instead of metrics/votes. Shape: research/perfis-precandidatos-2026.data.json.
function executiveProfileHtml(p){
  const src = p.source_election || {};
  const rows = Object.entries(p.wealth_buckets || {})
    .filter(([,v]) => Number(v) > 0)
    .sort((a,b) => b[1] - a[1])
    .map(([label,value], i) => {
      const share = p.wealth_total ? (100 * value / p.wealth_total) : 0;
      return `<div class="row">
        <div>${label}<div class="bar"><i style="width:${share.toFixed(1)}%;background:${COLORS[i % COLORS.length]}"></i></div></div>
        <div style="text-align:right;white-space:nowrap">${BRL(value)}<br><span class="muted">${share.toFixed(1)}%</span></div>
      </div>`;
    }).join('');
  return `<section class="panel"><div class="identity">
      <div class="avatar">${(p.display || '?').slice(0,1)}</div>
      <div>
        <div class="name">${p.display}</div>
        <div class="muted">${p.party_2026 || '—'} · ${p.office_2026 || '—'}</div>
        <div class="muted">${p.ocupacao || 'ocupação não informada'} · nascido(a) em ${p.municipio_nascimento || '—'}/${p.uf_nascimento || '—'}</div>
      </div>
    </div>
    <div class="note warn">Cargo do Executivo — <b>não vota no Congresso</b>, portanto não tem
    scorecard de votos nominais. Este é um <b>perfil</b> a partir do TSE.</div></section>
  <section class="panel"><h2>Patrimônio declarado</h2>
    <div class="note">Fonte: TSE DivulgaCand — <b>${src.cargo_label || 'candidatura'} ${src.year || ''}</b>.
    É um retrato de eleição passada, <b>não é o patrimônio atual</b> e não é comparável entre
    cargos/anos diferentes.</div>
    <div class="wealth-grid">
      <div><div class="big">${BRL(p.wealth_total)}</div><div class="muted">${p.n_bens || 0} bens declarados</div></div>
      <div>${rows || '<span class="muted">Sem bens declarados.</span>'}</div>
    </div></section>`;
}

/* ---- Cached-candidate grid (reusable components for a roster view) ----
   A roster entry is {name, party, uf, house, camara_id, senado_id, wealth_total}. */

// Stable key for a roster entry across both chambers (senators have no camara_id).
function candidateKey(c){ return c.house === 'senado' ? 's' + c.senado_id : 'c' + c.camara_id; }

// One clickable grid tile. `i` (optional) staggers the load animation.
function candidateCardHtml(c, i){
  const known = Number(c.wealth_total) > 0;
  const wealth = known ? BRL(c.wealth_total) : tr('wealthUnknown');
  const house = c.house === 'senado'
    ? '<span class="chip c-mix">Senado</span>'
    : '<span class="chip c-sim">Câmara</span>';
  const delay = i ? ` style="animation-delay:${Math.min(i, 14) * 28}ms"` : '';
  // Slim opinion badge — only when the entry carries it (Pages snapshot); the live app's
  // lightweight /api/politics roster has no scores, so its tiles stay unchanged.
  const op = c.opinion ? `<span class="opinion-tag op-${c.opinion.tone}" title="${tr('opinionTitle', c.opinion.label, c.opinion.pct)}">${c.opinion.pct}%<span class="op-i">ⓘ</span></span>` : '';
  return `<button class="ccard" type="button" data-key="${candidateKey(c)}"${delay}>
    <span class="ccard-top"><span class="avatar avatar-sm">${(c.name || '?').slice(0, 1)}</span>${house}${op}</span>
    <b class="ccard-name">${c.name}</b>
    <span class="muted ccard-meta">${c.party || '—'} · ${c.uf || '—'}</span>
    <span class="ccard-wealth${known ? '' : ' unknown'}">${wealth}</span>
  </button>`;
}

// The grid, or a friendly empty state.
function candidateGridHtml(list){
  if(!list.length){
    return `<div class="sub" style="margin-top:14px">${tr('noCandidates')}</div>`;
  }
  return `<div class="cgrid">${list.map((c, i) => candidateCardHtml(c, i)).join('')}</div>`;
}

/* ---- Filterable roster (GitHub Pages: filter the baked snapshot client-side) ----
   The snapshot carries the FULL scorecard per person, so we can filter on name, house, party,
   UF, declared wealth, and actual votes/alignment without any backend. These helpers are pure
   and shared so the live app can adopt them later. */

// Accent/case-insensitive name normalizer (matches the live app's `norm`).
const normName = s => (s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();

// Collapse a stored vote_status into one of SIM | NAO | AUSENTE | OUTRO for filtering.
function voteBucket(status){
  const v = status || '';
  if(v.includes('sim')) return 'SIM';
  if(v.includes('nao') || v.includes('não')) return 'NAO';
  if(v === 'ausente') return 'AUSENTE';
  return 'OUTRO';
}

// Flatten one full scorecard into a lightweight, filterable roster entry. Keeps the fields
// candidateCardHtml needs, plus wealth-known, summary alignment, and a {lawLabel -> SIM/NAO/…} map.
function rosterEntry(card, weightOverrides){
  const p = card.politic, s = card.summary || {};
  const votes = {};
  for(const t of (card.topics || [])) for(const law of (t.laws || [])){
    if(law.score) votes[law.label] = voteBucket(law.score.vote_status);
  }
  return {
    key: candidateKey(p),
    name: p.name, party: p.party || '', uf: p.uf || '', house: p.house || 'camara',
    camara_id: p.camara_id, senado_id: p.senado_id,
    wealth_total: Number(p.wealth_total) || 0,
    wealth_known: p.tse_sq != null && p.tse_sq !== '',
    gov: s.gov_alignment_pct, opp: s.opp_alignment_pct,
    opinion: opinionScore(card, weightOverrides),   // {pct, tone, label} | null — drives the slim tile badge
    votes, _name: normName(p.name),
  };
}

// Distinct facet values for populating the controls, in display order.
function rosterFacets(entries){
  const parties = [...new Set(entries.map(e => e.party).filter(Boolean))].sort((a,b) => a.localeCompare(b,'pt'));
  const ufs = [...new Set(entries.map(e => e.uf).filter(Boolean))].sort();
  const laws = [...new Set(entries.flatMap(e => Object.keys(e.votes)))].sort((a,b) => a.localeCompare(b,'pt'));
  return { parties, ufs, laws };
}

// Pure filter + sort. `f` = {query, house, parties[], ufs[], wealthMin, wealthMax, showUnknownWealth,
// govMin, voteLaw, voteValue, sort}. Unknown-wealth people are kept only when showUnknownWealth is
// on, and always sink to the bottom of a wealth sort (never faked as R$ 0 in the ordering).
function filterRoster(entries, f){
  const out = entries.filter(e => {
    if(f.query && !e._name.includes(f.query)) return false;
    if(f.house && f.house !== 'all' && e.house !== f.house) return false;
    if(f.parties && f.parties.length && !f.parties.includes(e.party)) return false;
    if(f.ufs && f.ufs.length && !f.ufs.includes(e.uf)) return false;
    if(!e.wealth_known){
      if(!f.showUnknownWealth) return false;
    }else{
      if(f.wealthMin != null && e.wealth_total < f.wealthMin) return false;
      if(f.wealthMax != null && e.wealth_total > f.wealthMax) return false;
    }
    if(f.govMin != null && (e.gov == null || e.gov < f.govMin)) return false;
    if(f.voteLaw && f.voteValue && (e.votes[f.voteLaw] || '') !== f.voteValue) return false;
    if(f.opinionMin != null || f.opinionMax != null){
      if(!e.opinion) return false;                 // no score → can't be in a % range
      if(f.opinionMin != null && e.opinion.pct < f.opinionMin) return false;
      if(f.opinionMax != null && e.opinion.pct > f.opinionMax) return false;
    }
    return true;
  });
  const w = e => e.wealth_known ? e.wealth_total : null;
  if(f.sort === 'wealth-desc') out.sort((a,b) => (w(b) ?? -1) - (w(a) ?? -1));
  else if(f.sort === 'wealth-asc') out.sort((a,b) => (w(a) ?? Infinity) - (w(b) ?? Infinity));
  else out.sort((a,b) => a.name.localeCompare(b.name,'pt'));
  return out;
}

// Render the filter panel. State lives in the page shell; this only emits markup with stable ids.
// A small ⓘ with a hover/focus tooltip — used to explain each filter.
// Escape & and " so quotes inside the text don't break the data-tip/aria-label attributes
// (CSS content:attr() decodes the entities back, so the tooltip shows the real characters).
function filterInfo(text){
  const safe = String(text).replace(/&/g, '&amp;').replace(/"/g, '&quot;');
  return `<span class="finfo" tabindex="0" role="img" aria-label="${safe}" data-tip="${safe}">ⓘ</span>`;
}

function filterControlsHtml(facets){
  const chip = (cls, attr, val, label) => `<button type="button" class="fchip" data-${attr}="${val}">${label}</button>`;
  const opts = (arr, ph) => `<option value="">${ph}</option>` + arr.map(x => `<option value="${x}">${x}</option>`).join('');
  const fi = filterInfo;
  return `<div class="filters">
    <div class="frow">
      <input id="f-query" class="search-input" placeholder="${tr('filterNamePlaceholder')}" autocomplete="off">
      ${fi(tr('filterNameTip'))}
      <span id="f-count" class="fcount"></span>
    </div>
    <div class="frow">
      <span class="flabel">${tr('house')}</span>${fi(tr('houseTip'))}
      <span class="fseg" id="f-house">
        <button type="button" data-house="all" class="on">${tr('all')}</button>
        <button type="button" data-house="camara">Câmara</button>
        <button type="button" data-house="senado">Senado</button>
      </span>
      <span class="flabel">${tr('sort')}</span>${fi(tr('sortTip'))}
      <select id="f-sort" class="fsel">
        <option value="name">${tr('sortName')}</option>
        <option value="wealth-desc">${tr('sortWealthDesc')}</option>
        <option value="wealth-asc">${tr('sortWealthAsc')}</option>
      </select>
    </div>
    <div class="frow"><span class="flabel">${tr('party')}</span>${fi(tr('partyTip'))}<span class="fchips" id="f-parties">${
      facets.parties.map(p => chip('party','party',p,p)).join('')}</span></div>
    <div class="frow"><span class="flabel">${tr('uf')}</span>${fi(tr('ufTip'))}<span class="fchips" id="f-ufs">${
      facets.ufs.map(u => chip('uf','uf',u,u)).join('')}</span></div>
    <div class="frow">
      <span class="flabel">${tr('wealth')}</span>${fi(tr('wealthTip'))}
      <input id="f-wmin" class="fnum" type="number" inputmode="numeric" placeholder="${tr('minMoney')}">
      <input id="f-wmax" class="fnum" type="number" inputmode="numeric" placeholder="${tr('maxMoney')}">
      <label class="fcheck"><input id="f-unknown" type="checkbox" checked> ${tr('includeUnknown')}</label>
    </div>
    <div class="frow">
      <span class="flabel">${tr('progressivePct')}</span>${fi(tr('progressivePctTip'))}
      <input id="f-opmin" class="fnum" type="number" inputmode="numeric" min="0" max="100" placeholder="mín %">
      <input id="f-opmax" class="fnum" type="number" inputmode="numeric" min="0" max="100" placeholder="máx %">
      <span class="muted" style="font-size:12px">${tr('progressiveScale')}</span>
    </div>
    <div class="frow">
      <span class="flabel">${tr('vote')}</span>${fi(tr('voteFilterTip'))}
      <select id="f-law" class="fsel">${opts(facets.laws, tr('anyLaw'))}</select>
      <select id="f-vote" class="fsel">
        <option value="">${tr('anyVote')}</option>
        <option value="SIM">${tr('votedYes')}</option>
        <option value="NAO">${tr('votedNo')}</option>
        <option value="AUSENTE">AUSENTE</option>
      </select>
      <span class="flabel">${tr('govMin')}</span>${fi(tr('govMinTip'))}
      <input id="f-gov" class="fnum" type="number" inputmode="numeric" placeholder="0–100">
      <button id="f-clear" type="button" class="secondary">${tr('clearFilters')}</button>
    </div>
  </div>`;
}

function initLanguageToggle(){
  applyStaticTranslations();
  const btn = el('lang-toggle');
  if(!btn) return;
  const render = () => {
    btn.textContent = tr('langToggle');
    btn.title = tr('langTitle');
    btn.setAttribute('aria-label', tr('langTitle'));
  };
  render();
  btn.addEventListener('click', () => {
    setLang(currentLang() === 'en' ? 'pt' : 'en');
    window.location.reload();
  });
}

// Wire the sun/moon toggle. The button (#theme-toggle) starts empty; we inject the icons
// here so both pages share one copy of the SVGs. Pre-paint theme selection lives inline
// in each page's <head> to avoid a flash of the wrong theme.
function initThemeToggle(){
  const root = document.documentElement;
  const btn = el('theme-toggle');
  if(!btn) return;
  btn.innerHTML = `
    <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="4"></circle>
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"></path>
    </svg>
    <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
    </svg>`;
  btn.addEventListener('click', () => {
    const dark = root.getAttribute('data-theme') === 'dark';
    const next = dark ? 'light' : 'dark';
    if(next === 'dark') root.setAttribute('data-theme', 'dark');
    else root.removeAttribute('data-theme');
    try{ localStorage.setItem('theme', next); }catch(e){}
  });
}
