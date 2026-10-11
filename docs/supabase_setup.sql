-- CivilEdu_AI：Supabase 資料表初始化
-- 在 Supabase 專案的 SQL Editor 貼上並執行一次即可。
-- 每一列的 data 欄位存放與本地 JSON 相同結構的內容：
--   units           ← units_db.json 的每個單元
--   student_records ← student_logs/班級_座號_姓名.json

create table if not exists public.units (
    id         text primary key,          -- 單元 id，例如 unit_897714b1
    data       jsonb not null,
    position   integer not null default 0 -- 教材清單的顯示順序
);

create table if not exists public.student_records (
    id         text primary key,          -- 班級_座號_姓名，例如 801_01_王小明
    data       jsonb not null,
    position   integer not null default 0
);

-- 開啟 RLS 且不建立任何 policy：公開的 anon / publishable 金鑰無法讀寫，
-- 只有放在 Streamlit Secrets 的 secret（service_role）金鑰能存取，學生個資不會外流。
alter table public.units enable row level security;
alter table public.student_records enable row level security;
