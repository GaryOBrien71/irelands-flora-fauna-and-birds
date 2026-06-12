-- Ireland's Flora, Fauna and Birds
-- Supabase setup SQL
-- Run this in Supabase SQL Editor.

create extension if not exists "pgcrypto";

create table if not exists public.species (
    id text primary key,
    common_name text not null,
    scientific_name text,
    kingdom_group text not null,
    category text,
    subcategory text,
    season text,
    habitat text,
    description text,
    edibility text,
    medicinal_uses text,
    warning text,
    conservation_status text,
    image_search text,
    image_url text,
    created_at timestamptz default now()
);

create table if not exists public.species_user_state (
    species_id text primary key references public.species(id) on delete cascade,
    spotted boolean default false,
    spotted_at timestamptz,
    notes text default '',
    updated_at timestamptz default now()
);

create table if not exists public.species_photos (
    id uuid primary key default gen_random_uuid(),
    species_id text references public.species(id) on delete cascade,
    photo_url text not null,
    caption text default '',
    file_name text default '',
    created_at timestamptz default now()
);

-- Create a public storage bucket for user photos.
insert into storage.buckets (id, name, public)
values ('nature-photos', 'nature-photos', true)
on conflict (id) do nothing;

-- For a private Streamlit app using a service-role key, RLS can stay enabled
-- because the service-role key bypasses RLS. If you use an anon key, add proper auth/RLS policies.
alter table public.species enable row level security;
alter table public.species_user_state enable row level security;
alter table public.species_photos enable row level security;

-- Simple read policies for anon/public read access if you decide to use anon key.
-- Comment these out if you want stricter access and only use service role.
drop policy if exists "Allow public read species" on public.species;
create policy "Allow public read species"
on public.species for select
using (true);

drop policy if exists "Allow public read user state" on public.species_user_state;
create policy "Allow public read user state"
on public.species_user_state for select
using (true);

drop policy if exists "Allow public read photos" on public.species_photos;
create policy "Allow public read photos"
on public.species_photos for select
using (true);

-- Storage policies. These are permissive for a password-protected family app.
-- For a public app, use Supabase Auth and tighten these.
drop policy if exists "Allow public photo reads" on storage.objects;
create policy "Allow public photo reads"
on storage.objects for select
using (bucket_id = 'nature-photos');

drop policy if exists "Allow public photo uploads" on storage.objects;
create policy "Allow public photo uploads"
on storage.objects for insert
with check (bucket_id = 'nature-photos');

drop policy if exists "Allow public photo updates" on storage.objects;
create policy "Allow public photo updates"
on storage.objects for update
using (bucket_id = 'nature-photos')
with check (bucket_id = 'nature-photos');
