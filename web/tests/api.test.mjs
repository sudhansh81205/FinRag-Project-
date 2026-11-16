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
  for (const changed of [{ request: { ...valid, value_period_end: '2020-09-26' } }, { included_evidence_ids: ['FOREIGN'] }, { evidence: [] }]) {
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
