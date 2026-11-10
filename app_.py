"""
OLIST BRAZILIAN E-COMMERCE - STREAMLIT DASHBOARD (one file)
Same five pages as the Power BI report: Executive Overview | Sales & Product | Customers & Reviews | Delivery & Logistics | Payment & Geography,
plus a data-quality page. Filters (slicers) are in the sidebar and apply to all five dashboard pages.
Run:    streamlit run app.py
Login:  APP_USER and APP_PASSWORD (environment variables or .streamlit/secrets.toml). No password is stored in the code.
Needs:  python olist_analysis.py
"""
import hmac, json, os
import numpy as np, pandas as pd, streamlit as st
from olist_analysis import PROCESSED_DIR, REPORTS_DIR

st.set_page_config(page_title="Olist dashboard", page_icon=":bar_chart:", layout="wide")
TEAL, AMBER = "#348E90", "#D98E1F"
st.markdown("""<style>
.block-container{padding-top:1rem;padding-bottom:1rem}
[data-testid=stSidebar]{background:#E3F1F1}
.hdr{background:linear-gradient(90deg,#1F6F72,#348E90);color:#fff;padding:14px 22px;border-radius:12px;border-bottom:4px solid #D98E1F;margin-bottom:12px}
.hdr h2{margin:0;color:#fff;font-size:26px}.hdr p{margin:2px 0 0 0;color:#E3F1F1;font-size:13px}
.kpi{background:#fff;border-radius:10px;padding:10px 14px;border-left:5px solid #348E90;box-shadow:0 1px 5px rgba(0,0,0,.13)}
.kpi .l{font-size:12px;color:#6B6B6B}.kpi .v{font-size:25px;font-weight:700;color:#1F6F72}
.ins{background:#FFF4DC;border-left:5px solid #D98E1F;border-radius:6px;padding:8px 12px;font-size:14px;margin-top:6px}
</style>""", unsafe_allow_html=True)

# ---------------------------------------------------------------- login
def credentials():
    try:
        return st.secrets["APP_USER"], st.secrets["APP_PASSWORD"]
    except Exception:
        return os.environ.get("APP_USER"), os.environ.get("APP_PASSWORD")

def require_login():
    user, pwd = credentials()
    if not user or not pwd:
        st.error("Login is not configured. Set APP_USER and APP_PASSWORD (see README)."); st.stop()
    if st.session_state.get("auth_ok"):
        return
    st.markdown('<div class="hdr"><h2>Olist analytics</h2><p>Please sign in</p></div>', unsafe_allow_html=True)
    u = st.text_input("User ID"); p = st.text_input("Password", type="password")
    if st.button("Sign in"):
        if hmac.compare_digest(u, user) and hmac.compare_digest(p, pwd):
            st.session_state["auth_ok"] = True; st.rerun()
        else:
            st.error("Wrong user ID or password.")
    st.stop()

# ---------------------------------------------------------------- data and helpers
@st.cache_data
def load_orders():
    o = pd.read_csv(PROCESSED_DIR / "order_level.csv.gz", parse_dates=["order_purchase_timestamp"]); o["month_no"] = o.order_purchase_timestamp.dt.month; return o

@st.cache_data
def load_items():
    return pd.read_csv(PROCESSED_DIR / "item_level.csv.gz", parse_dates=["order_purchase_timestamp"])

@st.cache_data
def load_payments():
    return pd.read_csv(PROCESSED_DIR / "payment_level.csv.gz")

def header(title, sub):
    st.markdown(f'<div class="hdr"><h2>{title}</h2><p>{sub}</p></div>', unsafe_allow_html=True)

def kpis(items):
    for col, (label, value) in zip(st.columns(len(items)), items):
        col.markdown(f'<div class="kpi"><div class="l">{label}</div><div class="v">{value}</div></div>', unsafe_allow_html=True)
    st.write("")

def panel(title):
    box = st.container(border=True); box.markdown(f"**{title}**"); return box

def insight(text):
    st.markdown(f'<div class="ins"><b>Insight:</b> {text}</div>', unsafe_allow_html=True)

R = lambda x: f"R$ {x:,.0f}"; P = lambda x: f"{100 * x:.2f}%"; N = lambda x: f"{x:,.0f}"; D = lambda x: f"{x:,.2f}"

# ---------------------------------------------------------------- dashboard pages (filters are applied before these run)

def page_home(fo, fi, fp):
    header("Welcome to Olist Analytics",
           "Brazilian E-Commerce Marketplace | Business Intelligence Dashboard")

    st.markdown("""
    ## About Olist

    **Olist** is a Brazilian e-commerce marketplace platform
    that connects independent sellers with customers.

    This dashboard analyses the public Olist Brazilian
    E-Commerce dataset to understand sales, customers,
    products, payments, reviews and delivery operations.

    The analysis combines nine source tables:
    - Orders and order items
    - Customers and sellers
    - Products and product categories
    - Payments and reviews
    - Geolocation

    ## Explore the Dashboard

    - Executive Overview: Business performance and KPIs.
    - Sales & Product: Category and seller performance.
    - Customers & Reviews: Customer behaviour and satisfaction.
    - Delivery & Logistics: Delivery performance and delays.
    - Payment & Geography: Payment methods and locations.
    - Predictive Model: Late-delivery risk estimation.
    """)

    st.info("Select a dashboard page from the left sidebar to begin.")
def page_Executive_Overview(fo, fi, fp):
    header("Executive Overview", "Business health at a glance")
    s = fo[fo.is_sales_order]; si = fi[fi.order_id.isin(s.order_id)]
    kpis([("Orders (valid)", N(len(s))), ("Item sales", R(s.item_sales.sum())), ("Unique customers", N(fo.customer_unique_id.nunique())), ("Active sellers", N(si.seller_id.nunique())), ("Avg review score", D(fo.review_score.mean()) if fo.review_score.notna().any() else "-")])
    m = s.groupby("purchase_month").agg(orders=("order_id", "count"), item_sales=("item_sales", "sum")); a, b = st.columns(2)
    with a.container(border=True): st.markdown("**Item sales per month (R$)**"); st.line_chart(m.item_sales, color=TEAL)
    with b.container(border=True): st.markdown("**Orders per month**"); st.bar_chart(m.orders, color=AMBER)
    a, b, c = st.columns(3); cat = si.groupby("category").price.sum().nlargest(10).sort_values()
    with a.container(border=True): st.markdown("**Top 10 categories by item sales**"); st.bar_chart(cat, horizontal=True, color=TEAL)
    with b.container(border=True): st.markdown("**Valid orders by customer state**"); st.bar_chart(s.groupby("customer_state").size().sort_values(ascending=False), color=TEAL)
    with c.container(border=True): st.markdown("**Orders by status**"); st.bar_chart(fo.order_status.value_counts(), color=AMBER)
    if len(m) and len(cat): insight(f"Item sales peak in {m.item_sales.idxmax()} ({R(m.item_sales.max())}). The top category, {cat.index[-1]}, holds {100 * cat.iloc[-1] / si.price.sum():.1f}% of item sales in this selection.")

def page_sales(fo, fi, fp):
    header("Sales & Product Performance", "Categories, sellers, price and freight (canceled and unavailable orders excluded)")
    si = fi[fi.order_id.isin(fo[fo.is_sales_order].order_id)]
    if si.empty: st.warning("No items in this selection."); return
    kpis([("Item sales", R(si.price.sum())), ("Items sold", N(len(si))), ("Avg item price", D(si.price.mean())), ("Avg freight per item", D(si.freight_value.mean())), ("Freight share of item sales", P(si.freight_value.sum() / si.price.sum()))])
    a, b = st.columns(2); cat = si.groupby("category").price.sum().sort_values(ascending=False)
    with a.container(border=True): st.markdown("**Top 10 categories by item sales (R$)**"); st.bar_chart(cat.head(10).sort_values(), horizontal=True, color=TEAL)
    with b.container(border=True): st.markdown("**Category share of item sales (top 15)**"); st.dataframe((100 * cat / cat.sum()).head(15).round(2).rename("share %"), use_container_width=True)
    a, b = st.columns(2); sel = si.groupby("seller_id").price.sum().sort_values(ascending=False)
    with a.container(border=True): st.markdown("**Top 10 sellers by item sales (R$)**"); st.bar_chart(sel.head(10).sort_values(), horizontal=True, color=AMBER)
    with b.container(border=True):
        st.markdown("**Monthly item sales by year (R$)**"); st.line_chart(si.assign(y=si.order_purchase_timestamp.dt.year, m=si.order_purchase_timestamp.dt.month).groupby(["m", "y"]).price.sum().unstack())
    insight(f"{len(sel):,} sellers sold items; the top 10 hold {100 * sel.head(10).sum() / sel.sum():.1f}% of item sales and {int((100 * sel.cumsum() / sel.sum() < 50).sum() + 1)} sellers generate half of them.")

def page_customers(fo, fi, fp):
    header("Customers & Reviews", "Who the customers are and how satisfied they are")
    per = fo.groupby("customer_unique_id").order_id.nunique(); rv = fo.review_score.dropna()
    kpis([("Unique customers", N(len(per))), ("Repeat customer rate", P((per > 1).mean())), ("Avg review score", D(rv.mean()) if len(rv) else "-"), ("% orders scoring 4-5", P((rv >= 4).mean()) if len(rv) else "-"), ("% orders scoring 1-2", P((rv <= 2).mean()) if len(rv) else "-")])
    a, b = st.columns(2)
    with a.container(border=True): st.markdown("**Order-level review score (rounded)**"); st.bar_chart(rv.round().astype(int).value_counts().sort_index(), color=AMBER)
    with b.container(border=True): st.markdown("**Average review score per month**"); st.line_chart(fo.groupby("purchase_month").review_score.mean(), color=TEAL)
    a, b = st.columns(2)
    with a.container(border=True): st.markdown("**Unique customers by state**"); st.bar_chart(fo.groupby("customer_state").customer_unique_id.nunique().sort_values(ascending=False), color=TEAL)
    with b.container(border=True): st.markdown("**One-time vs repeat customers**"); st.bar_chart(pd.Series({"One-time": int((per == 1).sum()), "Repeat": int((per > 1).sum())}), color=AMBER)
    insight(f"{100 * (per > 1).mean():.2f}% of customers in this selection ordered more than once; {100 * (rv <= 2).mean():.2f}% of reviewed orders scored 1 or 2." if len(rv) else "No reviews in this selection.")

def page_delivery(fo, fi, fp):
    header("Delivery & Logistics", "Delivered orders with a valid date sequence; late = delivered after the estimated date")
    v = fo[fo.valid_delivery]
    if v.empty: st.warning("No delivered orders in this selection."); return
    late = v[v.is_late == 1]
    kpis([("Avg delivery days", D(v.delivery_days.mean())), ("Avg promised days", D(v.estimated_days.mean())), ("On-time delivery", P(1 - v.is_late.mean())), ("Late delivery", P(v.is_late.mean())), ("Avg delay (late orders), days", D(late.delay_days.mean()) if len(late) else "-")])
    a, b = st.columns(2)
    with a.container(border=True): st.markdown("**Average delivery days by customer state**"); st.bar_chart(v.groupby("customer_state").delivery_days.mean().sort_values(), color=TEAL)
    with b.container(border=True): st.markdown("**Late deliveries % per month**"); st.line_chart(100 * v.groupby("purchase_month").is_late.mean(), color=AMBER)
    a, b = st.columns(2)
    with a.container(border=True): st.markdown("**Actual vs promised delivery days per month**"); st.line_chart(v.groupby("purchase_month")[["delivery_days", "estimated_days"]].mean())
    d = v.dropna(subset=["review_score"]).copy(); d["bucket"] = pd.cut(d.delay_days, [-1e9, 0, 3, 7, 1e9], labels=["on time or early", "1-3 days late", "4-7 days late", "over 7 days late"])
    sc = d.groupby("bucket", observed=True).review_score.mean()
    with b.container(border=True): st.markdown("**Average review score by delay**"); st.bar_chart(sc, color="#4A6F8A")
    if len(sc) == 4: insight(f"Orders delivered on time score {sc.iloc[0]:.2f} on average and orders more than 7 days late score {sc.iloc[3]:.2f}. This is an observed association; the data cannot show why.")

def page_payment(fo, fi, fp):
    header("Payment & Geographic Insights", "How customers pay and where they are (payment total includes freight and covers all orders with payments)")
    if fp.empty: st.warning("No payments in this selection."); return
    val = fp.groupby("payment_type").payment_value.sum().sort_values(ascending=False); s = fo[fo.is_sales_order]
    kpis([("Payment total", R(fp.payment_value.sum())), ("Avg payment per order", D(fp.payment_value.sum() / fp.order_id.nunique())), ("Credit-card share of value", P(val.get("credit_card", 0) / val.sum())), ("Avg instalments", D(fp.payment_installments.mean())), ("Cities served", N(fo.customer_city.nunique()))])
    a, b = st.columns(2)
    with a.container(border=True): st.markdown("**Payment value by payment type (R$)**"); st.bar_chart(val, color=TEAL)
    with b.container(border=True): st.markdown("**Credit-card payments by number of instalments**"); st.bar_chart(fp[fp.payment_type == "credit_card"].payment_installments.value_counts().sort_index(), color=AMBER)
    a, b = st.columns(2); bystate = fp.merge(fo[["order_id", "customer_state"]], on="order_id").groupby("customer_state").payment_value.sum().sort_values(ascending=False)
    with a.container(border=True): st.markdown("**Payment total by customer state (R$)**"); st.bar_chart(bystate, color=TEAL)
    with b.container(border=True): st.markdown("**Top 10 cities by valid orders**"); st.bar_chart(s.groupby("customer_city").size().nlargest(10).sort_values(), horizontal=True, color=AMBER)
    insight(f"Credit card carries {100 * val.get('credit_card', 0) / val.sum():.1f}% of payment value in this selection; {bystate.index[0]} has the largest payment total.")
@st.cache_resource
def fit_late_delivery_model(data):
    """Fit the notebook's explanatory logistic-regression model on delivered orders."""
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression

    d = data.copy()
    # The outcome is observable only for delivered orders with a valid delivery date.
    d = d[d.valid_delivery].copy()
    d = d[d.is_late.notna()].copy()
    d["dist_1000km"] = d["distance_km"] / 1000
    d["value_100"] = d["item_sales"] / 100
    d["freight_10"] = d["freight"] / 10
    d["peak_month"] = d["month_no"].isin([2, 3, 11]).astype(int)
    d["same_state"] = d["same_state"].fillna(0)
    features = ["dist_1000km", "same_state", "estimated_days", "n_items",
                "value_100", "freight_10", "peak_month"]
    d = d.replace([np.inf, -np.inf], np.nan).dropna(subset=["is_late"])
    X = d[features].astype(float)
    y = d["is_late"].astype(int)
    if len(d) < 100 or y.nunique() < 2:
        raise ValueError("There are not enough valid delivered orders or both outcome classes to fit the model.")
    model = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("logit", LogisticRegression(max_iter=2000, class_weight=None))
    ])
    model.fit(X, y)
    return model, d, features

def page_predictive(fo, fi, fp):
    header("Predictive Model – Late Delivery Risk",
           "Logistic regression based on the late-delivery analysis notebook")
    st.markdown("""
    This model estimates the probability that an order will arrive after its estimated
    delivery date. It uses order characteristics available at purchase time and learns
    patterns from historical delivered orders. It is an **indicative risk estimate**, not
    a guarantee or a live carrier forecast.
    """)
    try:
        model, train, features = fit_late_delivery_model(load_orders())
    except Exception as e:
        st.error(f"Could not train the predictive model: {e}")
        st.info("Run `python olist_analysis.py build` first and check that the processed order-level data is available.")
        return

    n = len(train)
    late_rate = train.is_late.mean()
    st.caption(f"Training population: {n:,} delivered orders with valid delivery dates. "
               f"Observed late-delivery rate: {late_rate:.1%}. "
               "The model is fitted on historical data; no independent test split is used.")

    # Risk groups and model fit
    train = train.copy()
    X = train[features].astype(float).replace([np.inf, -np.inf], np.nan)
    X = pd.DataFrame(model.named_steps["imputer"].transform(X), columns=features, index=train.index)
    train["predicted_risk"] = model.predict_proba(train[features].astype(float))[:, 1]
    train["risk_group"] = pd.qcut(train.predicted_risk.rank(method="first"), 5,
        labels=["1 Lowest", "2 Low", "3 Middle", "4 High", "5 Highest"])
    groups = train.groupby("risk_group", observed=True).agg(
        orders=("is_late", "size"),
        predicted_late=("predicted_risk", "mean"),
        actual_late=("is_late", "mean")).reset_index()
    a, b, c = st.columns(3)
    a.metric("Orders used", f"{n:,}")
    b.metric("Observed late rate", f"{late_rate:.1%}")
    c.metric("Model accuracy (training)", f"{model.score(train[features], train.is_late.astype(int)):.1%}")
    st.subheader("Historical risk groups")
    st.caption("Predicted and actual late rates for five equal-sized groups, from lowest to highest model risk.")
    chart = groups.set_index("risk_group")[["predicted_late", "actual_late"]] * 100
    st.bar_chart(chart)
    st.dataframe(groups.assign(
        predicted_late=groups.predicted_late.map("{:.1%}".format),
        actual_late=groups.actual_late.map("{:.1%}".format)), hide_index=True, use_container_width=True)
    if len(groups) >= 5:
        hi, lo = groups.iloc[-1].actual_late, groups.iloc[0].actual_late
        insight(f"The highest-risk group had an actual late rate of {hi:.1%}; the lowest-risk group had {lo:.1%}. These are historical training results.")

    st.subheader("Factors associated with late delivery")
    # Convert standardized logistic coefficients into odds ratios per one standard deviation.
    scaler = model.named_steps["scale"]
    coefs = model.named_steps["logit"].coef_[0]
    odds = pd.DataFrame({"Factor": features, "Odds ratio (per 1 SD)": np.exp(coefs)})
    labels = {
        "dist_1000km": "Distance (per 1,000 km)",
        "same_state": "Seller and customer in same state",
        "estimated_days": "Promised delivery days",
        "n_items": "Number of items",
        "value_100": "Order value (per R$100)",
        "freight_10": "Freight (per R$10)",
        "peak_month": "Peak month (Feb, Mar or Nov)"
    }
    odds["Factor"] = odds.Factor.map(labels)
    odds = odds.sort_values("Odds ratio (per 1 SD)", ascending=False)
    st.dataframe(odds.round(3), hide_index=True, use_container_width=True)
    st.caption("Odds ratios above 1 indicate higher estimated odds; below 1 indicate lower odds. "
               "These are associations, not proof of cause. Coefficients are shown per standard deviation.")

    st.subheader("What-if late-delivery estimator")
    st.write("Adjust order details to see the model's estimated late-delivery probability.")
    col1, col2, col3 = st.columns(3)
    distance = col1.number_input("Seller-to-customer distance (km)", min_value=0.0, max_value=6000.0, value=1000.0, step=100.0)
    promised = col2.number_input("Promised delivery days", min_value=1.0, max_value=90.0, value=20.0, step=1.0)
    items_count = col3.number_input("Number of items", min_value=1, max_value=30, value=1, step=1)
    col4, col5, col6 = st.columns(3)
    order_value = col4.number_input("Item sales (R$)", min_value=0.0, value=120.0, step=20.0)
    freight_value = col5.number_input("Freight (R$)", min_value=0.0, value=20.0, step=5.0)
    peak = col6.selectbox("Order month", ["Normal month", "Feb", "Mar", "Nov"]) != "Normal month"
    same_state = st.checkbox("Seller and customer are in the same state", value=(distance == 0))
    scenario = pd.DataFrame([{
        "dist_1000km": distance / 1000, "same_state": float(same_state),
        "estimated_days": promised, "n_items": items_count,
        "value_100": order_value / 100, "freight_10": freight_value / 10,
        "peak_month": float(peak)
    }], columns=features)
    probability = model.predict_proba(scenario)[0, 1]
    st.metric("Estimated chance of late delivery", f"{probability:.1%}")
    st.caption("Use realistic combinations. This model uses ZIP-prefix centroid distance from the processed Olist data; "
               "the notebook describes state-centre distance. Estimates outside the historical data range may be unreliable.")

    st.subheader("Model limitations")
    st.markdown("""
    - The model is trained on historical delivered orders because late/on-time outcomes are not yet known for undelivered orders.
    - It is not validated on a held-out test set, so training performance can be optimistic.
    - Distance is an approximate ZIP-prefix centroid distance, not a road or carrier route distance.
    - Weather, strikes, carrier performance and seller-specific delays are not included.
    - Results describe associations in historical data and should support, not replace, operational judgement.
    """)
def page_quality():
    st.title("Data quality audit")
    df = pd.read_csv(REPORTS_DIR / "data_quality_report.csv")
    status = st.multiselect("Status", ["Issue", "Info", "No issue"], default=["Issue"])
    st.dataframe(df[df.status.isin(status)], use_container_width=True)
    st.caption("Counts come from the Python audit of the original CSV files. Issues are flagged in the cleaned views, not deleted.")

# ---------------------------------------------------------------- navigation and filters
require_login()
DASH = DASH = {
    "Home": page_home,
    "Executive Overview": page_Executive_Overview,
    "Sales & Product": page_sales,
    "Customers & Reviews": page_customers,
    "Delivery & Logistics": page_delivery,
    "Payment & Geography": page_payment,
    "Predictive Model": page_predictive
}

st.sidebar.markdown("### Olist dashboard")
st.sidebar.markdown("### Olist dashboard")
st.sidebar.markdown("### Olist dashboard")
PAGE = st.sidebar.radio("Page", list(DASH) + ["Data quality"])
if PAGE in DASH:
    o, items, pays = load_orders(), load_items(), load_payments()
    st.sidebar.markdown("---"); st.sidebar.markdown("**Filters (slicers)**")
    years = sorted(o.purchase_year.dropna().unique().astype(int)); months = list(range(1, 13)); states = sorted(o.customer_state.dropna().unique())
    cats = sorted(o.category.dropna().unique()); statuses = sorted(o.order_status.dropna().unique())
    sy = st.sidebar.multiselect("Year", years, default=years); sm = st.sidebar.multiselect("Month (1-12)", months, default=months)
    ss = st.sidebar.multiselect("Customer state", states, default=states); sc = st.sidebar.multiselect("Category (first item of the order)", cats, default=cats)
    so = st.sidebar.multiselect("Order status", statuses, default=statuses)
    fo = o[o.purchase_year.isin(sy) & o.month_no.isin(sm) & o.customer_state.isin(ss) & o.category.isin(sc) & o.order_status.isin(so)]
    fi = items[items.order_id.isin(fo.order_id)]; fp = pays[pays.order_id.isin(fo.order_id)]
    st.sidebar.caption(f"{len(fo):,} of {len(o):,} orders selected")
    if fo.empty: st.warning("No orders match the filters.")
    else: DASH[PAGE](fo, fi, fp)

