-- ============================================
-- Cielo House — Supabase Database Schema
-- Run this in Supabase → SQL Editor
-- ============================================

-- Events Calendar
create table if not exists events (
  id uuid default gen_random_uuid() primary key,
  title text not null,
  location text,
  start_date date,
  end_date date,
  photo text,
  notes text,
  created_at timestamptz default now()
);

-- Blog Posts
create table if not exists blog_posts (
  id uuid default gen_random_uuid() primary key,
  title text not null,
  slug text unique,
  category text,
  status text default 'Draft',
  date date,
  excerpt text,
  image text,
  views integer default 0,
  content text,
  created_at timestamptz default now()
);

-- Testimonials
create table if not exists testimonials (
  id serial primary key,
  name text not null,
  company text not null,
  role text,
  highlight text,
  body text not null,
  visible boolean default true,
  sort_order integer default 0,
  created_at timestamptz default now()
);

-- FAQs
create table if not exists faqs (
  id serial primary key,
  question text not null,
  answer text not null,
  sort_order integer default 0,
  created_at timestamptz default now()
);

-- Subscribers
create table if not exists subscribers (
  id uuid default gen_random_uuid() primary key,
  email text unique not null,
  created_at timestamptz default now()
);

-- Analytics Stats
create table if not exists analytics (
  id serial primary key,
  sessions integer,
  sessions_pct numeric,
  visitors integer,
  visitors_pct numeric,
  clicks integer,
  forms integer,
  google_period text,
  gq1 jsonb,
  gq2 jsonb,
  gq3 jsonb,
  ai jsonb,
  updated_at timestamptz default now()
);

-- AI Knowledge Base
create table if not exists ai_knowledge (
  id serial primary key,
  profile text,
  qas jsonb default '[]',
  extra text,
  updated_at timestamptz default now()
);

-- Enable Row Level Security (keep data private)
alter table events enable row level security;
alter table blog_posts enable row level security;
alter table testimonials enable row level security;
alter table faqs enable row level security;
alter table subscribers enable row level security;
alter table analytics enable row level security;
alter table ai_knowledge enable row level security;

-- Public read access for testimonials (shown on website)
create policy "Public can read visible testimonials"
  on testimonials for select
  using (visible = true);

-- Public insert for subscribers (newsletter signup)
create policy "Anyone can subscribe"
  on subscribers for insert
  with check (true);

-- Anon key gets full access for dashboard (we'll secure with service role in production)
create policy "Anon full access events" on events for all using (true) with check (true);
create policy "Anon full access blog_posts" on blog_posts for all using (true) with check (true);
create policy "Anon full access testimonials all" on testimonials for all using (true) with check (true);
create policy "Anon full access faqs" on faqs for all using (true) with check (true);
create policy "Anon full access analytics" on analytics for all using (true) with check (true);
create policy "Anon full access ai_knowledge" on ai_knowledge for all using (true) with check (true);
create policy "Anon read subscribers" on subscribers for select using (true);
