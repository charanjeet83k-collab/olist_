# Python_Codes_App – Olist Brazilian E-Commerce (data analysis, EDA, dashboard web app)

| File | What it does |
|---|---|
| `olist_analysis.py` | Loads and validates the 9 CSV files, data-quality checks, builds order- and item-level tables, KPIs, EDA, charts (one file) |
| `eda_vscode.py` | EDA for VS Code: run the `# %%` cells one by one (tables and charts in the Interactive Window) |
| `app.py` | Streamlit dashboard with login: the same 5 pages as the Power BI report (Executive Overview, Sales & Product, Customers & Reviews, Delivery & Logistics, Payment & Geography) with sidebar filters, KPI cards and an insight on each page, plus a Data quality page |
| `VSCODE_GUIDE.md` | Step-by-step VS Code set-up and run guide |
| `tests/smoke_test.py` | Checks the app code and key KPIs without needing Streamlit |

## Run (in this order)
1. `pip install -r requirements.txt`
2. Set the folder with the nine CSV files: Windows `set OLIST_DATA_DIR=C:\path\to\csv` · Mac/Linux `export OLIST_DATA_DIR=/path/to/csv`
3. `python olist_analysis.py` (a few minutes) → `data/processed`, `reports/` (tables, `kpi_summary.json`, charts)
4. Login: set `APP_USER` and `APP_PASSWORD` (environment variables, or copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`)
5. `streamlit run app.py`
6. Optional: `python tests/smoke_test.py`

## KPI rules (same as the SQL views and the Power BI measures)
Sales KPIs exclude canceled and unavailable orders and orders without items. Item sales = SUM(price), freight excluded; payment total = SUM(payment_value) and is a different measure. Customers are counted with `customer_unique_id`. Delivery KPIs use delivered orders with a valid date sequence; late = delivered after the estimated timestamp. Reviews are averaged to one row per order. Geolocation is reduced to one row per ZIP.

## Results to expect
KPIs: 98,199 valid orders, item sales R$13,494,400.74, 96,096 unique customers, late deliveries 8.11%.

## Limits
No cost data (no profit). The app has been tested only with a Streamlit stand-in, not in a real Streamlit session, and is not deployed. Raw data is not included.
