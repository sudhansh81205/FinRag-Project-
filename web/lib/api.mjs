import { readFileSync } from 'node:fs';

export const filings = JSON.parse(readFileSync(new URL('../data/filings.json', import.meta.url), 'utf8'));
const statuses = new Set(['ok', 'invalid_request', 'index_not_ready', 'insufficient_evidence', 'service_error']);
const empty = (status, message) => ({ status, message, answer: '', evidence: [], calculations: [], included_evidence_ids: [] });
const json = (body, status = 200) => Response.json(body, { status, headers: { 'Cache-Control': 'no-store' } });
const tokenOf = request => /^Bearer [A-Za-z0-9_.-]{20,4096}$/.test(request.headers.get('Authorization') || '') ? request.headers.get('Authorization') : null;
function endpoint(raw, allowLoopback = false) {
  if (!raw) return null;
  const url = new URL(raw);
  const local = allowLoopback && url.protocol === 'http:' && ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname);
  if ((!local && url.protocol !== 'https:') || url.username || url.password || url.search || url.hash || url.pathname !== '/') throw new Error('Invalid configured endpoint');
  return url.origin;
}
export function validateQuery(body) {
  if (!body || typeof body !== 'object' || Array.isArray(body)) return 'A question and filing are required.';
  if (typeof body.question !== 'string' || body.question.trim().length < 3 || body.question.length > 2000) return 'Enter a question between 3 and 2,000 characters.';
  const filing = filings.find(f => f.accession === body.accession);
  if (!filing || body.ticker !== filing.ticker) return 'Choose a supported company and filing.';
  if (!/^\d{4}-\d{2}-\d{2}$/.test(body.value_period_end || '')) return 'Choose a valid value-period end.';
  const date = new Date(body.value_period_end + 'T00:00:00Z');
  if (!Number.isFinite(+date) || date.toISOString().slice(0, 10) !== body.value_period_end) return 'Choose a valid value-period end.';
  const delta = (new Date(filing.period_end) - date) / 86400000;
  if (!(delta >= 0 && delta <= 10 || delta >= 355 && delta <= 375 || delta >= 720 && delta <= 745)) return 'The value period must belong to this filing or its prior two comparatives.';
  if (body.scope !== 'consolidated') return 'Only consolidated statements are supported.';
  if (body.period_kind !== undefined && !['duration', 'instant'].includes(body.period_kind)) return 'Choose a fiscal-year total or year-end balance.';
  if (!['auto', 'narrative', 'numerical', 'chart'].includes(body.mode || 'auto')) return 'Choose a supported question type.';
  return '';
}
async function readBody(request) {
  if (!request.headers.get('content-type')?.startsWith('application/json')) throw new Error('JSON required');
  const text = await request.text();
  if (text.length > 12000) throw new Error('Request too large');
  return JSON.parse(text);
}
async function upstream(fetchImpl, url, options = {}, timeout = 22000) {
  return fetchImpl(url, { ...options, redirect: 'error', signal: AbortSignal.timeout(timeout) });
}
function requestMatches(result, body) {
  const r = result.request;
  return r && (result.question ?? r.question) === body.question && r.ticker === body.ticker && r.accession === body.accession && r.value_period_end === body.value_period_end && r.scope === body.scope && (body.period_kind === undefined || r.period_kind === body.period_kind);
}
function checkedAnswer(result, body, responseOk = true) {
  if (!result || !statuses.has(result.status)) return json(empty('service_error', 'The engine returned an unsupported response.'), 502);
  if (result.status !== 'ok') return json(empty(result.status, typeof result.message === 'string' ? result.message.slice(0, 1000) : 'The question could not be answered.'), result.status === 'service_error' ? 502 : 200);
  if (!responseOk || !requestMatches(result, body) || typeof result.answer !== 'string' || !result.answer.trim() || !Array.isArray(result.evidence) || !result.evidence.length || !Array.isArray(result.included_evidence_ids)) return json(empty('service_error', 'The answer lacked request-bound source evidence.'), 502);
  const ids = result.evidence.map(r => r?.evidence_id || r?.id);
  if (ids.some(id => typeof id !== 'string') || new Set(ids).size !== ids.length || ids.length !== result.included_evidence_ids.length || ids.some(id => !result.included_evidence_ids.includes(id))) return json(empty('service_error', 'The cited evidence did not match the included context.'), 502);
  return json(result);
}
export async function handle(request, { env = process.env, fetchImpl = fetch, allowLocalBackend = false } = {}) {
  const url = new URL(request.url);
  const route = (url.searchParams.get('route') || url.pathname.replace(/^\/api\/?/, '')).replace(/^\/+|\/+$/g, '');
  try {
    if (route === 'filings' && request.method === 'GET') return json({ filings, status: 'limited_workspace', independently_accepted_filings: 1, note: 'Two selected development filings; runtime health reports connected evidence. Independent final-study acceptance is separate.' });
    const supabase = endpoint(env.SUPABASE_URL);
    const publicKey = env.SUPABASE_PUBLISHABLE_KEY || env.SUPABASE_ANON_KEY;
    const dbReady = Boolean(supabase && publicKey);
    const magicLinkReady = dbReady && env.SUPABASE_AUTH_READY === "true";
    const passwordReady = dbReady && env.SUPABASE_PASSWORD_AUTH_READY === "true";
    const authReady = magicLinkReady || passwordReady;
    const backend = endpoint(env.FINRAG_BACKEND_URL, env.NODE_ENV !== 'production' && (allowLocalBackend || env.FINRAG_ALLOW_LOOPBACK_HTTP === 'true'));
    const answerTimeout = Number(env.FINRAG_BACKEND_TIMEOUT_MS || 240000);
    if (!Number.isInteger(answerTimeout) || answerTimeout < 1000 || answerTimeout > 240000) throw new Error('Invalid answer timeout');
    if (route === 'health' && request.method === 'GET') {
      let runtime = { status: 'index_not_ready', message: 'The financial engine is not connected. You can explore the filing inventory.' };
      if (backend) {
        try {
          const response = await upstream(fetchImpl, `${backend}/health`, { headers: { Authorization: `Bearer ${env.FINRAG_BACKEND_TOKEN || ''}` } }, 5000);
          const body = await response.json();
          runtime = response.ok && ['ready', 'index_not_ready'].includes(body.status) ? body : { status: 'service_error', message: 'The financial engine could not be reached.' };
        } catch { runtime = { status: 'service_error', message: 'The financial engine could not be reached.' }; }
      }
      return json({ runtime, answer_timeout_ms: answerTimeout + 10000, saved_queries: { configured: dbReady, provider: 'Supabase', sign_in_configured: authReady, sign_in_method: passwordReady ? 'password' : 'email_link', status: authReady ? 'sign_in_required' : dbReady ? 'auth_setup_required' : 'not_configured' }, build: 'finrag-web-v1', corpus: { inventory: filings.length, companies: new Set(filings.map(f => f.ticker)).size, accepted: 1, connected: (runtime.supported_filings || []).length } });
    }
    if (route === 'answer' && request.method === 'POST') {
      let body;
      try { body = await readBody(request); } catch { return json(empty('invalid_request', 'Send a valid JSON question under the size limit.'), 400); }
      const problem = validateQuery(body);
      if (problem) return json(empty('invalid_request', problem), 400);
      if (!backend || !env.FINRAG_BACKEND_TOKEN) return json(empty('index_not_ready', 'The source index and model service are not connected yet. No financial answer was generated.'), 503);
      const response = await upstream(fetchImpl, `${backend}/answer`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${env.FINRAG_BACKEND_TOKEN}` }, body: JSON.stringify(body) }, answerTimeout);
      const result = await response.json();
      return checkedAnswer(result, body, response.ok);
    }
    if (['jobs', 'jobs/poll'].includes(route) && request.method === 'POST') {
      let body;
      try { body = await readBody(request); } catch { return json(empty('invalid_request', 'Send a valid JSON request under the size limit.'), 400); }
      const problem = validateQuery(body);
      if (problem) return json(empty('invalid_request', problem), 400);
      if (route === 'jobs/poll' && !/^[A-Za-z0-9_-]{43}$/.test(body.job_id || '')) return json(empty('invalid_request', 'Invalid job reference.'), 400);
      if (!backend || !env.FINRAG_BACKEND_TOKEN) return json(empty('index_not_ready', 'The model service is not connected.'), 503);
      let response, result;
      try {
        response = await upstream(fetchImpl, `${backend}/${route}`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${env.FINRAG_BACKEND_TOKEN}` }, body: JSON.stringify(route === 'jobs' ? body : { job_id: body.job_id }) }, 10000);
        result = await response.json();
      } catch {
        return json({ ...empty('service_error', 'The answer job connection was interrupted.'), ...(route === 'jobs/poll' ? { retryable: true } : {}) }, 502);
      }
      if (response.status === 429 && result.status === 'busy') return json(empty('service_error', 'The model queue is full. Try again shortly.'), 429);
      if (!response.ok) return json({ ...empty('service_error', 'The answer job could not be reached.'), ...(route === 'jobs/poll' && response.status >= 500 ? { retryable: true } : {}) }, 502);
      if (route === 'jobs' && result.status === 'queued' && /^[A-Za-z0-9_-]{43}$/.test(result.job_id || '')) return json({ status: 'queued', job_id: result.job_id, expires_in_seconds: 900 }, 202);
      if (route === 'jobs/poll' && ['queued', 'running'].includes(result.status)) return json({ status: result.status }, 202);
      if (route === 'jobs/poll' && result.status === 'completed') {
        const fields = ['question', 'ticker', 'accession', 'value_period_end', 'period_kind', 'scope', 'mode'];
        if (result.result?.status === 'ok' && (!result.request || fields.some(key => (result.request[key] ?? (key === 'mode' ? 'auto' : undefined)) !== (body[key] ?? (key === 'mode' ? 'auto' : undefined))))) return json(empty('service_error', 'The job belongs to a different question.'), 502);
        return checkedAnswer(result.result, body);
      }
      if (route === 'jobs/poll' && result.status === 'not_found') return json(empty('service_error', 'This answer job expired or is unavailable. Submit the question again.'), 404);
      return json(empty('service_error', 'The engine returned an invalid job response.'), 502);
    }
    if (['auth/password', 'auth/signup', 'auth/verify'].includes(route) && request.method === 'POST') {
      if (!passwordReady) return json({ status: 'not_configured', message: 'Private account sign-in is not configured.' }, 503);
      const origin = request.headers.get('origin');
      if (origin && origin !== url.origin) return json({ status: 'invalid_request', message: 'Sign in from this workspace.' }, 403);
      const body = await readBody(request);
      let endpointPath, payload;
      if (route === 'auth/verify') {
        let link;try { link = new URL(body.confirmation_url); } catch { return json({status:'invalid_request',message:'Paste the confirmation link from your email.'},400); }
        const hash = link.searchParams.get('token') || link.searchParams.get('token_hash');const type = link.searchParams.get('type');
        if (link.origin !== supabase || link.pathname !== '/auth/v1/verify' || !/^[A-Za-z0-9_-]{20,256}$/.test(hash || '') || !['signup','email','magiclink'].includes(type)) return json({status:'invalid_request',message:'Use the original FinRAG confirmation link from your email.'},400);
        endpointPath = '/auth/v1/verify';payload = {token_hash:hash,type};
      } else {
        if (typeof body.email !== 'string' || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(body.email) || body.email.length > 254 || typeof body.password !== 'string' || body.password.length < 12 || body.password.length > 256) return json({status:'invalid_request',message:'Enter a valid email address and a password of 12 to 256 characters.'},400);
        endpointPath = route === 'auth/signup' ? '/auth/v1/signup' : '/auth/v1/token?grant_type=password';payload = {email:body.email,password:body.password};
      }
      const response = await upstream(fetchImpl, supabase + endpointPath, {method:'POST',headers:{apikey:publicKey,'Content-Type':'application/json'},body:JSON.stringify(payload)});
      const session = await response.json();
      if (!response.ok) return json({status:'service_error',message: response.status === 429 ? 'Too many sign-in attempts. Wait before trying again.' : session.error_code === 'email_not_confirmed' ? 'Confirm your email first. You can paste the confirmation link below.' : 'Sign-in could not be completed. Check your email, password or confirmation link.'},response.status === 429 ? 429 : 400);
      if (typeof session.access_token === 'string' && /^[A-Za-z0-9_.-]{20,4096}$/.test(session.access_token)) return json({status:'ok',access_token:session.access_token,expires_in:session.expires_in});
      if (route === 'auth/signup') return json({status:'confirmation_required',message:'Check your email to confirm your account, then sign in. If the link opens another page, paste the original confirmation link below.'});
      return json({status:'service_error',message:'Sign-in did not return a valid session.'},502);
    }
    if (route === 'auth/start'  && request.method === 'POST') {
      if (!magicLinkReady) return json({ status: 'not_configured', message: 'Email sign-in setup is pending. The database is connected; its redirect URL and email delivery must be verified first.' }, 503);
      const body = await readBody(request);
      if (typeof body.email !== 'string' || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(body.email) || body.email.length > 254) return json({ status: 'invalid_request', message: 'Enter a valid email address.' }, 400);
      const origin = request.headers.get('origin');
      if (origin && origin !== url.origin) return json({ status: 'invalid_request' }, 403);
      const response = await upstream(fetchImpl, `${supabase}/auth/v1/otp?redirect_to=${encodeURIComponent(url.origin + '/')}`, { method: 'POST', headers: { apikey: publicKey, 'Content-Type': 'application/json' }, body: JSON.stringify({ email: body.email, create_user: true, gotrue_meta_security: {} }) });
      return json({ status: response.ok ? 'ok' : 'service_error', message: response.ok ? 'Check your inbox for a sign-in link.' : 'Sign-in could not be started. Try again later.' }, response.ok ? 200 : 502);
    }
    if (route === 'saved' && ['GET', 'POST', 'DELETE'].includes(request.method)) {
      if (!dbReady) return json({ status: 'not_configured', message: 'Supabase saved queries are not configured.' }, 503);
      const authorization = tokenOf(request);
      if (!authorization) return json({ status: 'unauthorized', message: 'Sign in to access your saved queries.' }, 401);
      const auth = await upstream(fetchImpl, `${supabase}/auth/v1/user`, { headers: { apikey: publicKey, Authorization: authorization } });
      if (!auth.ok) return json({ status: 'unauthorized', message: 'Your sign-in expired. Sign in again.' }, 401);
      const user = await auth.json();
      if (!user.id) return json({ status: 'unauthorized' }, 401);
      let suffix = '?select=id,question,request,created_at&order=created_at.desc&limit=30';
      const options = { method: request.method, headers: { apikey: publicKey, Authorization: authorization, 'Content-Type': 'application/json', Prefer: 'return=representation' } };
      if (request.method === 'POST') {
        const body = await readBody(request); const problem = validateQuery(body);
        if (problem) return json({ status: 'invalid_request', message: problem }, 400);
        const { ticker, accession, value_period_end, period_kind, scope, mode = 'auto' } = body;
        options.body = JSON.stringify({ user_id: user.id, question: body.question.trim(), request: { ticker, accession, value_period_end, ...(period_kind ? { period_kind } : {}), scope, mode } });
        suffix = '';
      }
      if (request.method === 'DELETE') {
        const id = url.searchParams.get('id');
        if (!/^[a-f0-9-]{36}$/i.test(id || '')) return json({ status: 'invalid_request' }, 400);
        suffix = `?id=eq.${encodeURIComponent(id)}`;
      }
      const response = await upstream(fetchImpl, `${supabase}/rest/v1/saved_queries${suffix}`, options);
      if (!response.ok) return json({ status: 'service_error', message: 'Saved queries could not be loaded. Check the database migration and access policies.' }, 502);
      const data = await response.json();
      return json({ status: 'ok', data });
    }
    return json({ status: 'not_found', message: 'Endpoint not found.' }, 404);
  } catch { return json(empty('service_error', 'The service is unavailable. No fallback answer was used.'), 502); }
}
