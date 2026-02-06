create table if not exists events (
  id uuid primary key,
  ts timestamptz not null,
  event_type text not null,
  confidence double precision not null,
  sources text[] not null default '{}',
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists idx_events_ts on events(ts desc);
create index if not exists idx_events_type on events(event_type);
