# 🏏 IPL Performance Analytics Dashboard

> **Which teams and players win under pressure — and why?**

A full-stack data analytics project analyzing Indian Premier League (IPL) data from 2008–2024 using Python, SQL, and Power BI.

---

## 📌 Project Summary

This project explores IPL ball-by-ball data to uncover patterns in team performance, player contributions, and match outcomes. It demonstrates a complete analyst workflow — from raw data cleaning to interactive dashboards.

**Key Questions Answered:**
- Does winning the toss actually help win the match?
- Who are the most dangerous batters in death overs?
- Which bowlers are most economical in the powerplay?
- Can venue + toss data predict the match winner?

---

## 🗂️ Project Structure

```
ipl-analytics/
│
├── data/
│   ├── matches.csv              # Raw match data (from Kaggle)
│   ├── deliveries.csv           # Raw ball-by-ball data (from Kaggle)
│   ├── matches_clean.csv        # Cleaned by Python script
│   └── deliveries_clean.csv     # Cleaned by Python script
│
├── ipl_analysis.py              # Main Python script (cleaning + analysis + ML)
├── ipl_queries.sql              # 10 analytical SQL queries
│
├── outputs/
│   ├── top_batters.png          # Visualization: Top run scorers
│   └── toss_effect.png          # Visualization: Toss impact
│
├── IPL_Dashboard.pbix           # Power BI dashboard file
└── README.md
```

---

## 📦 Dataset

Download from Kaggle:
- [IPL Complete Dataset](https://www.kaggle.com/datasets/patrickb1912/ipl-complete-dataset-20082020)

Place `matches.csv` and `deliveries.csv` in the `data/` folder.

---

## ⚙️ Setup & Run

### 1. Install Python Dependencies

```bash
pip install pandas numpy matplotlib seaborn scikit-learn
```

### 2. Run the Analysis Script

```bash
python ipl_analysis.py
```

This will:
- Load and clean raw CSV files
- Save clean CSVs to `data/`
- Print analytical summaries in terminal
- Save visualizations to `outputs/`
- Run a logistic regression model to predict match winners

### 3. Load SQL Queries

Import `data/matches_clean.csv` and `data/deliveries_clean.csv` into SQLite or PostgreSQL, then run queries from `ipl_queries.sql`.

**With SQLite (quickest):**
```bash
sqlite3 ipl.db
.mode csv
.import data/matches_clean.csv matches
.import data/deliveries_clean.csv deliveries
.read ipl_queries.sql
```

### 4. Open Power BI Dashboard

Open `IPL_Dashboard.pbix` in Power BI Desktop.
- Connect to `matches_clean.csv` and `deliveries_clean.csv`
- Refresh data source

---

## 📊 Key Findings

| Question | Finding |
|---|---|
| Toss effect | Toss winners win ~51% of matches — minimal edge |
| Best death batter | Top SR players exceed 180 in overs 16–20 |
| Powerplay bowlers | Economy below 6 in powerplay is elite |
| Chase vs Defend | Teams win ~52% chasing at neutral venues |
| Win predictor | Toss + venue → ~54% accuracy (slight signal) |

---

## 🛠️ Tools Used

| Tool | Purpose |
|---|---|
| Python (pandas) | Data cleaning, feature engineering |
| Python (matplotlib/seaborn) | Visualizations |
| Python (scikit-learn) | Logistic regression model |
| SQL (SQLite) | Analytical queries |
| Power BI | Interactive dashboard |

---

## 💡 Potential Extensions

- Add player auction value analysis
- Build a team strength rating by season
- Predict win probability ball-by-ball using XGBoost
- Deploy as a Streamlit web app

---

## 👤 Author

**[Your Name]**
Data Analyst Portfolio Project
[LinkedIn] | [GitHub]
