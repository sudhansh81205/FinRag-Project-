const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const state = { filings: [], health: null, mode: 'auto', result: null, busy: false, token: null, lastQuery: null };
const element = (tag, text, cls) => { const node = document.createElement(tag); if (text !== undefined) node.textContent = text; if (cls) node.className = cls; return node; };
let toastTimer;
let savedRevision = 0;
let chartsLoaded = false;
const canonicalAccession = '0000320193-21-000105';
function closeMenu(restoreFocus = false) {
  const wasOpen = $('.sidebar').classList.contains('open');
  $('.sidebar').classList.remove('open');$('#menu-backdrop').hidden = true;
  $('.workspace').inert = false;$('#mobile-menu').setAttribute('aria-expanded', 'false');
  $('.sidebar').removeAttribute('role');$('.sidebar').removeAttribute('aria-modal');
  if (wasOpen && restoreFocus) $('#mobile-menu').focus();
}
function openMenu() {
  $('.sidebar').classList.add('open');$('#menu-backdrop').hidden = false;
  $('.workspace').inert = true;$('#mobile-menu').setAttribute('aria-expanded', 'true');
  $('.sidebar').setAttribute('role', 'dialog');$('.sidebar').setAttribute('aria-modal', 'true');
  $('#close-menu').focus();
}
function availableFiling(accession) {
  const connected = state.health?.runtime.supported_filings;
  return Array.isArray(connected) ? connected.includes(accession) : accession === canonicalAccession;
}
function updateAvailability() {
  const supported = availableFiling($('#filing').value);
  const ready = state.health?.runtime.status === 'ready';
  $('#selection-note').textContent = !supported ? 'This filing is in the inventory. Accepted evidence is not connected yet.' : ready ? 'This filing is connected. Each answer still needs matching source evidence.' : 'The financial engine is unavailable. Check the connection to continue.';
  $('#ask').disabled = state.busy || !supported || !ready || !state.filings.length;
  const chartReady = state.health?.runtime.modes?.chart === true;
  $('[data-mode="chart"]').disabled = state.busy || !chartReady;
  $('#chart-availability').hidden = chartReady;
  if (!chartReady && state.mode === 'chart') setMode('auto');
  const cloudReady = state.health?.saved_queries.sign_in_configured === true;
  $('#save-question').disabled = !cloudReady;
  $('#save-question').title = cloudReady ? 'Save this question privately' : 'Private saving is unavailable until sign-in setup is verified.';
}
function toast(text) { $('#toast').textContent = text; $('#toast').hidden = false;clearTimeout(toastTimer);toastTimer = setTimeout(() => { $('#toast').hidden = true; }, 4000); }
async function api(route, options = {}) {
  const response = await fetch(`/api/${route}`, { ...options, headers: { ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...(state.token ? { Authorization: `Bearer ${state.token}` } : {}), ...options.headers }, signal: options.signal || AbortSignal.timeout(route === 'answer' ? state.health?.answer_timeout_ms || 250000 : 28000) });
  const data = await response.json();
  return data;
}
function view(name) {
  if (!['research', 'library', 'saved', 'method', 'system'].includes(name)) return;
  $$('.view').forEach(node => { node.hidden = node.id !== `view-${name}`;node.classList.toggle('active', !node.hidden); });
  $$('.nav-item').forEach(node => { node.classList.toggle('active', node.dataset.view === name);if (node.dataset.view === name) node.setAttribute('aria-current', 'page');else node.removeAttribute('aria-current'); });
  $('#view-label').textContent = { research: 'Research', library: 'Filings', saved: 'Saved Questions', method: 'How it works', system: 'Connection and coverage' }[name];
  closeMenu();
  if (name === 'saved') renderSaved();
  if (name === 'method') renderChartSources();
  window.scrollTo({ top: 0, behavior: 'instant' });
  $('#main').focus({ preventScroll: true });
}
function setMode(mode) { state.mode = mode;$$('.mode').forEach(node => { const active = node.dataset.mode === mode;node.classList.toggle('active', active);node.setAttribute('aria-pressed', String(active)); }); }
function updateCount() { $('#char-count').textContent = `${$('#question').value.length.toLocaleString()} / 2,000`; }
function updateFilings() {
  const selected = state.filings.filter(f => f.ticker === $('#company').value);
  $('#filing').replaceChildren(...selected.map(f => { const option = element('option', `FY${f.period_end.slice(0, 4)} · ${f.form}`);option.value = f.accession;return option; }));
  updatePeriod();
}
function updatePeriod() { const filing = state.filings.find(f => f.accession === $('#filing').value);if (filing) { $('#period').value = filing.period_end;$('#period').max = filing.period_end;
  const name = filing.issuer.replace(/ Inc\.| Corporation/g, '');const year = filing.period_end.slice(0, 4);
  const labels = { margin: `What was ${name}’s gross margin in FY${year}?`, risk: `What risks does ${name} describe?`, revenue: `How much revenue did ${name} report in FY${year}?` };
  $$('[data-example]').forEach(button => { button.lastElementChild.textContent = labels[button.dataset.example]; });
}updateAvailability(); }
function query() { return { question: $('#question').value.trim(), ticker: $('#company').value, accession: $('#filing').value, value_period_end: $('#period').value, period_kind: $('#period-kind').value, scope: 'consolidated', mode: state.mode }; }
function loadQuery(value) {
  if (state.busy) { toast('Wait for the current research request to finish.');return; }
  invalidateResult();
  $('#company').value = value.ticker;updateFilings();$('#filing').value = value.accession;updatePeriod();$('#period').value = value.value_period_end;$('#period-kind').value = value.period_kind || 'duration';$('#question').value = value.question;setMode(value.mode || 'auto');updateCount();view('research');$('#question').focus();
}
function safeSource(raw) { try { const url = new URL(raw);return url.protocol === 'https:' && !url.username && !url.password && ['www.sec.gov', 'www.annualreports.com', 'annualreports.com', 'dd7pmep5szm19.cloudfront.net'].includes(url.hostname) ? url.href : null; } catch { return null; } }
function sourceLink(raw, label = 'Open original filing ↗') { const url = safeSource(raw);if (!url) return element('span', 'Source link unavailable', 'mono muted');const link = element('a', label);link.href = url;link.target = '_blank';link.rel = 'noopener noreferrer';return link; }
function evidenceLink(index, label) {
  const link = element('a', label);link.href = `#evidence-${index}`;
  link.addEventListener('click', event => {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();const target = $(`#evidence-${index}`);if (!target) return;
    target.open = true;target.querySelector('summary').focus({ preventScroll: true });
    target.scrollIntoView({ block: matchMedia('(min-width: 1200px)').matches ? 'nearest' : 'start', behavior: reduced ? 'instant' : 'smooth' });
    history.replaceState(null, '', link.hash);
  });
  return link;
}
async function renderChartSources() {
  if (chartsLoaded) return;
  const body = $('#chart-review-body');
  try {
    const response = await fetch('/review/charts.json', { signal: AbortSignal.timeout(15000) });
    if (!response.ok) throw new Error();
    const packet = await response.json();
    if (packet.status !== 'candidate_only' || packet.answering_enabled !== false || !Array.isArray(packet.charts)) throw new Error();
    body.replaceChildren();
    packet.charts.forEach(chart => {
      const article = element('article', undefined, 'chart-source');
      article.append(element('h3', `${chart.ticker} · Original chart`), element('p', '○ Independent review pending', 'supporting'), sourceLink(`${chart.source_url}#page=${chart.page}`, `Open original report · page ${chart.page} ↗`));
      if (/^\/review\/[a-f0-9]{64}\.(png|jpg|jpeg|gif)$/.test(chart.image)) {
        const link = element('a');link.href = chart.image;link.target = '_blank';link.rel = 'noopener noreferrer';link.setAttribute('aria-label', `Open full-size original ${chart.ticker} chart`);
        const image = element('img');image.src = chart.image;image.alt = `Original ${chart.ticker} chart, ${chart.description.title || 'title unknown'}`;image.loading = 'lazy';link.append(image);article.append(link);
      }
      article.append(element('p', 'Generated description with author corrections · acceptance pending', 'supporting'));
      const description = chart.description;
      article.append(table(['Chart detail', 'Source description'], [['Title', description.title], ['Type', description.chart_type], ['Horizontal axis', description.x_axis], ['Vertical axis', description.y_axis], ['Units', description.units], ['Series', description.series.join(', ')], ['Printed point values', description.readable_values.length ? JSON.stringify(description.readable_values) : 'Unknown · exact point values are not printed']]));
      const unknowns = element('ul');description.unknowns.forEach(note => unknowns.append(element('li', note)));article.append(unknowns);
      const questions = element('details');questions.append(element('summary', `${chart.questions.length} candidate questions and proposed labels · review only`), element('p', 'These labels are not independently approved. Held-out cases must not be used for tuning.'));
      questions.append(table(['Question / split', 'Proposed label', 'Source basis'], chart.questions.map(question => [`${question.question} (${question.split})`, question.answer, question.answer_basis])));article.append(questions);body.append(article);
    });
    chartsLoaded = true;
  } catch { body.replaceChildren(element('p', 'Chart inspection files are unavailable. Check the connection and reopen this section.')); }
}
function renderLibrary() {
  const needle = $('#filing-search').value.toLowerCase();const matched = state.filings.filter(f => `${f.issuer} ${f.ticker} ${f.accession} ${f.period_end}`.toLowerCase().includes(needle));
  $('#library-count').textContent = `${matched.length} FILINGS`;
  $('#filing-grid').replaceChildren(...matched.map((f, index) => {
  const card = element('article', undefined, 'filing-card');card.append(element('span', f.ticker, 'eyebrow'), element('h2', f.issuer), element('div', `FY${f.period_end.slice(0, 4)} · ${f.form}\n${f.accession}`, 'filing-meta'), element('span', availableFiling(f.accession) ? '✓ Available for bounded research' : '○ Inventory only · acceptance pending', 'inventory-tag'));
    const actions = element('div', undefined, 'filing-actions');const use = element('button', availableFiling(f.accession) ? 'Research this filing' : 'Research unavailable');use.disabled = !availableFiling(f.accession);use.title = availableFiling(f.accession) ? '' : 'Accepted evidence is not connected for this filing.';use.addEventListener('click', () => loadQuery({ ...f, value_period_end: f.period_end, question: '' }));actions.append(sourceLink(f.source_url, 'Open original filing ↗'), use);card.append(actions);return card;
  }));
}
function metricName(record) {
  const meta = record.metadata || {};
  if (meta.type === 'table_cell' && Array.isArray(meta.row_headers) && meta.row_headers.length) return meta.row_headers.join(' / ');
  if (meta.type === 'chart_description' && record.description?.title) return record.description.title;
  return (meta.metric || meta.section || meta.type || 'Source passage').replace(/^.*:/, '').replace(/([a-z])([A-Z])/g, '$1 $2');
}
function table(headers, rows, numericColumns = [1]) {
  const scroll = element('div', undefined, 'table-scroll');scroll.tabIndex = 0;scroll.setAttribute('role', 'region');scroll.setAttribute('aria-label', headers.join(', '));
  const table = element('table');const head = element('thead');const tr = element('tr');
  headers.forEach((title, index) => { const th = element('th', title, numericColumns.includes(index) ? 'numeric' : '');th.scope = 'col';tr.append(th); });head.append(tr);table.append(head);
  const body = element('tbody');rows.forEach(values => { const row = element('tr');values.forEach((value, index) => row.append(element('td', String(value ?? 'Unknown'), numericColumns.includes(index) ? 'numeric' : '')));body.append(row); });table.append(body);scroll.append(table);return scroll;
}
function renderCalculation(calc, records) {
  const box = element('section', undefined, 'calculation');box.append(element('h3', 'Checked calculation'));
  const expression = calc.expression || '';
  const referenced = new Set();
  function visit(value) { if (!value || typeof value !== 'object') return;if (typeof value.evidence_id === 'string') referenced.add(value.evidence_id);Object.values(value).forEach(item => Array.isArray(item) ? item.forEach(visit) : visit(item)); }
  visit(calc.program);
  const operands = records.filter(r => referenced.has(r.evidence_id || r.id) || expression.includes(r.evidence_id || r.id));
  if (operands.length) box.append(table(['Source value', 'Value', 'Unit / period'], operands.map(r => { const m = r.metadata || {};return [metricName(r), m.raw_value ?? m.normalized_value_decimal ?? m.normalized_value, `${m.raw_unit || m.unit || 'Unknown'} · ${m.period_end || 'Unknown'}`]; })));
  const named = operands.reduce((text, r) => text.split(r.evidence_id || r.id).join(metricName(r)), expression);
  box.append(element('p', named, 'calculation-expression'), element('p', `Result: ${calc.result ?? 'Unknown'} ${calc.unit || ''}`, 'calculation-result'));
  const details = element('details', undefined, 'technical-details');details.append(element('summary', 'Exact program and rule checks'), element('pre', JSON.stringify(calc, null, 2)));box.append(details);return box;
}
function renderEvidence(result) {
  const desk = $('#evidence-desk');desk.replaceChildren();
  desk.append(element('h2', 'The source work.'));desk.append(element('p', `${result.evidence.length} complete evidence objects included in this answer.`));
  result.evidence.forEach((record, index) => {
    const meta = record.metadata || {};const details = element('details', undefined, 'source-card');details.id = `evidence-${index + 1}`;details.open = index === 0;details.append(element('summary', `[${index + 1}] ${metricName(record)}`));
    details.append(element('div', `${record.evidence_id || record.id}\n${meta.period_end || ''} ${meta.currency || ''} ${meta.raw_unit || ''}`, 'source-meta'), element('p', record.content || ''), sourceLink(meta.source_url));desk.append(details);
    if (meta.type === 'chart_description') {
      const name = record.source?.asset?.split('/').at(-1);
      if (name && /^[a-f0-9]{64}\.(png|jpg|jpeg|gif)$/.test(name) && name.startsWith(meta.image_sha256)) {
        const image = element('img');image.src = `/review/${name}`;image.alt = `Original chart for source ${index + 1}`;details.append(image, sourceLink(record.source.pdf_url, `Original report · page ${record.source.page} ↗`));
      }
      if (record.description?.unknowns?.length) details.append(element('p', `Unknown values: ${record.description.unknowns.join(' ')}`));
    }
  });
}
function renderAnswer(result) {
  const body = $('#answer-body');body.replaceChildren();const card = element('div', undefined, 'answer-card result-enter');
  const messages = { ok: ['✓ Answer grounded in sources', 'Answer'], index_not_ready: ['○ Setup required', 'This source is not ready.'], insufficient_evidence: ['○ Insufficient evidence', 'A verified answer could not be constructed.'], invalid_request: ['! Check your question', 'Review the selected filing and period.'], service_error: ['! Service unavailable', 'The research service could not finish.'] };
  const labels = messages[result.status] || messages.service_error;
  card.append(element('span', labels[0], 'result-state'));
  if (state.lastQuery) { const filing = state.filings.find(f => f.accession === state.lastQuery.accession);card.append(element('div', `${filing?.issuer || state.lastQuery.ticker} · FY${filing?.period_end?.slice(0, 4) || ''} · Value period ${state.lastQuery.value_period_end}`, 'answer-context')); }
  if (result.status === 'ok' && state.lastQuery) card.append(element('h2', state.lastQuery.question));
  if (result.status !== 'ok') card.append(element('h2', labels[1]));
  const checkedValue = result.status === 'ok' && result.calculations?.length ? result.answer.match(/^Verified result: (.+?)\. Exact result:/)?.[1] : null;
  const content = element('div', result.status === 'ok' ? result.answer : result.message, 'answer-content');
  if (result.status === 'ok') {
    content.replaceChildren();
    result.answer.split(/\n\s*\n/).forEach(block => {
      if (/^#{1,4}\s+Direct Answer:?\s*$/i.test(block.trim())) return;
      const paragraph = element(/^#{1,4}\s/.test(block) ? 'h3' : 'p');
      let parts = [{ text: block.replace(/^#{1,4}\s+/, '') }];
      [...result.evidence].sort((a, b) => (b.evidence_id || b.id).length - (a.evidence_id || a.id).length).forEach(record => {
      const id = record.evidence_id || record.id;const index = result.evidence.indexOf(record) + 1;
      parts = parts.flatMap(part => { if (part.index) return [part];const split = part.text.split(id);return split.flatMap((text, i) => i ? [{ index }, { text }] : [{ text }]); });
      });
      parts.forEach(part => { if (part.index) paragraph.append(evidenceLink(part.index, `Source ${part.index}`));else paragraph.append(document.createTextNode(part.text)); });content.append(paragraph);
    });
  }
  card.append(content);
  if (checkedValue) {
    const displayValue = checkedValue.replace(/^(-?\d+)(.*)$/, (_match, integer, rest) => integer.replace(/\B(?=(\d{3})+(?!\d))/g, ',') + rest);
    content.replaceChildren(element('div', displayValue, 'answer-value'), element('p', 'Calculated from the cited filing values.'));
    const exact = element('details', undefined, 'technical-details');exact.append(element('summary', 'Exact answer and source identifiers'), element('pre', result.answer));content.append(exact);
  }
  if (result.status === 'ok') {
    const sources = element('div', undefined, 'answer-sources');sources.append(element('h3', 'Supporting sources'));const list = element('ul', undefined, 'citation-list');
    result.evidence.forEach((record, index) => { const li = element('li');li.append(evidenceLink(index + 1, `[${index + 1}] ${metricName(record)}`));list.append(li); });sources.append(list);card.append(sources);
    (result.calculations || []).forEach(calc => card.append(renderCalculation(calc, result.evidence)));
  } else {
    const next = element('button', result.status === 'service_error' || result.status === 'index_not_ready' ? 'Check connection and coverage' : 'Edit question', 'outline-button');next.addEventListener('click', () => result.status === 'service_error' || result.status === 'index_not_ready' ? view('system') : $('#question').focus());card.append(next);
  }
  body.append(card);$('#answer-section').hidden = false;
  $('#copy-answer').hidden = result.status !== 'ok';$('#export-answer').hidden = !result;$('#save-question').hidden = false;
  if (result.status === 'ok') renderEvidence(result);
  updateAvailability();
}
function clearEvidence() { const desk = $('#evidence-desk');desk.replaceChildren(element('h2', 'A clean evidence desk.'), element('p', 'Included source passages and checked calculations will appear after a successful, grounded answer.')); }
function invalidateResult() {
  state.result = null;state.lastQuery = null;$('#answer-section').hidden = true;
  $('#copy-answer').hidden = true;$('#export-answer').hidden = true;$('#save-question').hidden = true;clearEvidence();
}
function lockRequest(locked) {
  $$('#question, #company, #filing, #period, #period-kind, .mode, [data-example], .filing-actions button').forEach(control => { control.disabled = locked; });
  if (!locked) { updateAvailability();renderLibrary(); }
}
async function answerQuery(value) {
  if (!state.health?.runtime.jobs_supported) return api('answer', { method: 'POST', body: JSON.stringify(value) });
  const job = await api('jobs', { method: 'POST', body: JSON.stringify(value) });
  if (job.status !== 'queued') return job;
  const deadline = Date.now() + 900000;
  let failures = 0;
  while (Date.now() < deadline) {
    await new Promise(resolve => setTimeout(resolve, Math.min(8000, 1500 * (failures + 1))));
    let result;
    try { result = await api('jobs/poll', { method: 'POST', body: JSON.stringify({ ...value, job_id: job.job_id }) }); }
    catch { result = { status: 'service_error', retryable: true, answer: '', evidence: [], calculations: [], message: 'The answer job connection was interrupted.' }; }
    if (result.retryable === true && ++failures < 5) continue;
    failures = 0;
    if (!['queued', 'running'].includes(result.status)) return result;
    const label = $('#answer-body .result-state');
    if (label) label.textContent = result.status === 'queued' ? 'Queued · waiting for the model' : 'Running · researching the filing';
  }
  return { status: 'service_error', answer: '', evidence: [], calculations: [], message: 'The answer job expired. Submit the question again.' };
}
async function investigate() {
  if (state.busy) return;
  if ($('#ask').disabled) { toast($('#selection-note').textContent);return; }
  if ($('#question').value.trim().length < 3) { $('#question').focus();toast('Enter a financial question first.');return; }
  state.busy = true;state.result = null;state.lastQuery = query();lockRequest(true);$('#ask').disabled = true;$('#ask').firstElementChild.textContent = 'Asking FinRAG…';clearEvidence();$('#answer-section').hidden = false;$('#copy-answer').hidden = true;$('#export-answer').hidden = true;$('#save-question').hidden = true;$('#answer-section').setAttribute('aria-busy', 'true');
  const loading = element('div', undefined, 'answer-card');loading.append(element('span', 'Request submitted', 'result-state'), element('p', 'Waiting for the research service…', 'loading-indicator'));$('#answer-body').replaceChildren(loading);
  try { state.result = await answerQuery(state.lastQuery);if (!state.result.status) throw new Error(); }
  catch { state.result = { status: 'service_error', answer: '', evidence: [], calculations: [], message: 'The service could not be reached. Please try again.' }; }
  finally { state.busy = false;lockRequest(false);$('#ask').firstElementChild.textContent = 'Ask FinRAG';$('#answer-section').setAttribute('aria-busy', 'false');renderAnswer(state.result);if (state.result.status === 'service_error') refreshHealth(); }
}
function systemRow(title, message, status) { const row = element('article', undefined, 'system-row');const text = element('div');text.append(element('h2', title), element('p', message));row.append(text, element('span', status));return row; }
function renderSystem() {
  const health = state.health;const body = $('#system-body');body.replaceChildren();
  if (!health) { body.append(systemRow('Connection check', 'The status endpoint could not be reached.', 'UNAVAILABLE'));return; }
  body.append(systemRow('Financial engine', health.runtime.message || 'The configured backend reports readiness. Individual answer evidence is validated separately.', health.runtime.status === 'ready' ? 'CONNECTED' : 'SETUP REQUIRED'), systemRow('Saved questions', health.saved_queries.configured ? 'Private row-level access is configured. Email sign-in requires separate redirect and delivery verification.' : 'Connect a Supabase project and apply the saved-query schema to enable this feature.', health.saved_queries.configured ? 'SUPABASE CONFIGURED' : 'NOT CONFIGURED'), systemRow('Filing coverage', `${health.corpus.inventory} inventory entries across ${health.corpus.companies} companies. ${(health.runtime.supported_filings || []).length} connected for source-checked research. Independent final-study acceptance remains separate.`, 'PARTIAL'), systemRow('Experiment acceptance', 'Full A–G benchmark runs, the independent fifty-output audit and RAGAS results remain pending. Candidate chart integrity is separate from independent label approval.', 'NOT COMPLETE'));
}
async function refreshHealth() {
  try { state.health = await api('health');if (!state.health.runtime) throw new Error();const ready = state.health.runtime.status === 'ready';$('#health-pill').classList.toggle('ready', ready);$('#health-pill span').textContent = ready ? 'Engine connected' : 'Engine setup required'; }
  catch { state.health = null;$('#health-pill span').textContent = 'Connection unavailable'; }
  renderSystem();
  updateAvailability();
}
function showAuth() {
  $('#auth-message').textContent = state.health?.saved_queries.sign_in_configured ? '' : state.health?.saved_queries.configured ? 'Email sign-in is pending redirect and delivery verification. Research remains available without an account.' : 'Private saving is not connected. You can still ask questions and inspect filing evidence without signing in.';
  $('#auth-submit').disabled = !state.health?.saved_queries.sign_in_configured;$('#auth-signup').disabled = $('#auth-submit').disabled;$('#auth-verify').disabled = $('#auth-submit').disabled;$('#sign-out').hidden = !state.token;$('#auth-dialog').showModal();
}
async function renderSaved() {
  const revision = ++savedRevision;const token = state.token;
  const body = $('#saved-body');body.replaceChildren();
  if (!state.token || !state.health?.saved_queries.configured) { const box = element('div', undefined, 'saved-empty');box.append(element('h2', state.health?.saved_queries.sign_in_configured ? 'Your questions, in one place.' : 'Private saving is unavailable.'), element('p', state.health?.saved_queries.sign_in_configured ? 'Sign in with your account to see and save your private questions.' : 'Sign-in setup needs to be completed and verified. You can continue research and export answers without an account.'));const button = element('button', state.health?.saved_queries.sign_in_configured ? 'Sign in to your workspace' : 'Sign-in unavailable', 'outline-button');button.disabled = !state.health?.saved_queries.sign_in_configured;button.addEventListener('click', showAuth);const back = element('button', 'Back to research', 'text-button');back.addEventListener('click', () => view('research'));box.append(button, back);body.append(box);return; }
  body.append(element('p', 'Loading your saved questions…'));
  try {
    const result = await api('saved');if (revision !== savedRevision || token !== state.token) return;body.replaceChildren();
    if (result.status !== 'ok') { body.append(element('p', result.message || 'Saved questions could not be loaded.'));return; }
    if (!result.data.length) { body.append(element('p', 'No saved questions yet. Start a new research question and choose Save question.'));return; }
    result.data.forEach(item => { const row = element('article', undefined, 'saved-row');const open = element('button', item.question);open.append(element('small', `${item.request.ticker} · ${item.request.value_period_end} · ${new Date(item.created_at).toLocaleDateString()}`));open.addEventListener('click', () => loadQuery({ question: item.question, ...item.request }));const remove = element('button', 'Delete', 'text-button');remove.addEventListener('click', async () => { const r = await api(`saved?id=${encodeURIComponent(item.id)}`, { method: 'DELETE' });if (r.status === 'ok') renderSaved();else toast(r.message || 'Could not delete the question.'); });row.append(open, remove);body.append(row); });
  } catch { if (revision === savedRevision && token === state.token) body.replaceChildren(element('p', 'Your saved questions could not be reached.')); }
}
$$('[data-view]').forEach(button => button.addEventListener('click', () => view(button.dataset.view)));
$$('.mode').forEach(button => button.addEventListener('click', () => { invalidateResult();setMode(button.dataset.mode); }));
$('#company').addEventListener('change', () => { invalidateResult();updateFilings(); });$('#filing').addEventListener('change', () => { invalidateResult();updatePeriod(); });$('#period').addEventListener('change', invalidateResult);$('#filing-search').addEventListener('input', renderLibrary);$('#question').addEventListener('input', () => { invalidateResult();updateCount(); });$('#research-form').addEventListener('submit', event => { event.preventDefault();investigate(); });
$('#period-kind').addEventListener('change', invalidateResult);
$('#new-research').addEventListener('click', () => { if (state.busy) return;invalidateResult();view('research');$('#question').value = '';updateCount();$('#question').focus(); });
document.addEventListener('keydown', event => { if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') { event.preventDefault();investigate(); }if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault();view('research');$('#question').focus(); } });
$$('[data-example]').forEach(button => button.addEventListener('click', () => {
  const f = state.filings.find(f => f.accession === $('#filing').value);if (!f) return;
  const name = f.issuer.replace(/ Inc\.| Corporation/g, '');const year = f.period_end.slice(0, 4);
  const examples = { margin: [`What was ${name}'s gross margin in FY${year}?`, 'numerical'], risk: [`What risks does ${name} describe in its FY${year} annual report?`, 'narrative'], revenue: [`How much revenue did ${name} report in FY${year}?`, 'numerical'] };
  const [question, mode] = examples[button.dataset.example];loadQuery({ question, mode, ticker: f.ticker, accession: f.accession, value_period_end: f.period_end });
}));
$('#copy-answer').addEventListener('click', async () => { try { await navigator.clipboard.writeText(state.result?.answer || '');toast('Answer copied.'); } catch { toast('Clipboard access is unavailable.'); } });
$('#export-answer').addEventListener('click', () => { if (!state.result) return;const blob = new Blob([JSON.stringify({ query: state.lastQuery, result: state.result }, null, 2)], { type: 'application/json' });const url = URL.createObjectURL(blob);const link = element('a');link.href = url;link.download = 'finrag-research.json';link.click();setTimeout(() => URL.revokeObjectURL(url), 1000); });
$('#save-question').addEventListener('click', async () => { if (!state.token) { showAuth();return; }try { const result = await api('saved', { method: 'POST', body: JSON.stringify(state.lastQuery || query()) });toast(result.status === 'ok' ? 'Question saved privately.' : result.message || 'Could not save the question.'); } catch { toast('Could not reach saved questions.'); } });
$('#account-button').addEventListener('click', showAuth);$('#close-auth').addEventListener('click', () => $('#auth-dialog').close());$('#refresh-status').addEventListener('click', refreshHealth);
async function accountAction(route) {
  $('#auth-submit').disabled = true;$('#auth-signup').disabled = true;$('#auth-verify').disabled = true;
  try {
    const body = route === 'verify' ? {confirmation_url:$('#confirmation-link').value.trim()} : {email:$('#email').value.trim(),password:$('#password').value};
    const result = await api(`auth/${route}`, {method:'POST',body:JSON.stringify(body)});
    $('#auth-message').textContent = result.message || '';
    if (result.status === 'ok' && result.access_token) {
      state.token = result.access_token;sessionStorage.setItem('finrag_token',state.token);$('#password').value = '';$('#confirmation-link').value = '';
      $('#account-label').textContent = 'Signed-in workspace';$('#account-detail').textContent = 'Private saved questions';$('#auth-dialog').close();
      if (state.result) $('#save-question').disabled = false;renderSaved();toast('Signed in. Your saved questions are private.');
    }
  } catch { $('#auth-message').textContent = 'The account service could not be reached. Try again.'; }
  finally { $('#auth-submit').disabled = !state.health?.saved_queries.sign_in_configured;$('#auth-signup').disabled = $('#auth-submit').disabled;$('#auth-verify').disabled = $('#auth-submit').disabled; }
}
$('#auth-form').addEventListener('submit', event => {event.preventDefault();accountAction('password');});
$('#auth-signup').addEventListener('click', () => {if ($('#auth-form').reportValidity()) accountAction('signup');});
$('#auth-verify').addEventListener('click', () => accountAction('verify'));
$('#sign-out').addEventListener('click', () => { state.token = null;sessionStorage.removeItem('finrag_token');$('#account-label').textContent = 'Your workspace';$('#account-detail').textContent = 'Sign in to save questions';$('#auth-dialog').close();renderSaved();toast('Signed out of this browser.'); });
$('#mobile-menu').addEventListener('click', openMenu);$('#close-menu').addEventListener('click', () => closeMenu(true));$('#menu-backdrop').addEventListener('click', () => closeMenu(true));
document.addEventListener('keydown', event => {
  if (!$('.sidebar').classList.contains('open')) return;
  if (event.key === 'Escape') { event.preventDefault();closeMenu(true); }
  if (event.key === 'Tab') {
    const controls = $$('.sidebar a[href], .sidebar button:not(:disabled)').filter(node => node.getClientRects().length);
    const first = controls[0], last = controls.at(-1);
    if (event.shiftKey && document.activeElement === first) { event.preventDefault();last.focus(); }
    if (!event.shiftKey && document.activeElement === last) { event.preventDefault();first.focus(); }
  }
});
matchMedia('(max-width: 767px)').addEventListener('change', () => closeMenu());
let reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
function setMotion() { document.body.classList.toggle('reduced-motion', reduced);$('#motion-toggle').textContent = reduced ? 'Motion off' : 'Motion on';$('#motion-toggle').setAttribute('aria-pressed', String(reduced)); }
$('#motion-toggle').addEventListener('click', () => { reduced = !reduced;setMotion(); });setMotion();
// Only session-scoped access tokens; refresh tokens never enter storage. The API verifies users.
try { const hash = new URLSearchParams(location.hash.slice(1));const token = hash.get('access_token');if (token && /^[A-Za-z0-9_.-]{20,4096}$/.test(token)) sessionStorage.setItem('finrag_token', token);if (hash.has('access_token') || hash.has('error')) history.replaceState(null, '', location.pathname);state.token = sessionStorage.getItem('finrag_token'); } catch { state.token = null; }
if (state.token) { $('#account-label').textContent = 'Signed-in workspace';$('#account-detail').textContent = 'Private saved questions'; }
async function start() {
  await refreshHealth();
  try { const data = await api('filings');if (!Array.isArray(data.filings)) throw new Error();state.filings = data.filings;const companies = [...new Map(state.filings.map(f => [f.ticker, f])).values()];$('#company').replaceChildren(...companies.map(f => { const o = element('option', f.issuer);o.value = f.ticker;return o; }));updateFilings();$('#nav-count').textContent = String(state.filings.length).padStart(2, '0');renderLibrary(); }
  catch { $('#ask').disabled = true;toast('The filing inventory could not be loaded. Please refresh.'); }
}
start();
