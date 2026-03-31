-- ================================================================
-- IPL PERFORMANCE ANALYTICS — SQL QUERIES
-- Database: SQLite or PostgreSQL
-- Tables: matches, deliveries
-- Run after importing matches_clean.csv and deliveries_clean.csv
-- ================================================================


-- ────────────────────────────────────────────────────────────────
-- SETUP: Create Tables (SQLite syntax)
-- ────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY,
    season INTEGER,
    year INTEGER,
    date TEXT,
    city TEXT,
    venue TEXT,
    team1 TEXT,
    team2 TEXT,
    toss_winner TEXT,
    toss_decision TEXT,
    result TEXT,
    winner TEXT,
    win_by_runs INTEGER,
    win_by_wickets INTEGER,
    player_of_match TEXT,
    toss_win_match_win INTEGER
);

CREATE TABLE IF NOT EXISTS deliveries (
    match_id INTEGER,
    inning INTEGER,
    batting_team TEXT,
    bowling_team TEXT,
    over INTEGER,
    ball INTEGER,
    batsman TEXT,
    non_striker TEXT,
    bowler TEXT,
    batsman_runs INTEGER,
    extra_runs INTEGER,
    total_runs INTEGER,
    is_wicket INTEGER,
    dismissal_kind TEXT,
    player_dismissed TEXT,
    over_phase TEXT,
    is_boundary INTEGER,
    is_dot INTEGER,
    is_wicket_clean INTEGER
);


-- ────────────────────────────────────────────────────────────────
-- QUERY 1: Most Successful Teams (All Time)
-- ────────────────────────────────────────────────────────────────

SELECT
    winner AS team,
    COUNT(*) AS total_wins
FROM matches
WHERE winner IS NOT NULL
GROUP BY winner
ORDER BY total_wins DESC
LIMIT 10;


-- ────────────────────────────────────────────────────────────────
-- QUERY 2: Toss Decision — Does It Matter?
-- ────────────────────────────────────────────────────────────────

SELECT
    toss_decision,
    COUNT(*) AS matches_played,
    SUM(toss_win_match_win) AS toss_winner_also_won,
    ROUND(100.0 * SUM(toss_win_match_win) / COUNT(*), 1) AS win_pct
FROM matches
GROUP BY toss_decision;


-- ────────────────────────────────────────────────────────────────
-- QUERY 3: Top Run Scorers (All Time, min 500 balls)
-- ────────────────────────────────────────────────────────────────

SELECT
    batsman,
    SUM(batsman_runs) AS total_runs,
    COUNT(ball) AS balls_faced,
    SUM(is_boundary) AS boundaries,
    ROUND(100.0 * SUM(batsman_runs) / COUNT(ball), 1) AS strike_rate
FROM deliveries
GROUP BY batsman
HAVING balls_faced >= 500
ORDER BY total_runs DESC
LIMIT 15;


-- ────────────────────────────────────────────────────────────────
-- QUERY 4: Clutch Batters — Strike Rate in Death Overs (16-20)
-- ────────────────────────────────────────────────────────────────

SELECT
    batsman,
    SUM(batsman_runs) AS death_runs,
    COUNT(ball) AS death_balls,
    ROUND(100.0 * SUM(batsman_runs) / COUNT(ball), 1) AS death_sr
FROM deliveries
WHERE over_phase = 'Death'
GROUP BY batsman
HAVING death_balls >= 100
ORDER BY death_sr DESC
LIMIT 10;


-- ────────────────────────────────────────────────────────────────
-- QUERY 5: Most Economical Powerplay Bowlers
-- ────────────────────────────────────────────────────────────────

SELECT
    bowler,
    SUM(total_runs) AS runs_conceded,
    COUNT(ball) AS balls_bowled,
    SUM(is_wicket_clean) AS wickets,
    ROUND(6.0 * SUM(total_runs) / COUNT(ball), 2) AS economy
FROM deliveries
WHERE over_phase = 'Powerplay'
GROUP BY bowler
HAVING balls_bowled >= 120
ORDER BY economy ASC
LIMIT 10;


-- ────────────────────────────────────────────────────────────────
-- QUERY 6: Win Rate Chasing vs Defending (per team)
-- ────────────────────────────────────────────────────────────────

SELECT
    team,
    SUM(CASE WHEN chase_win = 1 THEN 1 ELSE 0 END) AS chase_wins,
    SUM(CASE WHEN defend_win = 1 THEN 1 ELSE 0 END) AS defend_wins,
    COUNT(*) AS total_wins
FROM (
    SELECT
        winner AS team,
        CASE WHEN win_by_wickets > 0 THEN 1 ELSE 0 END AS chase_win,
        CASE WHEN win_by_runs > 0 THEN 1 ELSE 0 END AS defend_win
    FROM matches
    WHERE winner IS NOT NULL
) sub
GROUP BY team
ORDER BY total_wins DESC;


-- ────────────────────────────────────────────────────────────────
-- QUERY 7: Season-wise Performance by Team
-- ────────────────────────────────────────────────────────────────

WITH team_games AS (
    SELECT year, team1 AS team FROM matches
    UNION ALL
    SELECT year, team2 AS team FROM matches
),
total_played AS (
    SELECT year, team, COUNT(*) AS played
    FROM team_games
    GROUP BY year, team
),
total_wins AS (
    SELECT year, winner AS team, COUNT(*) AS wins
    FROM matches
    WHERE winner IS NOT NULL
    GROUP BY year, winner
)
SELECT
    p.year,
    p.team,
    p.played,
    COALESCE(w.wins, 0) AS wins,
    ROUND(100.0 * COALESCE(w.wins, 0) / p.played, 1) AS win_pct
FROM total_played p
LEFT JOIN total_wins w ON p.year = w.year AND p.team = w.team
ORDER BY p.year DESC, win_pct DESC;


-- ────────────────────────────────────────────────────────────────
-- QUERY 8: Player of the Match — Most Awards
-- ────────────────────────────────────────────────────────────────

SELECT
    player_of_match,
    COUNT(*) AS potm_awards
FROM matches
WHERE player_of_match IS NOT NULL
GROUP BY player_of_match
ORDER BY potm_awards DESC
LIMIT 10;


-- ────────────────────────────────────────────────────────────────
-- QUERY 9: Best Venues for Chasing
-- ────────────────────────────────────────────────────────────────

SELECT
    venue,
    COUNT(*) AS total_matches,
    SUM(CASE WHEN win_by_wickets > 0 THEN 1 ELSE 0 END) AS chasing_wins,
    ROUND(100.0 * SUM(CASE WHEN win_by_wickets > 0 THEN 1 ELSE 0 END) / COUNT(*), 1) AS chase_win_pct
FROM matches
WHERE result = 'normal'
GROUP BY venue
HAVING total_matches >= 10
ORDER BY chase_win_pct DESC
LIMIT 10;


-- ────────────────────────────────────────────────────────────────
-- QUERY 10: Dot Ball % by Bowler (Middle Overs — Pressure Metric)
-- ────────────────────────────────────────────────────────────────

SELECT
    bowler,
    COUNT(ball) AS balls,
    SUM(is_dot) AS dot_balls,
    ROUND(100.0 * SUM(is_dot) / COUNT(ball), 1) AS dot_ball_pct
FROM deliveries
WHERE over_phase = 'Middle'
GROUP BY bowler
HAVING balls >= 150
ORDER BY dot_ball_pct DESC
LIMIT 10;
