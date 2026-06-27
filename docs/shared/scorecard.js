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

function metricsHtml(card){
  const s = card.summary;
  // Senators have no TSE wealth ingested yet -> show '—' for wealth-derived metrics instead of a
  // misleading 0%. Gov/Oposição line isn't published on the Senado /votacao feed either.
  const senator = card.politic.house === 'senado';
  const metrics = [
    [senator ? '—' : pct(s.wealth_capital_pct), 'patrimônio em capital'],
    [pct(s.coverage_pct), 'cobertura de leis relevantes'],
    [pct(s.key_attendance_pct), 'presença no projeto-chave'],
    [senator || s.self_interest_alignment_pct === null ? '—' : pct(s.self_interest_alignment_pct), 'protege o próprio patrimônio'],
    [s.gov_alignment_pct === null || s.gov_alignment_pct === undefined ? '—' : pct(s.gov_alignment_pct), 'alinhado ao Governo'],
    [s.opp_alignment_pct === null || s.opp_alignment_pct === undefined ? '—' : pct(s.opp_alignment_pct), 'alinhado à Oposição']
  ];
  return `<section class="metrics">${
    metrics.map(([n,l]) => `<div class="metric"><div class="n">${n}</div><div class="l">${l}</div></div>`).join('')
  }</section>`;
}

function wealthHtml(card){
  const p = card.politic;
  if(p.house === 'senado'){
    return `<section class="panel"><h2>Patrimônio declarado</h2>
      <div class="note">Patrimônio (bens declarados ao TSE) ainda não coletado para senadores — o
      score do Senado usa apenas os votos nominais nas mesmas leis.</div></section>`;
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
      rows.push(`<tr>
        <td><b>${law.label}</b><br><span class="muted">${law.description}</span>
          <div class="keywords">${law.keywords.map(k => `<span class="keyword">${k.label}</span>`).join('')}</div></td>
        <td>${topic.title}${law.is_key ? '<br><span class="chip c-mix">chave</span>' : ''}</td>
        <td><span class="chip ${chipClass(score)}">${score?.vote_label || 'sem score'}</span></td>
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
