/* Shared scorecard rendering + theme toggle for both pages (live app + GitHub Pages).
   SOURCE OF TRUTH: candidatos/shared/. docs/shared/ is a generated copy — do not edit it.

   Exposes (as globals, no module system): BRL, COLORS, el, pct, slugify, chipClass,
   identityHtml, metricsHtml, wealthHtml, votesHtml, METHOD_HTML, initThemeToggle. */

const BRL = n => 'R$ ' + Number(n || 0).toLocaleString('pt-BR', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2
});
const COLORS = ['#0f766e', '#b45309', '#2563eb', '#7c3aed', '#be123c'];
const el = id => document.getElementById(id);
const pct = value => value === null || value === undefined ? '—' : `${value}%`;
const slugify = (name, id) => 'c-' + id + '-' + String(name || '').toLowerCase()
  .normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

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
      <div class="muted">${p.party || '—'} · ${p.uf || '—'} · ${p.occupation || 'ocupação não informada'}</div>
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
    [known ? pct(s.wealth_capital_pct) : '—', 'patrimônio em capital'],
    [pct(s.coverage_pct), 'cobertura de leis relevantes'],
    [pct(s.key_attendance_pct), 'presença no projeto-chave'],
    [!known || s.self_interest_alignment_pct === null ? '—' : pct(s.self_interest_alignment_pct), 'protege o próprio patrimônio'],
    [s.gov_alignment_pct === null || s.gov_alignment_pct === undefined ? '—' : pct(s.gov_alignment_pct), 'alinhado ao Governo'],
    [s.opp_alignment_pct === null || s.opp_alignment_pct === undefined ? '—' : pct(s.opp_alignment_pct), 'alinhado à Oposição']
  ];
  return `<section class="metrics">${
    metrics.map(([n,l]) => `<div class="metric"><div class="n">${n}</div><div class="l">${l}</div></div>`).join('')
  }</section>`;
}

function wealthHtml(card){
  const p = card.politic;
  if(!wealthKnown(p)){
    return `<section class="panel"><h2>Patrimônio declarado</h2>
      <div class="note"><b>Declaração de bens não disponível para este(a) parlamentar.</b><br>
      O patrimônio é puxado da base de candidaturas do TSE, que aqui só está mapeada para a eleição
      de <b>2022</b>. Senadores cumprem mandato de <b>8 anos escalonado</b>, então quem foi eleito
      em <b>2018</b> ainda não tem os bens coletados por esta fonte. Isso é uma <b>limitação da
      fonte de dados</b> — não significa que a pessoa não tenha patrimônio. O score baseado em
      votos nominais não é afetado.</div></section>`;
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
  return `<section class="panel"><h2>Patrimônio declarado</h2>
    <div class="wealth-grid">
      <div><div class="big">${BRL(p.wealth_total)}</div><div class="muted">${p.wealth_capital_pct}% em ações/participações ou exterior</div></div>
      <div>${rows || '<span class="muted">Sem bens armazenados.</span>'}</div>
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
        : `<span class="chip c-na" title="Esta lei foi adicionada depois deste scorecard — recalcule o candidato (Buscar) para avaliá-la. Não significa ausência.">não avaliado</span>`;
      rows.push(`<tr>
        <td><b>${law.label}</b><br><span class="muted">${law.description}</span>
          <div class="keywords">${law.keywords.map(k => `<span class="keyword">${k.label}</span>`).join('')}</div></td>
        <td>${topic.title}${law.is_key ? '<br><span class="chip c-mix">chave</span>' : ''}</td>
        <td>${voteCell}</td>
        <td>${score ? `${score.present_count}/${score.nominal_count}` : '—'}</td>
      </tr>`);
    }
  }
  return `<section class="panel"><h2>Leis, palavras-chave e votos armazenados</h2>
    <table><thead><tr><th>Lei</th><th>Tópico</th><th>Voto</th><th>Presença</th></tr></thead>
    <tbody>${rows.join('')}</tbody></table></section>`;
}

const METHOD_HTML = `<section class="panel">
  <h2>Como o score é calculado</h2>
  <p>Para cada palavra-chave associada a uma lei, a direção indica o que um voto <code>Sim</code>
  representa. <code>+1</code> significa avançar a tese, <code>-1</code> significa bloquear a tese,
  e <code>0</code> é contexto sem direção de riqueza.</p>
  <div class="note warn">Ausência continua sendo ausência: o banco guarda presença, cobertura e
  evidência separadamente para evitar transformar dado faltante em intenção.</div>
</section>`;

// Full scorecard body for one candidate (identity + metrics + wealth + votes + method).
function cardBodyHtml(card){
  return `<section class="panel">${identityHtml(card)}</section>`
    + metricsHtml(card) + wealthHtml(card) + votesHtml(card) + METHOD_HTML;
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
  const wealth = known ? BRL(c.wealth_total) : 'patrimônio —';
  const house = c.house === 'senado'
    ? '<span class="chip c-mix">Senado</span>'
    : '<span class="chip c-sim">Câmara</span>';
  const delay = i ? ` style="animation-delay:${Math.min(i, 14) * 28}ms"` : '';
  return `<button class="ccard" type="button" data-key="${candidateKey(c)}"${delay}>
    <span class="ccard-top"><span class="avatar avatar-sm">${(c.name || '?').slice(0, 1)}</span>${house}</span>
    <b class="ccard-name">${c.name}</b>
    <span class="muted ccard-meta">${c.party || '—'} · ${c.uf || '—'}</span>
    <span class="ccard-wealth${known ? '' : ' unknown'}">${wealth}</span>
  </button>`;
}

// The grid, or a friendly empty state.
function candidateGridHtml(list){
  if(!list.length){
    return `<div class="sub" style="margin-top:14px">Nenhum candidato no banco corresponde — use <b>Buscar</b> para procurar um nome novo (Câmara → Senado).</div>`;
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
function rosterEntry(card){
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
    return true;
  });
  const w = e => e.wealth_known ? e.wealth_total : null;
  if(f.sort === 'wealth-desc') out.sort((a,b) => (w(b) ?? -1) - (w(a) ?? -1));
  else if(f.sort === 'wealth-asc') out.sort((a,b) => (w(a) ?? Infinity) - (w(b) ?? Infinity));
  else out.sort((a,b) => a.name.localeCompare(b.name,'pt'));
  return out;
}

// Render the filter panel. State lives in the page shell; this only emits markup with stable ids.
function filterControlsHtml(facets){
  const chip = (cls, attr, val, label) => `<button type="button" class="fchip" data-${attr}="${val}">${label}</button>`;
  const opts = (arr, ph) => `<option value="">${ph}</option>` + arr.map(x => `<option value="${x}">${x}</option>`).join('');
  return `<div class="filters">
    <div class="frow">
      <input id="f-query" class="search-input" placeholder="Buscar por nome…" autocomplete="off">
      <span id="f-count" class="fcount"></span>
    </div>
    <div class="frow">
      <span class="flabel">Casa</span>
      <span class="fseg" id="f-house">
        <button type="button" data-house="all" class="on">Todas</button>
        <button type="button" data-house="camara">Câmara</button>
        <button type="button" data-house="senado">Senado</button>
      </span>
      <span class="flabel">Ordenar</span>
      <select id="f-sort" class="fsel">
        <option value="name">Nome (A→Z)</option>
        <option value="wealth-desc">Patrimônio (maior→menor)</option>
        <option value="wealth-asc">Patrimônio (menor→maior)</option>
      </select>
    </div>
    <div class="frow"><span class="flabel">Partido</span><span class="fchips" id="f-parties">${
      facets.parties.map(p => chip('party','party',p,p)).join('')}</span></div>
    <div class="frow"><span class="flabel">UF</span><span class="fchips" id="f-ufs">${
      facets.ufs.map(u => chip('uf','uf',u,u)).join('')}</span></div>
    <div class="frow">
      <span class="flabel">Patrimônio</span>
      <input id="f-wmin" class="fnum" type="number" inputmode="numeric" placeholder="mín R$">
      <input id="f-wmax" class="fnum" type="number" inputmode="numeric" placeholder="máx R$">
      <label class="fcheck"><input id="f-unknown" type="checkbox" checked> incluir desconhecido</label>
    </div>
    <div class="frow">
      <span class="flabel">Voto</span>
      <select id="f-law" class="fsel">${opts(facets.laws, 'qualquer lei')}</select>
      <select id="f-vote" class="fsel">
        <option value="">qualquer voto</option>
        <option value="SIM">votou SIM</option>
        <option value="NAO">votou NÃO</option>
        <option value="AUSENTE">AUSENTE</option>
      </select>
      <span class="flabel">Gov. mín %</span>
      <input id="f-gov" class="fnum" type="number" inputmode="numeric" placeholder="0–100">
      <button id="f-clear" type="button" class="secondary">Limpar filtros</button>
    </div>
  </div>`;
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
