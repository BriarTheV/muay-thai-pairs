-- Database Schema for Muay Thai Matchmaker
-- Run this in your Supabase SQL Editor

-- Clubs table
CREATE TABLE IF NOT EXISTS clubs (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    contact_info JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Fighters table
CREATE TABLE IF NOT EXISTS fighters (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    gender TEXT CHECK (gender IN ('M', 'F')),
    dob DATE,
    weight_class TEXT,
    club_id INTEGER REFERENCES clubs(id),
    record_w INTEGER DEFAULT 0,
    record_l INTEGER DEFAULT 0,
    active_status BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Events table
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    date DATE NOT NULL,
    location TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Matches table
CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES events(id),
    fighter_red_id INTEGER REFERENCES fighters(id),
    fighter_blue_id INTEGER REFERENCES fighters(id),
    result TEXT CHECK (result IN ('red_win', 'blue_win', 'draw')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_fighters_club_id ON fighters(club_id);
CREATE INDEX IF NOT EXISTS idx_fighters_active ON fighters(active_status);
CREATE INDEX IF NOT EXISTS idx_matches_event_id ON matches(event_id);
CREATE INDEX IF NOT EXISTS idx_events_date ON events(date);

-- Row Level Security (RLS) policies
ALTER TABLE clubs ENABLE ROW LEVEL SECURITY;
ALTER TABLE fighters ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read/write all data
CREATE POLICY "Allow authenticated users to read clubs" ON clubs
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow authenticated users to insert clubs" ON clubs
    FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "Allow authenticated users to update clubs" ON clubs
    FOR UPDATE TO authenticated USING (true);

-- Similar policies for other tables...
-- (In a real app, you'd want more granular permissions)