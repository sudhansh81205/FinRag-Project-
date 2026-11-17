import test from 'node:test';
import assert from 'node:assert/strict';
import { handle, validateQuery } from '../lib/api.mjs';
const valid = { question: 'What was gross margin?', ticker: 'AAPL', accession: '0000320193-21-000105', value_period_end: '2021-09-25', scope: 'consolidated', mode: 'numerical' };
const req = (path, body, method = body ? 'POST' : 'GET', headers = {}) => new Request(`https://finrag.example/api/${path}`, { method, headers: { 'Content-Type': 'application/json', ...headers }, ...(body ? { body: JSON.stringify(body) } : {}) });
test('filing contract validates company, exact filing and comparative date', () => {
  assert.equal(validateQuery(valid), '');
  for (const bad of [{ ticker: 'MSFT' }, { value_period_end: '2099-01-01' }, { value_period_end: '2021-02-30' }, { scope: 'segment' }, { question: '' }]) assert.notEqual(validateQuery({ ...valid, ...bad }), '');
});
test('missing engine never produces a financial answer or model call', async () => {
  let calls = 0;const result = await handle(req('answer', valid), { env: {}, fetchImpl: () => { calls++; } });const body = await result.json();
  assert.equal(result.status, 503);assert.equal(body.status, 'index_not_ready');assert.equal(body.answer, '');assert.equal(calls, 0);
});
test('inventory and status are actual separate acceptance levels', async () => {
  const body = await (await handle(req('filings'), { env: {} })).json();assert.equal(body.filings.length, 18);assert.equal(body.status, 'inventory_only');
  const health = await (await handle(req('health'), { env: {} })).json();assert.equal(health.saved_queries.configured, false);assert.equal(health.runtime.status, 'index_not_ready');
});
const env = { FINRAG_BACKEND_URL: 'https://engine.example', FINRAG_BACKEND_TOKEN: 'private-test-token' };
const answer = { status: 'ok', answer: '41.78%', request: valid, evidence: [{ evidence_id: 'E1', content: 'original source' }], included_evidence_ids: ['E1'], calculations: [] };
test('correct request-bound engine response is preserved', async () => {
  let called;const response = await handle(req('answer', valid), { env, fetchImpl: async (url, options) => { called = { url, options };return Response.json(answer); } });
  assert.equal((await response.json()).answer, '41.78%');assert.equal(called.url, 'https://engine.example/answer');assert.equal(called.options.headers.Authorization, 'Bearer private-test-token');
});
test('wrong period and excluded citations are refused at gateway', async () => {
  for (const changed of [{ question: 'A different question' }, { request: { ...valid, value_period_end: '2020-09-26' } }, { included_evidence_ids: ['FOREIGN'] }, { evidence: [] }]) {
    const result = await (await handle(req('answer', valid), { env, fetchImpl: async () => Response.json({ ...answer, ...changed }) })).json();assert.equal(result.status, 'service_error');assert.equal(result.answer, '');
  }
});
test('upstream provider errors are visible without fallback or leaked credentials', async () => {
  const result = await (await handle(req('answer', valid), { env, fetchImpl: async () => { throw new Error('secret'); } })).json();assert.equal(result.status, 'service_error');assert.equal(result.answer, '');assert.ok(!JSON.stringify(result).includes('secret'));
});
test('unconfigured database and anonymous access do not expose private rows', async () => {
  assert.equal((await handle(req('saved'), { env: {} })).status, 503);
  assert.equal((await handle(req('saved'), { env: { SUPABASE_URL: 'https://example.supabase.co', SUPABASE_PUBLISHABLE_KEY: 'public-test' } })).status, 401);
});
test('expired auth is denied before any database query', async () => {
  let calls = 0;const result = await handle(req('saved', null, 'GET', { Authorization: `Bearer ${'a'.repeat(30)}` }), { env: { SUPABASE_URL: 'https://example.supabase.co', SUPABASE_PUBLISHABLE_KEY: 'public-test' }, fetchImpl: async () => { calls++;return new Response('', { status: 401 }); } });assert.equal(result.status, 401);assert.equal(calls, 1);
});
test('invalid JSON and malformed configured endpoints fail closed', async () => {
  const malformed = new Request('https://finrag.example/api/answer', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{' });assert.equal((await handle(malformed, { env: {} })).status, 400);
  const response = await handle(req('answer', valid), { env: { FINRAG_BACKEND_URL: 'http://private.example' } });assert.equal(response.status, 502);
});

test('database connectivity does not enable unverified email sign-in', async () => {
  let calls = 0;const db = { SUPABASE_URL: 'https://db.example', SUPABASE_PUBLISHABLE_KEY: 'public-test-key' };
  const health = await (await handle(req('health'), { env: db })).json();
  assert.equal(health.saved_queries.configured, true);assert.equal(health.saved_queries.sign_in_configured, false);
  const denied = await handle(req('auth/start', { email: 'owner@example.invalid' }), { env: db, fetchImpl: () => { calls++; } });
  assert.equal(denied.status, 503);assert.equal(calls, 0);
  const enabled = await handle(req('auth/start', { email: 'owner@example.invalid' }), { env: { ...db, SUPABASE_AUTH_READY: 'true' }, fetchImpl: async () => { calls++;return Response.json({}); } });
  assert.equal(enabled.status, 200);assert.equal(calls, 1);
});

test('local demo permits only explicitly opted-in development loopback HTTP', async () => {
 const local = { ...env, FINRAG_BACKEND_URL: 'http://127.0.0.1:8000', FINRAG_ALLOW_LOOPBACK_HTTP: 'true', NODE_ENV: 'development' };
 const success = await handle(req('answer', valid), { env: local, fetchImpl: async () => Response.json(answer) });
 assert.equal(success.status, 200);
 for (const bad of [{NODE_ENV:'production'}, {FINRAG_ALLOW_LOOPBACK_HTTP:'false'}, {FINRAG_BACKEND_URL:'http://192.168.1.2:8000'}, {FINRAG_BACKEND_URL:'http://localhost.evil'}]) {
  let calls=0;const response=await handle(req('answer',valid),{env:{...local,...bad},fetchImpl:()=>{calls++;}});
  assert.equal(response.status,502);assert.equal(calls,0);
 }
});
test('local model gets a bounded answer deadline, separate from health', async () => {
 const health=await (await handle(req('health'),{env:{}})).json();assert.equal(health.answer_timeout_ms,250000);
 const shorter=await (await handle(req('health'),{env:{FINRAG_BACKEND_TIMEOUT_MS:'45000'}})).json();assert.equal(shorter.answer_timeout_ms,55000);
 for(const limit of ['0','240001','NaN','1.5']) {
  const r=await handle(req('health'),{env:{FINRAG_BACKEND_TIMEOUT_MS:limit}});assert.equal(r.status,502);
 }
});

test('saved instant questions retain the selected period type', async () => {
  let inserted;
  const db = { SUPABASE_URL: 'https://db.example', SUPABASE_PUBLISHABLE_KEY: 'public-test' };
  const response = await handle(req('saved', { ...valid, period_kind: 'instant' }, 'POST', { Authorization: `Bearer ${'a'.repeat(30)}` }), { env: db, fetchImpl: async (url, options) => {
    if (url.endsWith('/auth/v1/user')) return Response.json({ id: 'owner' });
    inserted = JSON.parse(options.body);return Response.json([inserted]);
  } });
  assert.equal(response.status, 200);assert.equal(inserted.request.period_kind, 'instant');
});

test('job transport keeps provider credentials server-side and binds completed results to the exact question', async () => {
  const id = 'a'.repeat(43);
  let posted;
  const queued = await handle(req('jobs', valid), { env, fetchImpl: async (url, options) => {
    assert.equal(url, 'https://engine.example/jobs');posted = options;
    return Response.json({ status: 'queued', job_id: id });
  } });
  assert.equal(queued.status, 202);assert.equal((await queued.json()).job_id, id);
  assert.equal(posted.headers.Authorization, 'Bearer private-test-token');
  for (const status of ['queued', 'running']) {
    const pending = await handle(req('jobs/poll', { ...valid, job_id: id }), { env, fetchImpl: async () => Response.json({ status }) });
    assert.equal(pending.status, 202);
  }
  for (const request of [valid, { ...valid, question: 'A different question' }]) {
    const completed = await handle(req('jobs/poll', { ...valid, job_id: id }), { env, fetchImpl: async () => Response.json({ status: 'completed', request, result: answer }) });
    assert.equal(completed.status, request === valid ? 200 : 502);
    if (request !== valid) assert.equal((await completed.json()).answer, '');
  }
  for (const changed of [{ included_evidence_ids: ['foreign'] }, { request: { ...valid, ticker: 'MSFT' } }]) {
    const refused = await handle(req('jobs/poll', { ...valid, job_id: id }), { env, fetchImpl: async () => Response.json({ status: 'completed', request: valid, result: { ...answer, ...changed } }) });
    assert.equal(refused.status, 502);assert.equal((await refused.json()).answer, '');
  }
});

test('full queues, expired jobs and malformed capabilities fail with no answer', async () => {
  for (const [upstreamStatus, status, expected] of [[429, 'busy', 429], [200, 'not_found', 404]]) {
    const response = await handle(req('jobs/poll', { ...valid, job_id: 'a'.repeat(43) }), { env, fetchImpl: async () => Response.json({ status }, { status: upstreamStatus }) });
    assert.equal(response.status, expected);assert.equal((await response.json()).answer, '');
  }
  let calls = 0;
  const invalid = await handle(req('jobs/poll', { ...valid, job_id: 'short' }), { env, fetchImpl: () => calls++ });
  assert.equal(invalid.status, 400);assert.equal(calls, 0);
});

test('loopback HTTP backend is explicit local development only; production remains HTTPS', async () => {
  let calls = 0;
  const localEnv = { FINRAG_BACKEND_URL: 'http://127.0.0.1:8000', FINRAG_BACKEND_TOKEN: 'private-test' };
  const fetchImpl = async () => { calls++;return Response.json(answer); };
  assert.equal((await handle(req('answer', valid), { env: localEnv, fetchImpl })).status, 502);
  assert.equal(calls, 0);
  assert.equal((await handle(req('answer', valid), { env: localEnv, fetchImpl, allowLocalBackend: true })).status, 200);
  assert.equal(calls, 1);
  const remoteEnv = { ...localEnv, FINRAG_BACKEND_URL: 'http://remote.example' };
  assert.equal((await handle(req('answer', valid), { env: remoteEnv, fetchImpl, allowLocalBackend: true })).status, 502);
  assert.equal(calls, 1);
});

test('only polling transport failures are retryable; completed model failures and submission are final', async () => {
 const job_id = 'a'.repeat(43);
 const interrupted = async () => { throw new Error('secret provider detail'); };
 const poll = await (await handle(req('jobs/poll', { ...valid, job_id }), { env, fetchImpl: interrupted })).json();
 assert.equal(poll.retryable, true); assert.equal(poll.answer, ''); assert.ok(!JSON.stringify(poll).includes('secret'));
 const submit = await (await handle(req('jobs', valid), { env, fetchImpl: interrupted })).json();
 assert.equal(submit.retryable, undefined);
 const failure = await (await handle(req('jobs/poll', { ...valid, job_id }), { env, fetchImpl: async () => Response.json({ status: 'completed', result: { status: 'service_error', message: 'Model failed.' } }) })).json();
 assert.equal(failure.retryable, undefined); assert.equal(failure.answer, '');
 const unauthorized = await (await handle(req('jobs/poll', { ...valid, job_id }), { env, fetchImpl: async () => Response.json({ status: 'unauthorized' }, { status: 401 }) })).json();
 assert.equal(unauthorized.retryable, undefined);
});
