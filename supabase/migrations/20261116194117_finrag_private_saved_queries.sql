-- Apply to the explicitly selected FinRAG project after inspecting existing objects.
-- Personal saved questions are NOT evaluation outputs or accepted source evidence.
begin;
create table public.saved_queries (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  question text not null check (char_length(question) between 3 and 2000),
  request jsonb not null check (
    jsonb_typeof(request) = 'object'
    and request ?& array['ticker','accession','value_period_end','scope','mode']
    and request->>'scope' = 'consolidated'
    and request->>'mode' in ('auto','narrative','numerical','chart')
  ),
  created_at timestamptz not null default now()
);
create index saved_queries_owner_created_idx on public.saved_queries (user_id, created_at desc);
alter table public.saved_queries enable row level security;
revoke all on public.saved_queries from public, anon, authenticated;
grant select, insert, delete on public.saved_queries to authenticated;
create policy own_saved_queries_select on public.saved_queries for select to authenticated
  using ((select auth.uid()) = user_id);
create policy own_saved_queries_insert on public.saved_queries for insert to authenticated
  with check ((select auth.uid()) = user_id);
create policy own_saved_queries_delete on public.saved_queries for delete to authenticated
  using ((select auth.uid()) = user_id);
comment on table public.saved_queries is 'Private user questions; no model output, official evaluation label or accepted evidence.';
commit;
