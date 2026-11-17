const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const state = { filings: [], health: null, mode: 'auto', result: null, busy: false, token: null, lastQuery: null };
const element = (tag, text, cls) => { const node = document.createElement(tag); if (text !== undefined) node.textContent = text; if (cls) node.className = cls; return node; };
let toastTimer;
function toast(text) { $('#toast').textContent = text; $('#toast').hidden = false;clearTimeout(toastTimer);toastTimer = setTimeout(() => { $('#toast').hidden = true; }, 4000); }
async function api(route, options = {}) {
  const response = await fetch(`/api/${route}`, { ...options, headers: { ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...(state.token ? { Authorization: `Bearer ${state.token}` } : {}), ...options.headers }, signal: options.signal || AbortSignal.timeout(route === 'answer' ? state.health?.answer_timeout_ms || 250000 : 28000) });
  const data = await response.json();
  return data;
}
function view(name) {
  if (!['research', 'library', 'saved', 'method', 'system'].includes(name)) return;
  $$('.view').forEach(node => { node.hidden = node.id !== `view-${name}`;node.classList.toggle('active', !node.hidden); });
  $$('.nav-item').forEach(node => node.classList.toggle('active', node.dataset.view === name));
  $('#view-label').textContent = { research: 'RESEARCH', library: 'FILING LIBRARY', saved: 'SAVED QUESTIONS', method: 'THE APPROACH', system: 'SYSTEM STATUS' }[name];
  $('.sidebar').classList.remove('open');$('#mobile-menu').setAttribute('aria-expanded', 'false');
  if (name === 'saved') renderSaved();
  window.scrollTo({ top: 0, behavior: 'instant' });
}
function setMode(mode) { state.mode = mode;$$('.mode').forEach(node => { const active = node.dataset.mode === mode;node.classList.toggle('active', active);node.setAttribute('aria-pressed', String(active)); }); }
function updateCount() { $('#char-count').textContent = `${$('#question').value.length.toLocaleString()} / 2,000`; }
function updateFilings() {
  const selected = state.filings.filter(f => f.ticker === $('#company').value);
  $('#filing').replaceChildren(...selected.map(f => { const option = element('option', `FY${f.period_end.slice(0, 4)} · ${f.form}`);option.value = f.accession;return option; }));
  updatePeriod();
}
function updatePeriod() { const filing = state.filings.find(f => f.accession === $('#filing').value);if (filing) { $('#period').value = filing.period_end;$('#period').max = filing.period_end; } }
function query() { return { question: $('#question').value.trim(), ticker: $('#company').value, accession: $('#filing').value, value_period_end: $('#period').value, period_kind: $('#period-kind').value, scope: 'consolidated', mode: state.mode }; }
function loadQuery(value) {
  if (state.busy) { toast('Wait for the current research request to finish.');return; }
  invalidateResult();
  $('#company').value = value.ticker;updateFilings();$('#filing').value = value.accession;updatePeriod();$('#period').value = value.value_period_end;$('#period-kind').value = value.period_kind || 'duration';$('#question').value = value.question;setMode(value.mode || 'auto');updateCount();view('research');$('#question').focus();
}
function safeSource(raw) { try { const url = new URL(raw);return url.protocol === 'https:' && ['www.sec.gov', 'www.annualreports.com', 'annualreports.com'].includes(url.hostname) ? url.href : null; } catch { return null; } }
function sourceLink(raw, label = 'Open original filing ↗') { const url = safeSource(raw);if (!url) return element('span', 'Source link unavailable', 'mono muted');const link = element('a', label);link.href = url;link.target = '_blank';link.rel = 'noopener noreferrer';return link; }
function renderLibrary() {
  const needle = $('#filing-search').value.toLowerCase();const matched = state.filings.filter(f => `${f.issuer} ${f.ticker} ${f.accession} ${f.period_end}`.toLowerCase().includes(needle));
  $('#library-count').textContent = `${matched.length} FILINGS`;
  $('#filing-grid').replaceChildren(...matched.map((f, index) => {
    const card = element('article', undefined, 'filing-card');card.append(element('span', `[ ${String(index + 1).padStart(2, '0')} ]  /  ${f.ticker}`, 'eyebrow'), element('h2', f.issuer), element('div', `FY${f.period_end.slice(0, 4)} · ${f.form}\n${f.accession}`, 'filing-meta'), element('span', f.accession === '0000320193-21-000105' ? 'BOUNDED CANONICAL PACKAGE ACCEPTED' : 'INVENTORY · ACCEPTANCE PENDING', 'inventory-tag'));
    const actions = element('div', undefined, 'filing-actions');const use = element('button', 'Research this filing ↗');use.addEventListener('click', () => loadQuery({ ...f, value_period_end: f.period_end, question: '' }));actions.append(sourceLink(f.source_url, 'SEC source ↗'), use);card.append(actions);return card;
  }));
}
function renderEvidence(result) {
  const desk = $('#evidence-desk');desk.replaceChildren();
  desk.append(element('h2', 'The source work.'));desk.append(element('p', `${result.evidence.length} complete evidence objects included in this answer.`));
  result.evidence.forEach((record, index) => {
    const meta = record.metadata || {};const details = element('details', undefined, 'source-card');details.open = index === 0;details.append(element('summary', `[ ${String(index + 1).padStart(2, '0')} ] ${meta.metric || meta.section || meta.type || 'Source passage'}`));
    details.append(element('div', `${record.evidence_id || record.id}\n${meta.period_end || ''} ${meta.currency || ''} ${meta.raw_unit || ''}`, 'source-meta'), element('p', record.content || ''), sourceLink(meta.source_url));desk.append(details);
  });
  (result.calculations || []).forEach(calc => { const box = element('div', undefined, 'calculation');box.append(element('b', 'CHECKED CALCULATION'), element('p', `${calc.expression || ''}\n${calc.result || ''} ${calc.unit || ''}`));desk.append(box); });
}
function renderAnswer(result) {
  const body = $('#answer-body');body.replaceChildren();const card = element('div', undefined, 'answer-card');
  card.append(element('span', result.status.replaceAll('_', ' '), 'result-state'));
  card.append(element('h2', result.status === 'ok' ? 'A finding you can inspect.' : result.status === 'index_not_ready' ? 'The engine needs its sources.' : result.status === 'insufficient_evidence' ? 'The evidence is not enough.' : result.status === 'invalid_request' ? 'Let’s refine the question.' : 'The service is unavailable.'));
  card.append(element('p', result.status === 'ok' ? result.answer : result.message));
  if (result.status !== 'ok') card.append(element('p', 'No unsupported financial answer has been substituted.', 'muted'));
  body.append(card);$('#answer-section').hidden = false;
  $('#copy-answer').hidden = result.status !== 'ok';$('#export-answer').hidden = !result;$('#save-question').hidden = false;
  if (result.status === 'ok') renderEvidence(result);
}
function clearEvidence() { const desk = $('#evidence-desk');desk.replaceChildren(element('h2', 'A clean evidence desk.'), element('p', 'Included source passages and checked calculations will appear after a successful, grounded answer.')); }
function invalidateResult() {
  state.result = null;state.lastQuery = null;$('#answer-section').hidden = true;
  $('#copy-answer').hidden = true;$('#export-answer').hidden = true;$('#save-question').hidden = true;clearEvidence();
}
function lockRequest(locked) {
  $$('#question, #company, #filing, #period, #period-kind, .mode, [data-example], .filing-actions button').forEach(control => { control.disabled = locked; });
}
async function investigate() {
  if (state.busy) return;
  if ($('#question').value.trim().length < 3) { $('#question').focus();toast('Enter a financial question first.');return; }
  state.busy = true;state.result = null;state.lastQuery = query();lockRequest(true);$('#ask').disabled = true;$('#ask').firstElementChild.textContent = 'Investigating';clearEvidence();$('#answer-section').hidden = false;$('#copy-answer').hidden = true;$('#export-answer').hidden = true;$('#save-question').hidden = true;
  const loading = element('div', undefined, 'answer-card');loading.append(element('span', 'CHECKING SOURCE AVAILABILITY', 'result-state'), element('h2', 'Following the paper trail…'), element('div', undefined, 'progress-line'));$('#answer-body').replaceChildren(loading);
  try { state.result = await api('answer', { method: 'POST', body: JSON.stringify(state.lastQuery) });if (!state.result.status) throw new Error(); }
  catch { state.result = { status: 'service_error', answer: '', evidence: [], calculations: [], message: 'The service could not be reached. Please try again.' }; }
  finally { state.busy = false;lockRequest(false);$('#ask').disabled = false;$('#ask').firstElementChild.textContent = 'Investigate';renderAnswer(state.result); }
}
function systemRow(title, message, status) { const row = element('article', undefined, 'system-row');const text = element('div');text.append(element('h2', title), element('p', message));row.append(text, element('span', status));return row; }
function renderSystem() {
  const health = state.health;const body = $('#system-body');body.replaceChildren();
  if (!health) { body.append(systemRow('Connection check', 'The status endpoint could not be reached.', 'UNAVAILABLE'));return; }
  body.append(systemRow('Financial engine', health.runtime.message || 'The configured backend reports readiness. Individual answer evidence is validated separately.', health.runtime.status === 'ready' ? 'CONNECTED' : 'SETUP REQUIRED'), systemRow('Saved questions', health.saved_queries.configured ? 'Private row-level access is configured. Email sign-in requires separate redirect and delivery verification.' : 'Connect a Supabase project and apply the saved-query schema to enable this feature.', health.saved_queries.configured ? 'SUPABASE CONFIGURED' : 'NOT CONFIGURED'), systemRow('Filing coverage', `${health.corpus.inventory} inventory entries across ${health.corpus.companies} companies. One bounded canonical filing is previously accepted; wider acceptance and full indexed coverage remain open.`, 'PARTIAL'), systemRow('Experiment acceptance', 'Full A–G benchmark runs, the independent fifty-output audit and RAGAS results remain pending. Candidate chart integrity is separate from independent label approval.', 'NOT COMPLETE'));
}
async function refreshHealth() {
  try { state.health = await api('health');if (!state.health.runtime) throw new Error();const ready = state.health.runtime.status === 'ready';$('#health-pill').classList.toggle('ready', ready);$('#health-pill span').textContent = ready ? 'Engine connected' : 'Engine setup required'; }
  catch { state.health = null;$('#health-pill span').textContent = 'Connection unavailable'; }
  renderSystem();
}
function showAuth() {
  $('#auth-message').textContent = state.health?.saved_queries.sign_in_configured ? '' : state.health?.saved_queries.configured ? 'Your database is connected. Email sign-in is pending redirect and delivery verification.' : 'Supabase is not configured yet. You can still explore filings and prepare questions.';
  $('#auth-submit').disabled = !state.health?.saved_queries.sign_in_configured;$('#sign-out').hidden = !state.token;$('#auth-dialog').showModal();
}
async function renderSaved() {
  const body = $('#saved-body');body.replaceChildren();
  if (!state.token || !state.health?.saved_queries.configured) { const box = element('div', undefined, 'saved-empty');box.append(element('h2', state.health?.saved_queries.configured ? 'Your questions, in one place.' : 'A place for your next insight.'), element('p', state.health?.saved_queries.configured ? 'Sign in with an email link to see and save your private questions.' : 'Cloud saving is not connected yet. This workspace will show that clearly until your Supabase database is ready.'));const button = element('button', 'Sign in to your workspace ↗', 'outline-button');button.addEventListener('click', showAuth);box.append(button);body.append(box);return; }
  body.append(element('p', 'Loading your saved questions…'));
  try {
    const result = await api('saved');body.replaceChildren();
    if (result.status !== 'ok') { body.append(element('p', result.message || 'Saved questions could not be loaded.'));return; }
    if (!result.data.length) { body.append(element('p', 'No saved questions yet. Start a new research question and choose Save question.'));return; }
    result.data.forEach(item => { const row = element('article', undefined, 'saved-row');const open = element('button', item.question);open.append(element('small', `${item.request.ticker} · ${item.request.value_period_end} · ${new Date(item.created_at).toLocaleDateString()}`));open.addEventListener('click', () => loadQuery({ question: item.question, ...item.request }));const remove = element('button', 'Delete', 'text-button');remove.addEventListener('click', async () => { const r = await api(`saved?id=${encodeURIComponent(item.id)}`, { method: 'DELETE' });if (r.status === 'ok') renderSaved();else toast(r.message || 'Could not delete the question.'); });row.append(open, remove);body.append(row); });
  } catch { body.replaceChildren(element('p', 'Your saved questions could not be reached.')); }
}
$$('[data-view]').forEach(button => button.addEventListener('click', () => view(button.dataset.view)));
$$('.mode').forEach(button => button.addEventListener('click', () => { invalidateResult();setMode(button.dataset.mode); }));
$('#company').addEventListener('change', () => { invalidateResult();updateFilings(); });$('#filing').addEventListener('change', () => { invalidateResult();updatePeriod(); });$('#period').addEventListener('change', invalidateResult);$('#filing-search').addEventListener('input', renderLibrary);$('#question').addEventListener('input', () => { invalidateResult();updateCount(); });$('#ask').addEventListener('click', investigate);
$('#period-kind').addEventListener('change', invalidateResult);
$('#new-research').addEventListener('click', () => { if (state.busy) return;view('research');$('#question').value = '';updateCount();$('#answer-section').hidden = true;state.result = null;clearEvidence();$('#question').focus(); });
document.addEventListener('keydown', event => { if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') { event.preventDefault();investigate(); }if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault();view('research');$('#question').focus(); } });
const examples = { margin: ['What was Apple’s gross margin percentage in fiscal year 2021?', 'numerical'], risk: ['What supply-chain risks does Apple describe in its fiscal 2021 annual report?', 'narrative'], chart: ['How did Apple’s shareholder returns compare with the S&P 500 in the 2021 report?', 'chart'] };
$$('[data-example]').forEach(button => button.addEventListener('click', () => { const [question, mode] = examples[button.dataset.example];loadQuery({ question, mode, ticker: 'AAPL', accession: '0000320193-21-000105', value_period_end: '2021-09-25' }); }));
$('#copy-answer').addEventListener('click', async () => { try { await navigator.clipboard.writeText(state.result?.answer || '');toast('Answer copied.'); } catch { toast('Clipboard access is unavailable.'); } });
$('#export-answer').addEventListener('click', () => { if (!state.result) return;const blob = new Blob([JSON.stringify({ query: state.lastQuery, result: state.result }, null, 2)], { type: 'application/json' });const url = URL.createObjectURL(blob);const link = element('a');link.href = url;link.download = 'finrag-research.json';link.click();setTimeout(() => URL.revokeObjectURL(url), 1000); });
$('#save-question').addEventListener('click', async () => { if (!state.token) { showAuth();return; }try { const result = await api('saved', { method: 'POST', body: JSON.stringify(state.lastQuery || query()) });toast(result.status === 'ok' ? 'Question saved privately.' : result.message || 'Could not save the question.'); } catch { toast('Could not reach saved questions.'); } });
$('#account-button').addEventListener('click', showAuth);$('#close-auth').addEventListener('click', () => $('#auth-dialog').close());$('#refresh-status').addEventListener('click', refreshHealth);
$('#auth-form').addEventListener('submit', async event => { event.preventDefault();$('#auth-submit').disabled = true;try { const result = await api('auth/start', { method: 'POST', body: JSON.stringify({ email: $('#email').value.trim() }) });$('#auth-message').textContent = result.message; } catch { $('#auth-message').textContent = 'Sign-in could not be reached.'; }finally { $('#auth-submit').disabled = !state.health?.saved_queries.sign_in_configured; } });
$('#sign-out').addEventListener('click', () => { state.token = null;sessionStorage.removeItem('finrag_token');$('#account-label').textContent = 'Your workspace';$('#account-detail').textContent = 'Sign in to save questions';$('#auth-dialog').close();renderSaved();toast('Signed out of this browser.'); });
$('#mobile-menu').addEventListener('click', () => { const open = $('.sidebar').classList.toggle('open');$('#mobile-menu').setAttribute('aria-expanded', String(open)); });
let reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
function setMotion() { document.body.classList.toggle('reduced-motion', reduced);$('#motion-toggle').textContent = reduced ? 'MOTION OFF' : 'MOTION ON';$('#motion-toggle').setAttribute('aria-pressed', String(reduced)); }
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
