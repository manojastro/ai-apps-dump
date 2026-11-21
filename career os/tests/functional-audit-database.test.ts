import { beforeAll, afterAll, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { PGlite } from "@electric-sql/pglite";
import { pgcrypto } from "@electric-sql/pglite/contrib/pgcrypto";

// Isolated PostgreSQL fixture. This never connects to production Supabase.
const db = new PGlite({ extensions: { pgcrypto } });
const OWNER = "00000000-0000-4000-8000-000000000101";
const OTHER = "00000000-0000-4000-8000-000000000102";
const SKILL = "00000000-0000-4000-8000-000000000103";
const TASK = "00000000-0000-4000-8000-000000000104";
beforeAll(async () => {
  await db.exec(`
    create role authenticated; create role anon;
    create schema auth;
    create table auth.users(id uuid primary key,raw_user_meta_data jsonb default '{}');
    create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid $$;
    create schema storage;
    create table storage.buckets(id text primary key,name text,public boolean);
    create table storage.objects(id uuid primary key,bucket_id text,name text);
    create function storage.foldername(name text) returns text[] language sql immutable as $$ select string_to_array(name,'/') $$;
    grant usage on schema public,auth,storage to authenticated,anon;
  `);
  for (const name of ["202609180001_initial.sql", "202609180002_owned_links.sql"]) {
    await db.exec(readFileSync(new URL(`../supabase/migrations/${name}`, import.meta.url), "utf8"));
  }
  // Hosted Storage manages RLS itself; the fixture must enable it explicitly.
  await db.exec("alter table storage.objects enable row level security; grant all on all tables in schema public,storage to authenticated,anon;");
  await db.query("insert into auth.users(id) values($1),($2)", [OWNER, OTHER]);
  await db.query("insert into skills(id,user_id,name) values($1,$2,'AUDIT protected skill')", [SKILL, OWNER]);
  await db.query("insert into tasks(id,user_id,title,skill_id) values($1,$2,'AUDIT protected task',$3)", [TASK, OWNER, SKILL]);
}, 30_000);
afterAll(async () => { await db.close(); });

async function asUser(uid: string, fn: () => Promise<void>) {
  await db.query("select set_config('request.jwt.claim.sub',$1,false)", [uid]);
  await db.exec("set role authenticated");
  try { await fn(); } finally { await db.exec("reset role"); }
}

it("all 31 original public tables have RLS enabled", async () => {
  const rows = (await db.query<{ relrowsecurity: boolean }>("select relrowsecurity from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relkind='r'")).rows;
  expect(rows).toHaveLength(31);
  expect(rows.every(row => row.relrowsecurity)).toBe(true);
});
it("two users cannot read, update, delete or forge task ownership", async () => {
  await asUser(OWNER, async () => { expect((await db.query("select id from tasks")).rows).toHaveLength(1); });
  await asUser(OTHER, async () => {
    expect((await db.query("select id from tasks")).rows).toHaveLength(0);
    expect((await db.query("update tasks set title='AUDIT forbidden' where id=$1 returning id", [TASK])).rows).toHaveLength(0);
    expect((await db.query("delete from tasks where id=$1 returning id", [TASK])).rows).toHaveLength(0);
    await expect(db.query("insert into tasks(user_id,title) values($1,'AUDIT forged')", [OWNER])).rejects.toThrow();
  });
});
it("anonymous clients cannot read core task records", async () => {
  await db.query("select set_config('request.jwt.claim.sub','',false)");
  await db.exec("set role anon");
  try { expect((await db.query("select id from tasks")).rows).toHaveLength(0); }
  finally { await db.exec("reset role"); }
});
it("ownership triggers reject cross-user task and evidence links", async () => {
  await asUser(OTHER, async () => {
    await expect(db.query("insert into tasks(user_id,title,skill_id) values($1,'AUDIT foreign link',$2)", [OTHER, SKILL])).rejects.toThrow("Referenced record must belong");
    await expect(db.query("insert into evidence(user_id,title,kind,skill_id) values($1,'AUDIT foreign proof','code',$2)", [OTHER, SKILL])).rejects.toThrow("Referenced record must belong");
  });
});
it("private evidence folder policies reject another user and allow the owner", async () => {
  await asUser(OWNER, async () => {
    await db.query("insert into storage.objects(id,bucket_id,name) values(gen_random_uuid(),'career-evidence',$1)", [`${OWNER}/audit-proof.txt`]);
    expect((await db.query("select id from storage.objects")).rows).toHaveLength(1);
  });
  await asUser(OTHER, async () => {
    expect((await db.query("select id from storage.objects")).rows).toHaveLength(0);
    await expect(db.query("insert into storage.objects(id,bucket_id,name) values(gen_random_uuid(),'career-evidence',$1)", [`${OWNER}/foreign.txt`])).rejects.toThrow();
  });
});
it("invalid stages, negative time, reversed blocks and duplicate skill names are rejected", async () => {
  await asUser(OWNER, async () => {
    await expect(db.query("update tasks set status='invented' where id=$1", [TASK])).rejects.toThrow();
    await expect(db.query("update tasks set actual_minutes=-1 where id=$1", [TASK])).rejects.toThrow();
    await expect(db.query("insert into planner_blocks(user_id,title,block_date,start_time,end_time) values($1,'AUDIT invalid','2026-10-10','09:00','08:00')", [OWNER])).rejects.toThrow();
    await expect(db.query("insert into skills(user_id,name) values($1,'AUDIT protected skill')", [OWNER])).rejects.toThrow();
  });
});
it("soft deletion hides a parent from active lists and rejects new links", async () => {
  await asUser(OWNER, async () => {
    await db.query("update skills set deleted_at=now() where id=$1", [SKILL]);
    expect((await db.query("select id from skills where deleted_at is null")).rows).toHaveLength(0);
    await expect(db.query("insert into tasks(user_id,title,skill_id) values($1,'AUDIT deleted link',$2)", [OWNER, SKILL])).rejects.toThrow("Referenced record must belong");
  });
});
