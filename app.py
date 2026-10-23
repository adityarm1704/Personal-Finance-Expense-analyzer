from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

# -----------------------------------------------------------------------------
# Personal Finance & Expense Analyzer
# The demo-data generator, cleaning rules, summary metrics, and PDF statement
# workflow follow the supplied notebook's approach.
# -----------------------------------------------------------------------------

st.set_page_config(page_title="FinSight | Personal Finance", page_icon="💜", layout="wide", initial_sidebar_state="expanded")

NAVY = "#0B1020"
PANEL = "#141B31"
PURPLE = "#8B5CF6"
CYAN = "#38BDF8"
MUTED = "#A6B0CF"

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
  :root {{ --bg:{NAVY}; --panel:{PANEL}; --purple:{PURPLE}; --text:#F5F7FF; --muted:{MUTED}; }}
  html, body, [class*="css"] {{ font-family:'DM Sans',sans-serif; }}
  .stApp {{ background: radial-gradient(ellipse at 85% 0%, #25204b 0%, {NAVY} 43%); color:#F5F7FF; }}
  [data-testid="stSidebar"] {{ background:linear-gradient(180deg,#11172b 0%,#0b1020 100%); border-right:1px solid #252d49; }}
  [data-testid="stSidebar"] * {{ color:#E8EBFF; }}
  h1,h2,h3 {{ font-family:'Manrope',sans-serif !important; letter-spacing:-.035em; }}
  h1 {{ font-weight:800 !important; }}
  .hero {{ padding:1.35rem 1.5rem; border:1px solid #343052; border-radius:22px; background:linear-gradient(120deg,rgba(139,92,246,.20),rgba(56,189,248,.07)); margin-bottom:1.2rem; }}
  .eyebrow {{ color:#B8A5FF; text-transform:uppercase; letter-spacing:.16em; font-size:.72rem; font-weight:700; }}
  .hero-title {{ font:800 2rem 'Manrope',sans-serif; margin:.25rem 0 .4rem; color:#fff; }}
  .hero-sub {{ color:#B9C2DE; margin:0; }}
  .metric-card {{ background:linear-gradient(145deg,#1a2340,#13192c); border:1px solid #303a5c; border-radius:18px; padding:1rem 1.1rem; min-height:112px; }}
  .metric-label {{ color:#AEB9D8; font-size:.82rem; margin-bottom:.4rem; }}
  .metric-value {{ color:#F8FAFF; font:800 1.65rem 'Manrope',sans-serif; letter-spacing:-.04em; }}
  .metric-note {{ color:#8E9BBC; font-size:.76rem; margin-top:.35rem; }}
  .section-label {{ color:#B7A5FF; font-size:.76rem; font-weight:700; text-transform:uppercase; letter-spacing:.13em; margin-bottom:.3rem; }}
  .soft-card {{ background:rgba(20,27,49,.78); border:1px solid #293451; border-radius:18px; padding:1rem 1.2rem; }}
  .small-muted {{ color:#A6B0CF; font-size:.88rem; }}
  div[data-testid="stDataFrame"] {{ border:1px solid #303a5c; border-radius:12px; overflow:hidden; }}
  .stButton button, .stDownloadButton button {{ border-radius:11px; border:1px solid #6D54C7; background:linear-gradient(90deg,#7048DB,#8B5CF6); color:white; font-weight:700; }}
  .stButton button:hover, .stDownloadButton button:hover {{ border-color:#B4A0FF; color:white; }}
  div[data-baseweb="select"] > div, .stDateInput input, .stTextInput input {{ background:#171f37; border-color:#35405f; color:#fff; }}
  [data-testid="stMetric"] {{ background:#171f37; padding:14px 16px; border-radius:14px; border:1px solid #303a5c; }}
  hr {{ border-color:#28314c; }}
  footer {{ visibility:hidden; }}
</style>
""", unsafe_allow_html=True)

CHART_TEMPLATE = "plotly_dark"
CHART_LAYOUT = dict(template=CHART_TEMPLATE, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#DCE3FF", family="DM Sans"), margin=dict(l=10,r=10,t=48,b=10), legend=dict(bgcolor="rgba(0,0,0,0)"))


def money(value: float) -> str:
    return f"₹{value:,.0f}"


def metric_card(label: str, value: str, note: str, accent: str = PURPLE) -> None:
    st.markdown(f'''<div class="metric-card" style="border-top:3px solid {accent}"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>''', unsafe_allow_html=True)


def generate_demo_data() -> pd.DataFrame:
    """Same seeded 3,000-row synthetic dataset pattern as the provided notebook."""
    rng = np.random.default_rng(42)
    n = 3000
    categories = ["Food", "Housing", "Transport", "Shopping", "Healthcare", "Entertainment", "Education", "Utilities", "Salary", "Freelance", "Investment"]
    descriptions = {
        "Food": ["Groceries", "Restaurant", "Cafe", "Food Delivery"], "Housing": ["House Rent", "Maintenance", "Furniture"],
        "Transport": ["Fuel", "Bus", "Train", "Cab"], "Shopping": ["Clothing", "Electronics", "Online Shopping"],
        "Healthcare": ["Medicine", "Doctor", "Medical Test"], "Entertainment": ["Movie", "Subscription", "Gaming"],
        "Education": ["Course Fee", "Books", "Online Course"], "Utilities": ["Electricity", "Internet", "Mobile Bill"],
        "Salary": ["Monthly Salary", "Bonus"], "Freelance": ["Freelance Payment", "Consulting"], "Investment": ["Dividend", "Investment Return"]}
    start = pd.Timestamp("2025-01-01").value // 10**9
    end = pd.Timestamp("2026-01-01").value // 10**9
    dates = pd.to_datetime(rng.integers(start, end, size=n), unit="s").normalize()
    category = rng.choice(categories, size=n, p=[.20,.08,.12,.13,.06,.08,.05,.08,.08,.07,.05])
    typ = np.where(np.isin(category, ["Salary", "Freelance", "Investment"]), "Income", "Expense")
    amounts = []
    for cat in category:
        if cat == "Salary": amounts.append(rng.integers(25000,65001))
        elif cat == "Freelance": amounts.append(rng.integers(1000,20001))
        elif cat == "Investment": amounts.append(rng.integers(500,10001))
        elif cat == "Housing": amounts.append(rng.integers(5000,18001))
        else: amounts.append(rng.integers(100,5001))
    raw = pd.DataFrame({
        "Transaction_ID":[f"TXN{i:05d}" for i in range(1,n+1)], "Date":dates,
        "Description":[rng.choice(descriptions[cat]) for cat in category], "Category":category, "Type":typ,
        "Amount":amounts, "Payment_Mode":rng.choice(["UPI","Cash","Debit Card","Credit Card","Bank Transfer"],size=n),
        "Account":rng.choice(["Savings","Current","Credit"],size=n,p=[.65,.15,.20]),
        "City":rng.choice(["Pune","Mumbai","Sangli","Nashik","Nagpur"],size=n)})
    # Intentional quality issues copied from notebook to demonstrate cleaning.
    raw.loc[10,"Description"] = None; raw.loc[25,"Category"] = None
    raw.loc[40,"Amount"] = np.nan; raw.loc[50,"Payment_Mode"] = "upi"; raw.loc[60,"Amount"] = -500
    raw = pd.concat([raw, raw.iloc[[100,200]]], ignore_index=True)
    return clean_transactions(raw)[0]


def clean_transactions(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df = frame.copy()
    raw_count = len(df)
    if "Transaction_ID" in df.columns:
        df = df.drop_duplicates(subset="Transaction_ID", keep="first").copy()
    if "Date" not in df.columns or "Amount" not in df.columns or "Type" not in df.columns:
        raise ValueError("CSV must include Date, Amount, and Type columns. Recommended columns: Transaction_ID, Description, Category, Type, Amount, Payment_Mode, Account, City.")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    for col in ["Description","Category","Type","Payment_Mode","Account","City"]:
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()
    for col in ["Payment_Mode","Type","Category"]:
        if col in df.columns: df[col] = df[col].str.title()
    for col, default in [("Description","Unknown Description"),("Category","Uncategorized"),("Payment_Mode","Unknown"),("Account","Unknown"),("City","Unknown")]:
        if col not in df.columns: df[col] = default
        df[col] = df[col].fillna(default)
    invalid_dates = int(df["Date"].isna().sum())
    invalid_amounts = int((df["Amount"].isna() | df["Amount"].lt(0)).sum())
    df = df.dropna(subset=["Date","Amount"])
    df = df[df["Amount"] >= 0].copy()
    df = df[df["Type"].isin(["Income","Expense"])].copy()
    if "Transaction_ID" not in df.columns:
        df.insert(0,"Transaction_ID",[f"TXN{i:05d}" for i in range(1,len(df)+1)])
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["Month_Name"] = df["Date"].dt.strftime("%b")
    df["Year_Month"] = df["Date"].dt.to_period("M").astype(str)
    df["Amount"] = df["Amount"].astype(float)
    return df, {"raw_rows":raw_count,"clean_rows":len(df),"removed_rows":raw_count-len(df),"invalid_dates":invalid_dates,"invalid_amounts":invalid_amounts}


SENSITIVE_PATTERNS = [
    (re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.I), "[PAN REDACTED]"),
    (re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b", re.I), "[IFSC REDACTED]"),
    (re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I), "[EMAIL REDACTED]"),
    (re.compile(r"\b[\w.+-]+@[\w.-]+\b", re.I), "[ID REDACTED]"),
    (re.compile(r"(?<!\d)(?:\+?91[-\s]?)?[6-9]\d{9}(?!\d)"), "[PHONE REDACTED]"),
    (re.compile(r"\b\d{12}\b"), "[12-DIGIT ID REDACTED]"),
    (re.compile(r"\b\d{16,19}\b"), "[CARD/ACCOUNT NUMBER REDACTED]"),
    (re.compile(r"\b(?:A/C|ACCT|ACCOUNT|ACC(?:OUNT)?\s*NO\.?|CARD)\s*[:#-]?\s*[A-Z0-9-]{5,}\b", re.I), "[ACCOUNT DETAIL REDACTED]"),
    (re.compile(r"\b(?:CUSTOMER|CUST|CIF|CRN|CLIENT)\s*(?:ID|NO\.?)?\s*[:#-]?\s*[A-Z0-9-]{4,}\b", re.I), "[CUSTOMER ID REDACTED]"),
]


def redact_text(value) -> str:
    if pd.isna(value): return ""
    text = str(value)
    for pattern, replacement in SENSITIVE_PATTERNS: text = pattern.sub(replacement, text)
    def mask_digit_run(match):
        digits = re.sub(r"\D", "", match.group(0))
        return "[NUMBER REDACTED]" if len(digits) >= 8 else match.group(0)
    text = re.sub(r"(?<!\w)(?:\d[\s/-]?){8,19}(?!\w)", mask_digit_run, text)
    return re.sub(r"\s+", " ", text).strip()


def parse_money(value):
    if pd.isna(value): return np.nan
    s = str(value).strip()
    if s.lower() in {"", "-", "—", "–", "na", "n/a", "none"}: return np.nan
    s = s.replace("₹","").replace("INR","").replace("Rs.","").replace("Rs","").replace(",","").strip()
    negative = (s.startswith("(") and s.endswith(")")) or s.endswith("-")
    s = s.strip("()")
    if s.endswith("-"): s = s[:-1]
    try:
        number = float(s)
        return -abs(number) if negative else number
    except ValueError: return np.nan


def parse_statement_date(value):
    if pd.isna(value) or not str(value).strip(): return pd.NaT
    for fmt in ["%d/%m/%Y","%d-%m-%Y","%Y-%m-%d","%d %b %Y","%d %B %Y"]:
        try: return pd.to_datetime(str(value).strip(), format=fmt, errors="raise")
        except (ValueError,TypeError): pass
    return pd.to_datetime(value, errors="coerce", dayfirst=True)


def infer_category(description, typ):
    d = str(description).lower()
    if typ == "Income":
        if "salary" in d or "payroll" in d: return "Salary"
        if any(x in d for x in ["refund","reversal"]): return "Review"
        return "Other Income"
    rules = {"Food":["grocery","grocer","restaurant","cafe","food","swiggy","zomato"],"Transport":["uber","ola","fuel","petrol","metro","bus","train","parking"],"Housing":["rent","maintenance"],"Utilities":["electricity","water bill","internet","mobile bill","broadband"],"Shopping":["amazon","flipkart","shopping","retail"],"Healthcare":["pharmacy","hospital","doctor","medical","medicine"],"Entertainment":["movie","cinema","subscription","netflix","spotify"]}
    for cat, words in rules.items():
        if any(word in d for word in words): return cat
    return "Uncategorized"


def standardize_statement(source: pd.DataFrame, date_col: str, description_col: str, debit_col: str|None, credit_col: str|None, amount_col: str|None, amount_convention: str|None, type_col: str|None) -> pd.DataFrame:
    required = [date_col, description_col]
    if debit_col and credit_col: required += [debit_col, credit_col]
    elif amount_col:
        required += [amount_col]
        if amount_convention not in {"negative_expense_positive_income","positive_expense","positive_all_requires_type"}:
            raise ValueError("Choose a sign convention for the single amount column.")
        if amount_convention == "positive_all_requires_type" and not type_col: raise ValueError("This convention requires a transaction-type column.")
    else: raise ValueError("Map both debit and credit columns, or map a single amount column with a sign convention.")
    if type_col: required.append(type_col)
    missing = [c for c in required if c not in source.columns]
    if missing: raise KeyError(f"Mapped columns not found: {missing}")
    result = pd.DataFrame()
    result["Date"] = source[date_col].map(parse_statement_date)
    result["Description"] = source[description_col].map(redact_text)
    result["Debit"] = 0.0; result["Credit"] = 0.0; result["Review_Flag"] = ""
    blankish = {"", "-", "—", "–"}
    if debit_col and credit_col:
        debit = source[debit_col].map(parse_money); credit = source[credit_col].map(parse_money)
        debit_bad = source[debit_col].map(lambda x: not pd.isna(x) and str(x).strip() not in blankish and pd.isna(parse_money(x)))
        credit_bad = source[credit_col].map(lambda x: not pd.isna(x) and str(x).strip() not in blankish and pd.isna(parse_money(x)))
        result["Debit"] = debit.fillna(0).abs(); result["Credit"] = credit.fillna(0).abs()
        result.loc[debit_bad | credit_bad,"Review_Flag"] = "Invalid debit/credit value"
    else:
        signed = source[amount_col].map(parse_money)
        bad = source[amount_col].map(lambda x: not pd.isna(x) and str(x).strip() not in blankish and pd.isna(parse_money(x)))
        if amount_convention == "negative_expense_positive_income":
            result["Debit"] = signed.where(signed < 0,0).abs().fillna(0); result["Credit"] = signed.where(signed > 0,0).fillna(0)
        elif amount_convention == "positive_expense": result["Debit"] = signed.abs().fillna(0)
        else:
            raw_type = source[type_col].fillna("").astype(str).str.lower()
            is_debit = raw_type.str.contains(r"debit|withdraw|expense|\bdr\b",regex=True)
            is_credit = raw_type.str.contains(r"credit|deposit|income|\bcr\b|salary",regex=True)
            result["Debit"] = signed.abs().where(is_debit,0).fillna(0); result["Credit"] = signed.abs().where(is_credit,0).fillna(0)
        result.loc[bad,"Review_Flag"] = "Invalid amount value"
    both = (result["Debit"] > 0) & (result["Credit"] > 0)
    result.loc[both,"Review_Flag"] = "Both debit and credit populated; verify source"
    result["Amount"] = result[["Debit","Credit"]].max(axis=1)
    result["Type"] = np.select([(result["Debit"]>0)&(result["Credit"]==0),(result["Credit"]>0)&(result["Debit"]==0)],["Expense","Income"],default="Review")
    if type_col:
        tx_type = source[type_col].fillna("").astype(str).str.lower()
        is_debit = tx_type.str.contains(r"debit|withdraw|expense|\bdr\b",regex=True)
        is_credit = tx_type.str.contains(r"credit|deposit|income|\bcr\b|salary",regex=True)
        conflict = (is_debit & (result["Credit"]>0)) | (is_credit & (result["Debit"]>0))
        result.loc[conflict,"Type"] = "Review"; result.loc[conflict,"Review_Flag"] = "Transaction type conflicts with debit/credit columns"
    reversal = result["Description"].str.contains(r"refund|reversal|reversed|chargeback|cancelled|canceled",case=False,na=False)
    result.loc[reversal,"Type"] = "Review"
    result.loc[reversal & result["Review_Flag"].eq(""),"Review_Flag"] = "Possible refund/reversal: verify treatment"
    result.loc[result["Date"].isna() & result["Review_Flag"].eq(""),"Review_Flag"] = "Missing or unparsed date"
    result.loc[result["Description"].eq("") & result["Review_Flag"].eq(""),"Review_Flag"] = "Missing description"
    result.loc[result["Amount"].eq(0) & result["Review_Flag"].eq(""),"Review_Flag"] = "Zero/unknown amount"
    result["Category"] = [infer_category(d,t) if t in {"Income","Expense"} else "Review" for d,t in zip(result["Description"],result["Type"])]
    result["Payment_Mode"] = "Unknown"
    result["Transaction_ID"] = [f"PDF_TXN_{i:06d}" for i in range(1,len(result)+1)]
    result["Year_Month"] = result["Date"].dt.to_period("M").astype(str)
    return result[["Date","Description","Debit","Credit","Amount","Type","Category","Payment_Mode","Transaction_ID","Year_Month","Review_Flag"]].copy()


def extract_pdf_tables(uploaded_file):
    if pdfplumber is None: raise ImportError("Install pdfplumber with: pip install pdfplumber")
    candidates=[]
    with pdfplumber.open(BytesIO(uploaded_file.getvalue())) as pdf:
        for page_no,page in enumerate(pdf.pages,start=1):
            for table_no,table in enumerate(page.extract_tables() or [],start=1):
                if table and any(any(cell not in (None,"") for cell in row) for row in table):
                    candidates.append({"page":page_no,"table_on_page":table_no,"rows":table})
    return candidates


def candidate_frame(candidate, header_row=0):
    rows=candidate["rows"]
    if not rows: return pd.DataFrame()
    width=max(len(row) for row in rows); rows=[list(row)+[None]*(width-len(row)) for row in rows]
    headers=[str(x).strip() if x is not None and str(x).strip() else f"Column_{i+1}" for i,x in enumerate(rows[header_row])]
    body=rows[header_row+1:]
    seen={}; unique=[]
    for h in headers:
        seen[h]=seen.get(h,0)+1; unique.append(h if seen[h]==1 else f"{h}_{seen[h]}")
    return pd.DataFrame(body,columns=unique)


def masked_preview(frame, limit=10):
    safe=frame.head(limit).copy()
    for col in safe.columns: safe[col]=safe[col].map(redact_text)
    return safe


def render_header(title, subtitle):
    st.markdown(f'<div class="hero"><div class="eyebrow">FINSIGHT • PERSONAL FINANCE</div><div class="hero-title">{title}</div><p class="hero-sub">{subtitle}</p></div>',unsafe_allow_html=True)


# Sidebar navigation and data source
with st.sidebar:
    st.markdown("<div style='font:800 1.35rem Manrope,sans-serif;color:#fff;padding:.5rem 0 .1rem'>💜 FinSight</div><div style='color:#9DA9CD;font-size:.8rem;margin-bottom:1.2rem'>Your money, in perspective.</div>",unsafe_allow_html=True)
    page=st.radio("WORKSPACE",["Overview","Transactions","PDF Statement Analyzer","Data Quality"],label_visibility="visible")
    st.markdown("---")
    st.markdown("<div class='small-muted'>DATA SOURCE</div>",unsafe_allow_html=True)
    source_choice=st.radio("Choose data",["Notebook demo data","Upload transaction CSV"],label_visibility="collapsed")
    uploaded_csv=None
    if source_choice=="Upload transaction CSV":
        uploaded_csv=st.file_uploader("Choose a transactions CSV",type=["csv"],key="main_csv")
    st.markdown("---")
    st.caption("Demo records are synthetic, not real bank transactions.")

@st.cache_data(show_spinner=False)
def cached_demo(): return generate_demo_data()

quality_info={"raw_rows":3002,"clean_rows":0,"removed_rows":0,"invalid_dates":0,"invalid_amounts":0}
try:
    if source_choice=="Upload transaction CSV":
        if uploaded_csv is None:
            st.info("Upload a CSV from the sidebar to view your own transactions. You can switch back to notebook demo data at any time.")
            st.stop()
        raw_user=pd.read_csv(uploaded_csv)
        data,quality_info=clean_transactions(raw_user)
        data_source_name=uploaded_csv.name
    else:
        data=cached_demo()
        quality_info={"raw_rows":3002,"clean_rows":len(data),"removed_rows":3002-len(data),"invalid_dates":0,"invalid_amounts":2}
        data_source_name="Notebook synthetic demo"
except Exception as exc:
    st.error(f"Could not load the data: {exc}")
    st.stop()

if data.empty:
    st.warning("No valid transactions remain after cleaning. Check your CSV columns and values.")
    st.stop()

# Shared summaries
income=float(data.loc[data.Type=="Income","Amount"].sum())
expenses=float(data.loc[data.Type=="Expense","Amount"].sum())
net=income-expenses
savings_rate=(net/income*100) if income else 0.0
monthly=(data.pivot_table(index="Year_Month",columns="Type",values="Amount",aggfunc="sum",fill_value=0).sort_index())
for col in ["Income","Expense"]:
    if col not in monthly: monthly[col]=0.0
monthly["Net_Cash_Flow"]=monthly["Income"]-monthly["Expense"]
monthly=monthly.reset_index()
expenses_df=data[data.Type=="Expense"].copy()
category_analysis=(expenses_df.groupby("Category",as_index=False).agg(Transaction_Count=("Transaction_ID","count"),Total_Expense=("Amount","sum"),Average_Expense=("Amount","mean"),Median_Expense=("Amount","median")).sort_values("Total_Expense",ascending=False))

if page=="Overview":
    render_header("Your financial snapshot", "A clear view of cash flow, spending patterns, and the habits shaping your money.")
    st.markdown(f"<div class='small-muted' style='margin:-.5rem 0 1rem'>Source: <b>{data_source_name}</b> · {len(data):,} cleaned transactions</div>",unsafe_allow_html=True)
    cols=st.columns(4,gap="medium")
    with cols[0]: metric_card("TOTAL INCOME",money(income),"Money received",CYAN)
    with cols[1]: metric_card("TOTAL EXPENSES",money(expenses),"Money spent",PURPLE)
    with cols[2]: metric_card("NET CASH FLOW",money(net),"Income minus expenses", "#34D399" if net>=0 else "#FB7185")
    with cols[3]: metric_card("SAVINGS RATE",f"{savings_rate:.1f}%","Net cash flow ÷ income", "#FBBF24")
    st.write("")
    left,right=st.columns([1.55,1],gap="large")
    with left:
        st.markdown("<div class='section-label'>Cash flow over time</div>",unsafe_allow_html=True)
        fig=go.Figure()
        fig.add_trace(go.Bar(x=monthly.Year_Month,y=monthly.Income,name="Income",marker_color=CYAN))
        fig.add_trace(go.Bar(x=monthly.Year_Month,y=monthly.Expense,name="Expenses",marker_color=PURPLE))
        fig.update_layout(**CHART_LAYOUT,barmode="group",height=340,title="Monthly income vs expenses",xaxis_title="Month",yaxis_title="Amount (₹)")
        st.plotly_chart(fig,use_container_width=True)
    with right:
        st.markdown("<div class='section-label'>Where expenses go</div>",unsafe_allow_html=True)
        if not category_analysis.empty:
            fig=px.pie(category_analysis,names="Category",values="Total_Expense",hole=.68,color_discrete_sequence=[PURPLE,CYAN,"#A78BFA","#F472B6","#34D399","#FBBF24","#60A5FA","#FB7185"])
            fig.update_layout(**CHART_LAYOUT,height=340,title="Expense mix")
            fig.update_traces(textposition="inside",textinfo="percent")
            st.plotly_chart(fig,use_container_width=True)
        else: st.info("No expense transactions in the selected data.")
    a,b=st.columns(2,gap="large")
    with a:
        st.markdown("<div class='section-label'>Top expense categories</div>",unsafe_allow_html=True)
        if not category_analysis.empty:
            fig=px.bar(category_analysis.head(8).sort_values("Total_Expense"),x="Total_Expense",y="Category",orientation="h",color="Total_Expense",color_continuous_scale=[[0,"#312E81"],[1,PURPLE]])
            fig.update_layout(**CHART_LAYOUT,height=330,title="Spending by category",coloraxis_showscale=False,xaxis_title="Amount (₹)",yaxis_title="")
            st.plotly_chart(fig,use_container_width=True)
    with b:
        st.markdown("<div class='section-label'>Monthly net cash flow</div>",unsafe_allow_html=True)
        fig=px.line(monthly,x="Year_Month",y="Net_Cash_Flow",markers=True)
        fig.update_traces(line_color=CYAN,marker_color=PURPLE,line_width=3)
        fig.add_hline(y=0,line_dash="dash",line_color="#7E8AAE")
        fig.update_layout(**CHART_LAYOUT,height=330,title="Income minus expenses",xaxis_title="Month",yaxis_title="Net (₹)")
        st.plotly_chart(fig,use_container_width=True)
    if not category_analysis.empty:
        top=category_analysis.iloc[0]
        st.markdown(f"<div class='soft-card'><div class='section-label'>QUICK INSIGHT</div><b>{top['Category']}</b> is your largest expense category at <b>{money(float(top['Total_Expense']))}</b>. Your highest-spend category is a useful starting point for reviewing your budget.</div>",unsafe_allow_html=True)

elif page=="Transactions":
    render_header("Transaction explorer", "Search, filter, inspect, and export a slice of your transaction history.")
    f1,f2,f3=st.columns(3)
    with f1: types=st.multiselect("Transaction type",sorted(data.Type.unique()),default=sorted(data.Type.unique()))
    with f2: cats=st.multiselect("Category",sorted(data.Category.astype(str).unique()),default=sorted(data.Category.astype(str).unique()))
    with f3: modes=st.multiselect("Payment mode",sorted(data.Payment_Mode.astype(str).unique()),default=sorted(data.Payment_Mode.astype(str).unique()))
    min_date=pd.to_datetime(data.Date).min().date(); max_date=pd.to_datetime(data.Date).max().date()
    d1,d2,d3=st.columns([1,1,1.2])
    with d1: start_date=st.date_input("From",value=min_date,min_value=min_date,max_value=max_date)
    with d2: end_date=st.date_input("To",value=max_date,min_value=min_date,max_value=max_date)
    with d3: search=st.text_input("Search description or ID",placeholder="e.g. groceries or TXN...")
    filtered=data[data.Type.isin(types)&data.Category.astype(str).isin(cats)&data.Payment_Mode.astype(str).isin(modes)].copy()
    filtered=filtered[(filtered.Date.dt.date>=start_date)&(filtered.Date.dt.date<=end_date)]
    if search.strip():
        mask=filtered.Description.astype(str).str.contains(search.strip(),case=False,na=False)|filtered.Transaction_ID.astype(str).str.contains(search.strip(),case=False,na=False)
        filtered=filtered[mask]
    c1,c2,c3=st.columns(3)
    with c1: st.metric("Filtered transactions",f"{len(filtered):,}")
    with c2: st.metric("Income",money(filtered.loc[filtered.Type=="Income","Amount"].sum()))
    with c3: st.metric("Expenses",money(filtered.loc[filtered.Type=="Expense","Amount"].sum()))
    display_cols=[c for c in ["Transaction_ID","Date","Description","Category","Type","Amount","Payment_Mode","Account","City"] if c in filtered.columns]
    st.dataframe(filtered[display_cols].sort_values("Date",ascending=False),use_container_width=True,hide_index=True,column_config={"Amount":st.column_config.NumberColumn("Amount (₹)",format="₹ %.2f"),"Date":st.column_config.DateColumn("Date",format="DD MMM YYYY")})
    st.download_button("⬇ Download filtered transactions (CSV)",filtered[display_cols].to_csv(index=False).encode("utf-8-sig"),file_name="filtered_transactions.csv",mime="text/csv",disabled=filtered.empty)

elif page=="Data Quality":
    render_header("Data quality & validation", "The app follows the notebook's cleaning rules before calculating financial metrics.")
    cols=st.columns(4)
    with cols[0]: metric_card("ROWS LOADED",f"{quality_info['raw_rows']:,}","Before cleaning",CYAN)
    with cols[1]: metric_card("VALID ROWS",f"{len(data):,}","Used for analysis", "#34D399")
    with cols[2]: metric_card("ROWS REMOVED",f"{quality_info['removed_rows']:,}","Duplicates / invalid values", "#FB7185")
    with cols[3]: metric_card("DUPLICATE IDS",f"{int(data.Transaction_ID.duplicated().sum()):,}","Expected: zero",PURPLE)
    st.write("")
    checks=pd.DataFrame({"Validation check":["Missing dates remaining","Missing amounts remaining","Negative amounts remaining","Unexpected transaction types","Duplicate transaction IDs remaining"],"Result":[int(data.Date.isna().sum()),int(data.Amount.isna().sum()),int((data.Amount<0).sum()),int((~data.Type.isin(["Income","Expense"])).sum()),int(data.Transaction_ID.duplicated().sum())]})
    st.dataframe(checks,use_container_width=True,hide_index=True)
    st.markdown("#### Cleaning approach")
    st.markdown("- Duplicate transaction IDs are removed, keeping the first row.\n- Dates and amounts are converted to suitable types.\n- Text fields are trimmed and category/type/payment-mode labels are standardized.\n- Missing labels receive a neutral placeholder; missing or negative amounts are excluded rather than invented.\n- Only Income and Expense transaction types are included in the dashboard.")
    st.caption("For uploaded CSV files, include Date, Amount, and Type. Transaction_ID is recommended; if absent, IDs are generated for the session.")

elif page=="PDF Statement Analyzer":
    render_header("Bank statement analyzer", "Extract table-based PDFs, redact sensitive identifiers, map transaction columns, and review before exporting.")
    st.warning("Privacy note: use a local copy of your statement. The app processes the uploaded PDF in this Streamlit session and does not intentionally save it. Redaction is a safeguard, not a guarantee; review all output before sharing.")
    if pdfplumber is None:
        st.error("PDF support is not installed. Run `pip install pdfplumber` in your project environment.")
        st.stop()
    pdf_file=st.file_uploader("Upload a bank statement PDF",type=["pdf"],key="statement_pdf")
    if pdf_file is None:
        st.markdown("<div class='soft-card'><div class='section-label'>SUPPORTED WORKFLOW</div>1. Upload a text/table-based PDF. 2. Choose a detected table. 3. Inspect the masked preview. 4. Map the transaction columns. 5. Review flagged rows. 6. Opt in to download a sanitized CSV.</div>",unsafe_allow_html=True)
        st.info("Scanned/image-only PDFs may not contain extractable tables. This version does not run OCR; a no-table result means the statement needs OCR or a custom parser.")
    else:
        try:
            with st.spinner("Extracting table structures from the PDF…"):
                candidates=extract_pdf_tables(pdf_file)
            if not candidates:
                st.error("No tables were detected. The PDF may be scanned or use an unsupported layout. This app does not run OCR.")
            else:
                labels=[f"Page {x['page']} · Table {x['table_on_page']} · {len(x['rows'])} rows" for x in candidates]
                selected=st.selectbox("Detected table",range(len(candidates)),format_func=lambda i:labels[i])
                header_row=st.number_input("Header row index (0 means first row)",min_value=0,max_value=max(0,len(candidates[selected]["rows"])-1),value=0,step=1)
                extracted=candidate_frame(candidates[selected],int(header_row))
                st.markdown("#### Masked source preview")
                st.caption("Values are redacted before display. Column names are shown so you can map fields.")
                st.dataframe(masked_preview(extracted),use_container_width=True,hide_index=True)
                st.markdown("#### Map transaction columns")
                available=list(extracted.columns)
                if len(available)<2:
                    st.error("This table has too few columns. Choose another detected table.")
                else:
                    def choose(label, key, optional=False, default_idx=0):
                        opts=(['— Not mapped —'] if optional else [])+available
                        idx=min(default_idx,len(available)-1)+(1 if optional else 0)
                        idx=min(idx,len(opts)-1)
                        val=st.selectbox(label,opts,index=idx,key=key)
                        return None if val=='— Not mapped —' else val
                    map1,map2=st.columns(2)
                    with map1: date_col=choose("Date column","pdf_date")
                    with map2: desc_col=choose("Description / narration column","pdf_desc",default_idx=min(1,len(available)-1))
                    amount_mode=st.radio("Amount columns",["Separate debit and credit columns","Single amount column"],horizontal=True)
                    debit_col=credit_col=amount_col=type_col=convention=None
                    if amount_mode=="Separate debit and credit columns":
                        a,b=st.columns(2)
                        with a: debit_col=choose("Debit / withdrawal column","pdf_debit",optional=True,default_idx=min(2,len(available)-1))
                        with b: credit_col=choose("Credit / deposit column","pdf_credit",optional=True,default_idx=min(3,len(available)-1))
                    else:
                        a,b=st.columns(2)
                        with a: amount_col=choose("Amount column","pdf_amount",default_idx=min(2,len(available)-1))
                        with b: convention=st.selectbox("Amount sign convention",["negative_expense_positive_income","positive_expense","positive_all_requires_type"],format_func=lambda x:{"negative_expense_positive_income":"Negative = expense, positive = income","positive_expense":"All positive amounts are expenses","positive_all_requires_type":"Positive amounts; infer type from a type column"}[x])
                    use_type=st.checkbox("Map an explicit transaction type column (optional)",value=False)
                    if use_type: type_col=choose("Transaction type column","pdf_type",optional=True,default_idx=min(4,len(available)-1))
                    if st.button("Analyze mapped transactions",type="primary"):
                        try:
                            standardized=standardize_statement(extracted,date_col,desc_col,debit_col,credit_col,amount_col,convention,type_col)
                            st.session_state["standardized_statement"]=standardized
                            st.session_state["statement_filename"]=pdf_file.name
                        except Exception as e: st.error(str(e))
                standardized=st.session_state.get("standardized_statement")
                if standardized is not None:
                    st.markdown("---")
                    st.markdown("#### Sanitized transaction review")
                    accepted=standardized[standardized.Type.isin(["Income","Expense"])]
                    total_income=float(accepted.loc[accepted.Type=="Income","Credit"].sum())
                    total_expense=float(accepted.loc[accepted.Type=="Expense","Debit"].sum())
                    reviews=int((standardized.Type=="Review").sum())
                    k1,k2,k3,k4=st.columns(4)
                    with k1: metric_card("ACCEPTED INCOME",money(total_income),"Income rows only",CYAN)
                    with k2: metric_card("ACCEPTED EXPENSES",money(total_expense),"Expense rows only",PURPLE)
                    with k3: metric_card("NET CASH FLOW",money(total_income-total_expense),"Income minus expenses","#34D399")
                    with k4: metric_card("NEEDS REVIEW",f"{reviews:,}","Do not assume these are correct","#FBBF24")
                    shown=standardized.copy(); shown["Date"]=pd.to_datetime(shown["Date"],errors="coerce")
                    st.dataframe(shown,use_container_width=True,hide_index=True,column_config={"Date":st.column_config.DateColumn("Date",format="DD MMM YYYY"),"Debit":st.column_config.NumberColumn("Debit (₹)",format="₹ %.2f"),"Credit":st.column_config.NumberColumn("Credit (₹)",format="₹ %.2f"),"Amount":st.column_config.NumberColumn("Amount (₹)",format="₹ %.2f")})
                    duplicate=standardized.duplicated(subset=["Date","Description","Amount"],keep=False)
                    validation=pd.DataFrame({"Check":["Rows extracted","Missing/unparsed dates","Blank descriptions","Zero transaction amounts","Rows marked Review","Duplicate-looking rows","Rows with review flags"],"Result":[len(standardized),int(standardized.Date.isna().sum()),int(standardized.Description.eq("").sum()),int(standardized.Amount.fillna(0).eq(0).sum()),reviews,int(duplicate.sum()),int(standardized.Review_Flag.ne("").sum())]})
                    with st.expander("Validation report",expanded=True): st.dataframe(validation,use_container_width=True,hide_index=True)
                    st.checkbox("I reviewed the sanitized rows and understand that flagged transactions may be misclassified.",key="approve_statement_export")
                    export_cols=["Date","Description","Debit","Credit","Amount","Type","Category","Payment_Mode","Transaction_ID","Year_Month","Review_Flag"]
                    export=standardized[export_cols].copy()
                    export["Date"]=pd.to_datetime(export["Date"],errors="coerce").dt.strftime("%Y-%m-%d")
                    st.download_button("⬇ Download sanitized statement CSV",export.to_csv(index=False).encode("utf-8-sig"),file_name="sanitized_bank_transactions.csv",mime="text/csv",disabled=not st.session_state.get("approve_statement_export",False))
                    st.caption("Only the allow-listed sanitized columns are exported. Account balances and customer/account metadata are not included.")
        except Exception as exc:
            st.error(f"Could not read this PDF: {exc}")

st.markdown("<div style='text-align:center;color:#7582A8;font-size:.75rem;padding:1.5rem 0 0'>FINSIGHT · Built with Streamlit, Pandas, NumPy and Plotly · Educational project</div>",unsafe_allow_html=True)
