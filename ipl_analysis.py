"""
IPL Performance Analytics - Data Cleaning & Analysis
=====================================================
Tools: Python (pandas, matplotlib, seaborn, sklearn)
Dataset: IPL Ball-by-Ball Data from Kaggle
         - matches.csv
         - deliveries.csv
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────
# PHASE 1: LOAD DATA
# ─────────────────────────────────────────────

def load_data():
    """Load raw IPL CSV files."""
    matches = pd.read_csv('data/matches.csv')
    deliveries = pd.read_csv('data/deliveries.csv')
    print(f"Matches loaded: {matches.shape}")
    print(f"Deliveries loaded: {deliveries.shape}")
    return matches, deliveries


# ─────────────────────────────────────────────
# PHASE 2: CLEAN DATA
# ─────────────────────────────────────────────

# Teams have changed names over the years — normalize them
TEAM_NAME_MAP = {
    'Delhi Daredevils': 'Delhi Capitals',
    'Kings XI Punjab': 'Punjab Kings',
    'Rising Pune Supergiants': 'Rising Pune Supergiant',
    'Deccan Chargers': 'Sunrisers Hyderabad',
}

def clean_matches(matches: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize match data."""
    df = matches.copy()

    # Fix team names
    for col in ['team1', 'team2', 'winner', 'toss_winner']:
        df[col] = df[col].replace(TEAM_NAME_MAP)

    # Parse date
    df['date'] = pd.to_datetime(df['date'], dayfirst=True)
    df['year'] = df['date'].dt.year

    # Drop rows with no result (abandoned matches etc.)
    df = df[df['result'] != 'no result'].reset_index(drop=True)

    # Binary: did toss winner also win the match?
    df['toss_win_match_win'] = (df['toss_winner'] == df['winner']).astype(int)

    print(f"Clean matches: {df.shape[0]} rows")
    return df


def clean_deliveries(deliveries: pd.DataFrame) -> pd.DataFrame:
    """Clean delivery-level data and engineer features."""
    df = deliveries.copy()

    # Fix team names in deliveries
    for col in ['batting_team', 'bowling_team']:
        df[col] = df[col].replace(TEAM_NAME_MAP)

    # Over phase: Powerplay (1-6), Middle (7-15), Death (16-20)
    df['over_phase'] = pd.cut(
        df['over'],
        bins=[0, 6, 15, 20],
        labels=['Powerplay', 'Middle', 'Death']
    )

    # Is it a boundary?
    df['is_boundary'] = df['batsman_runs'].isin([4, 6]).astype(int)

    # Is it a dot ball?
    df['is_dot'] = (df['total_runs'] == 0).astype(int)

    # Is it a wicket (legitimate)?
    df['is_wicket_clean'] = (
        df['is_wicket'] == 1) & (
        ~df['dismissal_kind'].isin(['run out', 'retired hurt', 'obstructing the field'])
    )

    print(f"Clean deliveries: {df.shape[0]} rows")
    return df


# ─────────────────────────────────────────────
# PHASE 3: ANALYSIS FUNCTIONS
# ─────────────────────────────────────────────

def toss_effect(matches: pd.DataFrame):
    """Does winning the toss help win the match?"""
    effect = matches.groupby('toss_decision')['toss_win_match_win'].agg(['mean', 'count'])
    effect.columns = ['Win Rate', 'Matches']
    effect['Win Rate'] = (effect['Win Rate'] * 100).round(1)
    print("\n📊 Toss Effect on Match Outcome:")
    print(effect)

    overall = matches['toss_win_match_win'].mean() * 100
    print(f"\nOverall: Toss winner wins {overall:.1f}% of matches")
    return effect


def top_batters(deliveries: pd.DataFrame, top_n: int = 10):
    """Top run scorers with strike rate."""
    stats = deliveries.groupby('batter').agg(
        runs=('batsman_runs', 'sum'),
        balls=('ball', 'count'),
        boundaries=('is_boundary', 'sum')
    ).reset_index()

    stats['strike_rate'] = (stats['runs'] / stats['balls'] * 100).round(1)
    stats = stats[stats['balls'] >= 500]  # min 500 balls faced
    stats = stats.sort_values('runs', ascending=False).head(top_n)

    print(f"\n🏏 Top {top_n} Run Scorers (min 500 balls):")
    print(stats[['batter', 'runs', 'balls', 'strike_rate', 'boundaries']].to_string(index=False))
    return stats


def death_over_batters(deliveries: pd.DataFrame, top_n: int = 10):
    """Most dangerous batters in death overs (16-20)."""
    death = deliveries[deliveries['over_phase'] == 'Death']
    stats = death.groupby('batter').agg(
        runs=('batsman_runs', 'sum'),
        balls=('ball', 'count')
    ).reset_index()
    stats['strike_rate'] = (stats['runs'] / stats['balls'] * 100).round(1)
    stats = stats[stats['balls'] >= 100].sort_values('strike_rate', ascending=False).head(top_n)

    print(f"\n💀 Top Death-Over Batters (SR, min 100 balls):")
    print(stats[['batter', 'runs', 'balls', 'strike_rate']].to_string(index=False))
    return stats


def powerplay_bowlers(deliveries: pd.DataFrame, top_n: int = 10):
    """Most economical bowlers in powerplay."""
    pp = deliveries[deliveries['over_phase'] == 'Powerplay']
    stats = pp.groupby('bowler').agg(
        runs=('total_runs', 'sum'),
        balls=('ball', 'count'),
        wickets=('is_wicket_clean', 'sum')
    ).reset_index()
    stats['economy'] = (stats['runs'] / (stats['balls'] / 6)).round(2)
    stats = stats[stats['balls'] >= 120].sort_values('economy').head(top_n)

    print(f"\n🎯 Most Economical Powerplay Bowlers:")
    print(stats[['bowler', 'runs', 'balls', 'wickets', 'economy']].to_string(index=False))
    return stats


def team_win_rate_by_season(matches: pd.DataFrame):
    """Calculate win rate per team per season."""
    # Count total games played
    team_games = pd.concat([
        matches[['year', 'team1']].rename(columns={'team1': 'team'}),
        matches[['year', 'team2']].rename(columns={'team2': 'team'})
    ])
    total = team_games.groupby(['year', 'team']).size().reset_index(name='played')

    wins = matches.groupby(['year', 'winner']).size().reset_index(name='wins')
    wins = wins.rename(columns={'winner': 'team'})

    merged = total.merge(wins, on=['year', 'team'], how='left').fillna(0)
    merged['win_rate'] = (merged['wins'] / merged['played'] * 100).round(1)

    return merged


# ─────────────────────────────────────────────
# PHASE 4: PREDICT MATCH WINNER (Logistic Regression)
# ─────────────────────────────────────────────

def predict_winner(matches: pd.DataFrame):
    """Simple logistic regression: can toss + venue predict the winner?"""
    df = matches.dropna(subset=['winner']).copy()

    # Encode features
    df['toss_chose_bat'] = (df['toss_decision'] == 'bat').astype(int)
    df['toss_winner_is_team1'] = (df['toss_winner'] == df['team1']).astype(int)
    df['winner_is_team1'] = (df['winner'] == df['team1']).astype(int)

    venue_dummies = pd.get_dummies(df['venue'], prefix='venue', drop_first=True)
    X = pd.concat([
        df[['toss_chose_bat', 'toss_winner_is_team1']],
        venue_dummies
    ], axis=1)
    y = df['winner_is_team1']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = LogisticRegression(max_iter=500)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    acc = accuracy_score(y_test, preds)
    print(f"\n🤖 Logistic Regression Accuracy: {acc*100:.1f}%")
    print("(Baseline: ~50% — any above this means signal exists)")
    print("\nClassification Report:")
    print(classification_report(y_test, preds, target_names=['Team2 Wins', 'Team1 Wins']))
    return model


# ─────────────────────────────────────────────
# PHASE 5: VISUALIZATIONS
# ─────────────────────────────────────────────

def plot_top_batters(stats: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = sns.color_palette("YlOrRd", len(stats))
    bars = ax.barh(stats['batter'], stats['runs'], color=colors)
    ax.set_xlabel('Total Runs', fontsize=12)
    ax.set_title('Top IPL Run Scorers (All Seasons)', fontsize=14, fontweight='bold')
    ax.invert_yaxis()
    for bar, sr in zip(bars, stats['strike_rate']):
        ax.text(bar.get_width() + 50, bar.get_y() + bar.get_height()/2,
                f'SR: {sr}', va='center', fontsize=9)
    plt.tight_layout()
    plt.savefig('outputs/top_batters.png', dpi=150)
    plt.close()
    print("✅ Saved: outputs/top_batters.png")


def plot_toss_effect(effect: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(7, 5))
    colors = ['#2196F3', '#FF5722']
    bars = ax.bar(effect.index, effect['Win Rate'], color=colors, width=0.5)
    ax.axhline(50, linestyle='--', color='gray', label='50% baseline')
    ax.set_ylabel('Win Rate (%)')
    ax.set_title('Does Winning Toss Help Win the Match?', fontsize=13, fontweight='bold')
    ax.set_ylim(0, 70)
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f"{bar.get_height():.1f}%", ha='center', fontweight='bold')
    ax.legend()
    plt.tight_layout()
    plt.savefig('outputs/toss_effect.png', dpi=150)
    plt.close()
    print("✅ Saved: outputs/toss_effect.png")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == '__main__':
    import os
    os.makedirs('outputs', exist_ok=True)

    print("=" * 55)
    print("   IPL PERFORMANCE ANALYTICS — PYTHON ANALYSIS")
    print("=" * 55)

    matches, deliveries = load_data()
    matches = clean_matches(matches)
    deliveries = clean_deliveries(deliveries)

    # Save clean CSVs for SQL import
    matches.to_csv('data/matches_clean.csv', index=False)
    deliveries.to_csv('data/deliveries_clean.csv', index=False)
    print("\n✅ Clean CSVs saved to data/")

    # Run analyses
    effect = toss_effect(matches)
    top_batters(deliveries)
    death_over_batters(deliveries)
    powerplay_bowlers(deliveries)
    predict_winner(matches)

    # Save visualizations
    batter_stats = top_batters(deliveries)
    plot_top_batters(batter_stats)
    plot_toss_effect(effect)

    print("\n✅ All analysis complete!")
