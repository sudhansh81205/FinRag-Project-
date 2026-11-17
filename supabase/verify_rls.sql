-- Run only on the named FinRAG development database. All fixtures roll back.
-- This is a runtime SQL verification script, not a migration or fabricated test result.
begin;
insert into auth.users (id, email) values
 ('10000000-0000-0000-0000-000000000001','finrag-rls-a@example.invalid'),
 ('10000000-0000-0000-0000-000000000002','finrag-rls-b@example.invalid');
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"10000000-0000-0000-0000-000000000001","role":"authenticated"}',true);
insert into public.saved_queries (user_id,question,request) values
 ('10000000-0000-0000-0000-000000000001','Owner A question',
 '{"ticker":"AAPL","accession":"0000320193-21-000105","value_period_end":"2021-09-25","scope":"consolidated","mode":"auto"}');
do $$ begin
 if (select count(*) from public.saved_queries) <> 1 then raise exception 'Owner cannot read own saved query'; end if;
 begin
  insert into public.saved_queries (user_id,question,request) values
   ('10000000-0000-0000-0000-000000000002','Foreign owner write',
    '{"ticker":"AAPL","accession":"x","value_period_end":"2021-09-25","scope":"consolidated","mode":"auto"}');
  raise exception 'Cross-owner insertion unexpectedly succeeded';
 exception when insufficient_privilege then null; end;
end $$;
select set_config('request.jwt.claims','{"sub":"10000000-0000-0000-0000-000000000002","role":"authenticated"}',true);
do $$ begin
 if (select count(*) from public.saved_queries) <> 0 then raise exception 'Cross-owner read leaked a row'; end if;
 delete from public.saved_queries;
 if found then raise exception 'Cross-owner delete removed a row'; end if;
end $$;
reset role;
set local role anon;
do $$ begin
 begin
  perform * from public.saved_queries;
  raise exception 'Anonymous read unexpectedly granted';
 exception when insufficient_privilege then null; end;
end $$;
reset role;
rollback;
