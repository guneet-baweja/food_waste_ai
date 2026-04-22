create table if not exists public.app_state (
  key text primary key,
  payload jsonb not null default '[]'::jsonb,
  updated_at timestamptz not null default timezone('utc', now())
);

insert into public.app_state (key, payload)
values
  ('users', '[]'::jsonb),
  ('donations', '[]'::jsonb),
  ('notifications', '[]'::jsonb),
  ('leaderboard', '[]'::jsonb),
  ('insurance', '[]'::jsonb),
  ('futures_market', '[]'::jsonb),
  ('carbon_credits', '[]'::jsonb)
on conflict (key) do nothing;

insert into storage.buckets (id, name, public)
values ('food-images', 'food-images', true)
on conflict (id) do nothing;

create policy if not exists "Public can read food images"
on storage.objects
for select
to public
using (bucket_id = 'food-images');
