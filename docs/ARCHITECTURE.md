# Plan: Electricity market model – architecture

## Context
Greenfield repo (only README, LICENSE, requirements.txt, .gitignore; Python 3.12, pandas/sklearn/plotly/jupyter already pinned). Goal: three decoupled stages —
1. **Ingestion**: API clients for RTE and weather, downloading raw data.
2. **ETL / features**: cleaning, harmonisation, derived metrics used by modelling.
3. **Modelling**: develop/test ML and DL models (consumption, day-ahead price, generation mix) for France.

Decisions: weather = Open-Meteo (primary) + Météo-France (cross-check); code = installable package `src/emm/` with thin notebooks; storage = layered Parquet + DuckDB; scope = France load, day-ahead price, generation mix.

## Implementation scope (approved narrowing)
Create ONLY: folder skeleton (with `.gitkeep` / `__init__.py`), config files, and the venv. No client/ETL/model code, no notebooks.
- `pyproject.toml` is the single dependency source; **delete `requirements.txt`**.
- Recreate `.venv` (Python 3.12) and `pip install -e ".[dev]"` from pyproject (runtime deps + `dev` extra: pytest, ruff).
- Single `.env.example` (prefixed keys: RTE_*, ENTSOE_TOKEN, METEOFRANCE_API_KEY); real `.env` and `data/` gitignored.
- `configs/{sources,locations,models}.yaml`, `.claude/privacy.md`, update README structure section.
- Empty package dirs under `src/emm/` (ingestion, etl, features, models, evaluation) with `__init__.py`; `notebooks/`, `tests/`, `data/{raw,interim,processed}`.
- Copy this architecture plan into the project as `docs/ARCHITECTURE.md` (the layout, stage details, milestones).
- Schema = folders + config files + environment only. Commit only if asked.

## Proposed layout
```
Electricity_market_model/
├── pyproject.toml            # package `emm`, deps, ruff/pytest config
├── .env.example              # RTE_CLIENT_ID/SECRET, ENTSOE_TOKEN, METEOFRANCE_KEY (real .env gitignored)
├── configs/
│   ├── sources.yaml          # datasets, endpoints, units, start dates, chunk sizes
│   ├── locations.yaml        # weather points (population-weighted cities: Paris, Lyon, Marseille, Lille, Toulouse, Bordeaux…)
│   └── models.yaml           # targets, horizons, feature sets, hyper-params
├── data/                     # gitignored
│   ├── raw/{rte,entsoe,openmeteo,meteofrance}/   # immutable, as downloaded (JSON/CSV → Parquet, partitioned by month)
│   ├── interim/              # cleaned, typed, UTC-indexed, one table per source
│   └── processed/            # model-ready feature tables + metrics
├── src/emm/
│   ├── config.py             # load yaml + env, path helpers
│   ├── ingestion/
│   │   ├── base.py           # BaseClient: auth, retry/backoff, rate-limit, chunked date ranges, incremental ("only fetch missing")
│   │   ├── rte.py            # OAuth2 client: consumption (short term, actual), generation per type, eCO2mix
│   │   ├── entsoe.py         # day-ahead prices FR (+ later neighbours), cross-border flows
│   │   ├── openmeteo.py      # historical + forecast: temp, wind, irradiance, cloud, precipitation
│   │   └── meteofrance.py    # observations/forecast for cross-check
│   ├── etl/
│   │   ├── clean.py          # tz → UTC, dedupe, dtype, resample to common freq (15/30 min → hourly), gap/outlier flagging
│   │   ├── merge.py          # join load + generation + price + weather on a single hourly UTC index
│   │   ├── calendar.py       # French holidays, school holidays, DST-aware hour/dow, bridge days
│   │   └── metrics.py        # derived insights (see below)
│   ├── features/
│   │   └── build.py          # lags, rolling stats, weather-lag, calendar encodings → data/processed
│   ├── models/
│   │   ├── base.py           # common fit/predict/save interface
│   │   ├── baselines.py      # seasonal naive (t-24h / t-168h), persistence
│   │   ├── ml.py             # Ridge/ElasticNet, LightGBM/XGBoost
│   │   └── dl.py             # LSTM/GRU, TCN/N-BEATS style, Transformer (PyTorch)
│   ├── evaluation/
│   │   ├── cv.py             # expanding-window time-series CV (no shuffling, no leakage)
│   │   └── scoring.py        # MAE, RMSE, MAPE/sMAPE, skill vs seasonal-naive; peak-hour & price-spike metrics
│   └── cli.py                # `emm ingest|etl|features|train` (Typer) for reproducible runs
├── notebooks/
│   ├── 00_data_sources_check.ipynb     # sanity call to each API
│   ├── 10_ingestion_demo.ipynb
│   ├── 20_eda_cleaning.ipynb
│   ├── 30_metrics_insights.ipynb
│   ├── 40_baselines.ipynb
│   ├── 50_ml_load.ipynb  / 51_ml_price.ipynb
│   ├── 60_dl_load.ipynb  / 61_dl_price.ipynb
│   └── 90_model_comparison.ipynb
├── tests/                    # unit tests with recorded API fixtures (no live calls)
└── .claude/privacy.md        # secrets/data paths definition for data-privacy-gate
```

## Stage details

**1. Ingestion** – every client extends `BaseClient`; writes raw files untouched to `data/raw/<source>/<dataset>/YYYY-MM.parquet` plus a manifest (fetched range, timestamp, row count) so reruns are incremental and idempotent. Secrets only via env. Live calls only in notebooks 00/10 and the CLI, never in tests.

**2. ETL & metrics** – raw → interim (typed, UTC, deduped, gaps flagged not silently filled) → processed (merged hourly table). Metrics module produces the reusable insights the models consume:
- Residual load = load − (wind + solar); renewable share; nuclear availability proxy
- Thermo-sensitivity (MW/°C below ~15 °C), heating/cooling degree hours
- Load ramp rates, peak/off-peak spreads, daily load factor
- Price spreads, negative-price hours, price volatility, merit-order proxy (price vs residual load)
- Net import/export position (phase 2 with neighbours)

**3. Modelling** – same feature table feeds all models; targets: load (D+1 hourly), day-ahead price (D+1 hourly), generation by source. Ladder: seasonal-naive → linear → gradient boosting → LSTM/GRU/Transformer. Strict chronological split (e.g. train ≤ 2022, val 2023, test 2024+), expanding-window CV, forecasts must only use information available at gate closure (use *forecast* weather for target day, not observed). Results logged to `data/processed/experiments/` (parquet/CSV of metrics per run) and compared in notebook 90.

## Build order (suggested milestones)
1. Scaffold: `pyproject.toml`, dirs, config loader, `.env.example`, `.claude/privacy.md`, gitignore `data/` & `.env`.
2. Open-Meteo + RTE clients (OAuth2) with incremental raw download; ENTSO-E prices.
3. Clean + merge + calendar; metrics; EDA notebooks.
4. Baselines + CV/scoring harness, then ML (LightGBM) for load and price.
5. DL models (add `torch`), comparison notebook; Météo-France cross-check later.

Optional extras in pyproject (`ml`, `dl`, `dev`); torch/lightgbm are not installed by default. Planned additions: `pyarrow`, `duckdb`, `pyyaml` (present), `python-dotenv`, `tenacity`, `typer`, `lightgbm`, `torch`, `pytest`, `ruff`, `holidays`.

## Verification
- `pytest` on cleaning/metrics/CV with small fixtures (e.g. DST transition days, missing hours, duplicated timestamps).
- Notebook 00 returns a non-empty frame from each API; rerunning `emm ingest` fetches nothing new (idempotent).
- ETL output: continuous hourly UTC index, no duplicates, gap report empty or explained.
- Models: every model beats seasonal-naive on the validation window or is flagged; CV folds show no leakage (train end < test start).
- Before first push: run `data-privacy-gate` to confirm `.env` and `data/` are untracked.

## Open points to confirm later
- API access: RTE (data.rte-france.com app registration), ENTSO-E token request, Météo-France key — need to be created by you.
