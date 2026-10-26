# Electricity market model

## 🎯 Objective
Personal project to analyse and predict electricity market trends in France: consumption, day-ahead prices and generation mix. <br>
Projet d'analyse et prédiction des marchés de l'électricité en France.

## 🚀 Status
🚧 Phase 1 – learning prototypes (project scaffold done)

## 🧭 How the project is built
The project has two phases, with a deliberate split of work between me and the AI assistant.

### Phase 1 – Learn by hand (me)
I write the first versions myself, as single scripts or notebooks, to understand how each data source and technique actually works:
- one minimal API call per provider (RTE, ENTSO-E, Open-Meteo, Météo-France): auth, request, response shape, saving raw data
- first exploration and cleaning of the data in notebooks
- first simple forecasting experiments

These prototypes live in `notebooks/` and are intentionally small and disposable.

### Phase 2 – Industrialisation (AI assistant)
Once I understand a step, the AI assistant turns my prototype into reusable, tested code in the `src/emm/` package:
- API clients with retry, rate limiting and incremental downloads
- ETL pipeline: cleaning, UTC harmonisation, merging, calendar features and derived metrics
- model training and evaluation framework (baselines, ML, deep learning) with leakage-free time-series validation
- a CLI to rerun everything reproducibly

I review the generated code against my prototypes.

## 🏗️ Architecture
Three decoupled stages:
1. **Ingestion** – download raw data from RTE, ENTSO-E and weather APIs (Open-Meteo, Météo-France) into `data/raw/`
2. **ETL & metrics** – clean (`data/interim/`), merge and derive insights such as residual load, thermo-sensitivity and price spreads (`data/processed/`)
3. **Modelling** – forecast consumption, price and generation mix; compare baselines, ML (Ridge, LightGBM) and DL (LSTM, Transformer)

Full details, folder layout and milestones: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

```
configs/    sources, weather locations, model settings (yaml)
data/       raw → interim → processed (not versioned)
docs/       architecture
notebooks/  phase 1 prototypes and analysis
src/emm/    ingestion, etl, features, models, evaluation (phase 2)
tests/
```

## 🛠️ Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,ml]"      # add ",dl" for PyTorch
cp .env.example .env            # then fill in your API credentials
```
Credentials needed: RTE (client id/secret), ENTSO-E (token), Météo-France (API key). Open-Meteo needs none.

## 🛠️ Technologies
- Python 3.12+, pandas, DuckDB/Parquet, scikit-learn, LightGBM, PyTorch
- Dependencies are managed only in `pyproject.toml`

## 👤 Auteur
Florian Selot
