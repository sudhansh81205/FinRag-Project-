import test from 'node:test';
import assert from 'node:assert/strict';
import { handle, filings } from '../lib/api.mjs';

const env = {SUPABASE_URL:'https://db.example',SUPABASE_PUBLISHABLE_KEY:'publishable-fixture',SUPABASE_PASSWORD_AUTH_READY:'true'};
const headers = {'Content-Type':'application/json',Authorization:`Bearer ${'a'.repeat(30)}`};
const f = filings.at(-1);
const value = {question:`How much revenue did ${f.issuer} report?`,ticker:f.ticker,accession:f.accession,value_period_end:f.period_end,period_kind:'duration',scope:'consolidated',mode:'auto'};
const req = (route, method='GET', body) => new Request(`https://finrag.example/api/${route}`,{method,headers,...(body?{body:JSON.stringify(body)}:{})});

test('a fresh request/session reads server-persisted questions and delete survives another refresh', async () => {
  let rows = [];
  const fetchImpl = async (url, options) => {
    if (url.endsWith('/auth/v1/user')) return Response.json({id:'owner'});
    if (options.method === 'POST') {rows.push({id:'11111111-1111-4111-8111-111111111111',...JSON.parse(options.body)});return Response.json(rows);}
    if (options.method === 'DELETE') {rows=[];return Response.json([]);}
    return Response.json(rows);
  };
  assert.equal((await handle(req('auth/session'),{env,fetchImpl})).status,200);
  await handle(req('saved','POST',value),{env,fetchImpl});
  const afterRefresh = await (await handle(req('saved'),{env:{...env},fetchImpl})).json();
  assert.equal(afterRefresh.data[0].question,value.question);
  assert.equal(afterRefresh.data[0].request.accession,f.accession);
  await handle(req('saved?id=11111111-1111-4111-8111-111111111111','DELETE'),{env,fetchImpl});
  assert.deepEqual((await (await handle(req('saved'),{env,fetchImpl})).json()).data,[]);
});

test('saved pages are bounded and every page revalidates the current user', async () => {
  let users=0;let requested;
  const fetchImpl=async(url)=>{if(url.endsWith('/auth/v1/user')){users++;return Response.json({id:'owner'});}requested=new URL(url);return Response.json(Array.from({length:31},(_,i)=>({id:String(i)})));};
  const r=await (await handle(req('saved?offset=30'),{env,fetchImpl})).json();
  assert.equal(r.data.length,30);assert.equal(r.has_more,true);assert.equal(r.offset,30);assert.equal(requested.searchParams.get('offset'),'30');
  assert.equal((await handle(req('saved?offset=-1'),{env,fetchImpl})).status,400);
  assert.equal((await handle(req('auth/session'),{env,fetchImpl})).status,200);assert.equal(users,3);
});

test('the filing library validates every registered source selection', async () => {
  assert.equal(filings.length,18);
  for(const filing of filings){const {validateQuery}=await import('../lib/api.mjs');assert.equal(validateQuery({...value,ticker:filing.ticker,accession:filing.accession,value_period_end:filing.period_end}),'');}
  const status=await (await handle(req('project-status'),{env:{}})).json();
  assert.equal(status.coverage.prd_application_counts_met,true);assert.equal(status.experiments.final_matrix_completed,0);
});
