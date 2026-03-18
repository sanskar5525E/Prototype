import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
import io

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="CreditPulse Demo — Wholesale Risk Intelligence",
    layout="wide", page_icon="⚡"
)

# ══════════════════════════════════════════════════════════════════════════════
#  CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@700;800&family=Inter:wght@400;500;600&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:#060E18;color:#F0F4F8;}
header[data-testid="stHeader"]{background:transparent;}
section[data-testid="stSidebar"]{background:#0D1B2A !important;border-right:1px solid rgba(255,255,255,0.07);}
section[data-testid="stSidebar"] *{color:#C8D8E8 !important;}
[data-testid="metric-container"]{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:16px 20px;}
[data-testid="metric-container"] label{color:#8899AA !important;font-size:11px !important;letter-spacing:0.08em;text-transform:uppercase;}
[data-testid="metric-container"] [data-testid="stMetricValue"]{color:#F0F4F8 !important;font-family:'DM Mono',monospace !important;font-size:20px !important;}
.stButton>button{background:linear-gradient(135deg,#5B9EF4,#4A7EC4) !important;border:none !important;color:white !important;border-radius:10px !important;font-weight:600 !important;padding:10px 24px !important;}
[data-testid="stDataFrame"]{border-radius:12px;overflow:hidden;}
.stTabs [data-baseweb="tab-list"]{background:rgba(255,255,255,0.03);border-radius:10px;padding:4px;gap:4px;}
.stTabs [data-baseweb="tab"]{background:transparent;color:#8899AA;border-radius:8px;font-size:13px;font-weight:500;}
.stTabs [aria-selected="true"]{background:rgba(91,158,244,0.15) !important;color:#5B9EF4 !important;}
.stSelectbox>div>div{background:rgba(255,255,255,0.05) !important;border:1px solid rgba(255,255,255,0.1) !important;border-radius:10px !important;color:#F0F4F8 !important;}
.streamlit-expanderHeader{background:rgba(255,255,255,0.04) !important;border-radius:10px !important;color:#C8D8E8 !important;}
.stDownloadButton>button{background:rgba(0,229,160,0.1) !important;border:1px solid rgba(0,229,160,0.3) !important;color:#00E5A0 !important;border-radius:10px !important;}
.stSuccess{background:rgba(0,229,160,0.1) !important;border:1px solid rgba(0,229,160,0.3) !important;border-radius:10px !important;}
.stInfo{background:rgba(91,158,244,0.1) !important;border:1px solid rgba(91,158,244,0.3) !important;border-radius:10px !important;}
.stWarning{background:rgba(255,140,66,0.1) !important;border:1px solid rgba(255,140,66,0.3) !important;border-radius:10px !important;}
.stError{background:rgba(255,56,96,0.1) !important;border:1px solid rgba(255,56,96,0.3) !important;border-radius:10px !important;}

/* ── Mobile Friendly ── */
@media (max-width: 768px) {
  /* Bigger tap targets */
  .stButton>button{padding:14px 20px !important;font-size:15px !important;width:100% !important;}
  .stDownloadButton>button{padding:14px 20px !important;font-size:14px !important;}
  /* Tabs scroll on mobile */
  .stTabs [data-baseweb="tab-list"]{overflow-x:auto !important;flex-wrap:nowrap !important;}
  .stTabs [data-baseweb="tab"]{white-space:nowrap !important;font-size:12px !important;padding:8px 12px !important;}
  /* Metrics stack nicely */
  [data-testid="metric-container"]{padding:12px 14px !important;}
  [data-testid="metric-container"] [data-testid="stMetricValue"]{font-size:17px !important;}
  /* Dataframe scrollable */
  [data-testid="stDataFrame"]{overflow-x:auto !important;}
  /* Expanders full width */
  .streamlit-expanderHeader{font-size:13px !important;}
  /* Remove sidebar on mobile — show as hamburger */
  section[data-testid="stSidebar"]{width:100% !important;}
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
GRADE_META = {
    "A":{"color":"#00E5A0","rgba":"0,229,160",  "label":"Low Risk",      "action":"Increase Limit",   "call":"Thank & Reward Call",    "limit_mult":1.2},
    "B":{"color":"#FFD166","rgba":"255,209,102", "label":"Moderate Risk", "action":"Monitor Monthly",  "call":"Check-In Call",          "limit_mult":0.8},
    "C":{"color":"#FF8C42","rgba":"255,140,66",  "label":"High Risk",     "action":"Reduce Limit 50%", "call":"Payment Follow-Up Call", "limit_mult":0.5},
    "D":{"color":"#FF3860","rgba":"255,56,96",   "label":"Critical Risk", "action":"Suspend Credit",   "call":"Urgent Collection Call", "limit_mult":0.0},
}
CALL_SCRIPTS = {
    "A":"Bhai {name}, aapka payment record bahut accha hai. Aapke liye hum credit limit badha rahe hain. Thank you for always paying on time!",
    "B":"Hello {name} bhai, bas ek friendly call tha. Kuch invoices thoda late ho rahe hain — koi problem hai toh batao, hum mil ke sort kar lete hain.",
    "C":"Hello {name} bhai, aapke {amount} ke invoices overdue hain. Kab tak payment ho sakti hai? Batao toh hum account active rakh sakte hain.",
    "D":"Hello {name} bhai, urgent baat karni thi. {amount} bahut time se pending hai. Aaj payment nahi hua toh hume supply band karni padegi. Please abhi baat karo.",
}
OVERDUE_CAP = 45
WA_NUMBER   = "919439493613"

# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def fmt(x):
    """Short Indian format for KPIs — lakhs and crores."""
    try:
        v = float(x)
        if v >= 10_000_000: return "₹{:.2f} Cr".format(v / 10_000_000)
        elif v >= 100_000:  return "₹{:.2f} L".format(v / 100_000)
        elif v >= 1_000:    return "₹{:.1f}K".format(v / 1_000)
        else:               return "₹{:.0f}".format(v)
    except: return "₹0"

def fmt_full(x):
    """Full Indian number format — 2,77,500 style."""
    try:
        v = int(float(x))
        s = str(v)
        if len(s) <= 3: return "₹" + s
        last3 = s[-3:]
        rest  = s[:-3]
        parts = []
        while len(rest) > 2:
            parts.append(rest[-2:])
            rest = rest[:-2]
        if rest: parts.append(rest)
        parts.reverse()
        return "₹" + ",".join(parts) + "," + last3
    except: return "₹0"

def card_html(gk, cnt):
    m = GRADE_META[gk]
    return (
        '<div style="background:rgba('+m["rgba"]+',0.08);border:1px solid '
        +m["color"]+'40;border-radius:14px;padding:16px;">'
        '<div style="color:'+m["color"]+';font-weight:700;font-size:15px;margin-bottom:6px">'
        'Grade '+gk+' &middot; '+str(cnt)+' customers</div>'
        '<div style="color:#C8D8E8;font-size:12px;margin-bottom:4px">&#128203; '+m["action"]+'</div>'
        '<div style="color:#C8D8E8;font-size:12px">&#128222; '+m["call"]+'</div></div>'
    )

def script_html(gk, script, out_str, overdue, action):
    m = GRADE_META[gk]
    return (
        '<div style="background:rgba('+m["rgba"]+',0.08);border:1px solid '
        +m["color"]+'40;border-radius:12px;padding:16px;margin-bottom:12px;">'
        '<div style="font-size:11px;color:'+m["color"]+';letter-spacing:0.1em;margin-bottom:8px">SUGGESTED SCRIPT</div>'
        '<div style="color:#C8D8E8;font-size:14px;line-height:1.7">'+str(script)+'</div></div>'
        '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;">'
        '<div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:12px">'
        '<div style="font-size:10px;color:#8899AA">Outstanding</div>'
        '<div style="font-size:14px;font-weight:700;color:'+m["color"]+'">'+out_str+'</div></div>'
        '<div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:12px">'
        '<div style="font-size:10px;color:#8899AA">Max Overdue</div>'
        '<div style="font-size:14px;font-weight:700;color:#C8D8E8">'+str(int(overdue))+' days</div></div>'
        '<div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:12px">'
        '<div style="font-size:10px;color:#8899AA">Credit Action</div>'
        '<div style="font-size:13px;font-weight:600;color:#C8D8E8">'+str(action)+'</div></div></div>'
    )

def trend_badge(trend):
    cfg = {
        "Improving":("#00E5A0","0,229,160","&#8593; Improving"),
        "Worsening":("#FF3860","255,56,96","&#8595; Worsening"),
        "Stable":   ("#FFD166","255,209,102","&#8594; Stable"),
        "New":      ("#8899AA","136,153,170","&#8212; New / Low Data"),
    }
    c,rgba,label = cfg.get(trend, cfg["New"])
    return '<span style="background:rgba('+rgba+',0.15);color:'+c+';padding:2px 10px;border-radius:20px;font-size:11px;font-weight:600">'+label+'</span>'

# ══════════════════════════════════════════════════════════════════════════════
#  DATA
# ══════════════════════════════════════════════════════════════════════════════
def generate_example_data():
    """
    Realistic FMCG India data:
    - Invoice window: last 90 days only (not 300)
    - Due dates: 14-21 days credit period (FMCG standard)
    - Overdue: max 60 days (realistic, not 180)
    - Amounts: Rs. 5,000-50,000 (typical FMCG invoice)
    - Payment patterns reflect real distributor behaviour
    """
    np.random.seed(42)
    # Realistic Indian FMCG customer names
    customers = [
        "Raju Kirana Stores",
        "Mehta General Traders",
        "Shree Ram Distributors",
        "Patel Wholesale Mart",
        "Krishna Retail Hub",
        "Sharma & Sons Traders",
        "Gupta FMCG Supplies",
        "Vijay Super Store",
    ]
    data   = []
    today  = pd.Timestamp(datetime.now().date())

    # Each customer gets a payment personality
    personalities = {
        "Raju Kirana Stores":       "good",      # Grade A — always on time
        "Mehta General Traders":    "mostly_good",# Grade B — slight delays
        "Shree Ram Distributors":   "average",   # Grade B — moderate delays
        "Patel Wholesale Mart":     "late",       # Grade C — regularly late
        "Krishna Retail Hub":       "good",       # Grade A
        "Sharma & Sons Traders":    "very_late",  # Grade D — critical
        "Gupta FMCG Supplies":      "average",    # Grade B/C
        "Vijay Super Store":        "partial",    # Grade C — partial payments
    }

    for cust in customers:
        personality = personalities[cust]
        n_invoices  = int(np.random.randint(4, 9))

        for i in range(n_invoices):
            # Invoices within last 90 days — realistic window
            days_ago = int(np.random.randint(5, 90))
            inv_date = today - pd.Timedelta(days=days_ago)
            # FMCG credit period: 14-21 days
            credit_days = int(np.random.choice([14, 21]))
            due_date    = inv_date + pd.Timedelta(days=credit_days)
            # Realistic amounts: Rs. 5,000 - 50,000
            amount = int(np.random.choice([
                5000, 8000, 10000, 12000, 15000,
                18000, 20000, 25000, 30000, 40000, 50000
            ]))

            # Payment behaviour by personality
            if personality == "good":
                # Pays on time or 1-3 days early
                paid = amount
                pay_date = due_date - pd.Timedelta(days=int(np.random.randint(0,4)))

            elif personality == "mostly_good":
                r = float(np.random.rand())
                if r < 0.7:
                    paid = amount
                    pay_date = due_date + pd.Timedelta(days=int(np.random.randint(0,8)))
                else:
                    paid = amount
                    pay_date = due_date + pd.Timedelta(days=int(np.random.randint(8,18)))

            elif personality == "average":
                r = float(np.random.rand())
                if r < 0.5:
                    paid = amount
                    pay_date = due_date + pd.Timedelta(days=int(np.random.randint(5,20)))
                elif r < 0.8:
                    paid = round(amount * float(np.random.uniform(0.5, 0.9)))
                    pay_date = due_date + pd.Timedelta(days=int(np.random.randint(0,15)))
                else:
                    paid = 0; pay_date = pd.NaT

            elif personality == "late":
                r = float(np.random.rand())
                if r < 0.4:
                    paid = amount
                    pay_date = due_date + pd.Timedelta(days=int(np.random.randint(20,45)))
                elif r < 0.7:
                    paid = round(amount * float(np.random.uniform(0.3, 0.6)))
                    pay_date = due_date + pd.Timedelta(days=int(np.random.randint(10,30)))
                else:
                    paid = 0; pay_date = pd.NaT

            elif personality == "very_late":
                # Grade D — mostly unpaid or very late
                r = float(np.random.rand())
                if r < 0.3:
                    paid = round(amount * float(np.random.uniform(0.1, 0.3)))
                    pay_date = due_date + pd.Timedelta(days=int(np.random.randint(30,60)))
                else:
                    paid = 0; pay_date = pd.NaT

            elif personality == "partial":
                # Pays partial amounts, rarely full
                r = float(np.random.rand())
                if r < 0.2:
                    paid = amount
                    pay_date = due_date + pd.Timedelta(days=int(np.random.randint(15,35)))
                else:
                    paid = round(amount * float(np.random.uniform(0.2, 0.7)))
                    pay_date = due_date + pd.Timedelta(days=int(np.random.randint(5,25))) if float(np.random.rand()) > 0.3 else pd.NaT

            else:
                paid = 0; pay_date = pd.NaT

            data.append({
                "customer_name": cust,
                "invoice_no":    "INV-{}-{:03d}".format(cust[:3].upper(), i+1),
                "invoice_date":  inv_date,
                "due_date":      due_date,
                "amount":        amount,
                "paid_amount":   round(float(paid)),
                "payment_date":  pay_date,
            })

    return pd.DataFrame(data)

def clean_data(df):
    df = df.copy()
    df.drop(columns=[c for c in ["outstanding","fully_paid","overdue_days","paid_late"] if c in df.columns], inplace=True)
    df.columns = df.columns.str.lower().str.strip().str.replace(" ","_")
    for c in ["invoice_date","due_date","payment_date"]:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    df["amount"]      = pd.to_numeric(df["amount"],      errors="coerce").fillna(0)
    df["paid_amount"] = pd.to_numeric(df["paid_amount"], errors="coerce").fillna(0)
    if "payment_date" not in df.columns: df["payment_date"] = pd.NaT
    return df[df["amount"]>0].copy()

def calc_metrics(df, today):
    df = df.copy()
    df["outstanding"]  = (df["amount"]-df["paid_amount"]).clip(lower=0)
    df["fully_paid"]   = df["paid_amount"]>=df["amount"]
    df["overdue_days"] = 0
    df["paid_late"]    = False
    mask_unpaid = (df["outstanding"]>0)&(df["due_date"]<today)
    df.loc[mask_unpaid,"overdue_days"] = (today-df.loc[mask_unpaid,"due_date"]).dt.days.astype(int)
    mask_late = df["fully_paid"]&df["payment_date"].notna()&(df["payment_date"]>df["due_date"])
    df.loc[mask_late,"overdue_days"] = (df.loc[mask_late,"payment_date"]-df.loc[mask_late,"due_date"]).dt.days.astype(int)
    df.loc[mask_late,"paid_late"] = True
    df["overdue_days"] = df["overdue_days"].clip(lower=0,upper=60)
    return df

def predict_behaviour(inv_df):
    paid = inv_df[inv_df["fully_paid"]==True].copy().sort_values("invoice_date")
    total_inv  = len(inv_df)
    paid_count = len(paid)

    if paid_count < 3:
        if total_inv == 0:
            return "New", 0, "No invoice history yet."
        unpaid_pct = round(((total_inv - paid_count) / total_inv) * 100)
        return "New", 0, "Only {} paid invoice(s). Need 3+ to predict. {}% invoices unpaid.".format(paid_count, unpaid_pct)

    mid             = len(paid) // 2
    first_half_avg  = paid.iloc[:mid]["overdue_days"].mean()
    second_half_avg = paid.iloc[mid:]["overdue_days"].mean()
    delta   = second_half_avg - first_half_avg
    last3   = paid.tail(3)["overdue_days"].mean()
    overall = paid["overdue_days"].mean()
    pay_rate = paid_count / total_inv if total_inv > 0 else 0

    if (delta > 5 and last3 > overall) or last3 > overall * 1.3:
        msg = "Payment delays increasing. Last 3 invoices averaged {:.0f} days late vs {:.0f} days overall.".format(last3, overall)
        if pay_rate < 0.6:
            msg += " Only {:.0f}% invoices fully paid — high default risk.".format(pay_rate * 100)
        return "Worsening", round(last3, 1), msg
    elif (delta < -5 and last3 < overall) or last3 < overall * 0.7:
        return "Improving", round(last3, 1), "Payment behaviour improving. Last 3 invoices averaged {:.0f} days late vs {:.0f} days overall.".format(last3, overall)
    else:
        return "Stable", round(last3, 1), "Consistent payment pattern. Average delay {:.0f} days. Pay rate {:.0f}%.".format(overall, pay_rate * 100)

def calc_ageing(df):
    df = df[df["outstanding"]>0].copy()
    def bucket(d):
        if d<=0:    return "Current"
        elif d<=15: return "1-15 days"
        elif d<=30: return "16-30 days"
        elif d<=45: return "31-45 days"
        else:       return "45+ days"
    df["bucket"] = df["overdue_days"].apply(bucket)
    order = ["Current","1-15 days","16-30 days","31-45 days","45+ days"]
    ag    = df.groupby(["customer_name","bucket"])["outstanding"].sum().reset_index()
    pivot = ag.pivot(index="customer_name",columns="bucket",values="outstanding").fillna(0)
    for col in order:
        if col not in pivot.columns: pivot[col]=0
    pivot = pivot[order].reset_index()
    pivot["Total Outstanding"] = pivot[order].sum(axis=1)
    return pivot

def score_customer(row):
    od = min(row["max_overdue"]/OVERDUE_CAP,1)*40
    ou = (row["total_outstanding"]/row["total_amount"])*40 if row["total_amount"]>0 else 0
    pr = row["total_paid"]/row["total_amount"] if row["total_amount"]>0 else 0
    lr = row["late_count"]/row["paid_count"]   if row["paid_count"]>0   else 1
    return min(round(od+ou+min((1-pr)*10+lr*10,20)),100)

def get_grade(s):
    return "A" if s<=10 else "B" if s<=30 else "C" if s<=55 else "D"

def aggregate(df):
    g = df.groupby("customer_name").agg(
        total_invoices=("invoice_no","count"), total_amount=("amount","sum"),
        total_paid=("paid_amount","sum"),      max_overdue=("overdue_days","max"),
        late_count=("paid_late","sum"),        paid_count=("fully_paid","sum"),
    ).reset_index()
    g["total_outstanding"] = (g["total_amount"]-g["total_paid"]).clip(lower=0)
    g["avg_delay"] = g["customer_name"].map(
        df[df["paid_late"]].groupby("customer_name")["overdue_days"].mean()).fillna(0).round(1)
    rows = []
    for _,r in g.iterrows():
        sc=score_customer(r); gr=get_grade(sc); m=GRADE_META[gr]
        trend,last3,pred = predict_behaviour(df[df["customer_name"]==r["customer_name"]])
        rows.append({
            "Customer":r["customer_name"],"Invoices":int(r["total_invoices"]),
            "Total Credit":round(float(r["total_amount"]),2),
            "Total Paid":round(float(r["total_paid"]),2),
            "Outstanding":round(float(r["total_outstanding"]),2),
            "Max Overdue(d)":int(r["max_overdue"]),"Avg Delay(d)":float(r["avg_delay"]),
            "Risk Score":sc,"Risk Grade":gr,"Grade Label":m["label"],
            "Suggested Limit":round(float(r["total_amount"])*m["limit_mult"],2),
            "Credit Action":m["action"],"Call Type":m["call"],
            "Call Script":CALL_SCRIPTS[gr].format(name=r["customer_name"],amount=fmt(r["total_outstanding"])),
            "Behaviour Trend":trend,"Recent Avg Delay":last3,"Behaviour Insight":pred,
        })
    return pd.DataFrame(rows).sort_values("Risk Score",ascending=False).reset_index(drop=True)

# ══════════════════════════════════════════════════════════════════════════════
#  AUTO LOAD EXAMPLE DATA — always fresh, no cache
# ══════════════════════════════════════════════════════════════════════════════
today = pd.Timestamp(datetime.now().date())

raw   = generate_example_data()
clean = clean_data(raw)
inv   = calc_metrics(clean, today)
summ  = aggregate(inv)
age   = calc_ageing(inv)

summary = summ
df_inv  = inv
ageing  = age

# ══════════════════════════════════════════════════════════════════════════════
#  DEMO BANNER
# ══════════════════════════════════════════════════════════════════════════════
wa_msg = "Hi Sanskar! I tried the CreditPulse demo and want to get my own account."
wa_url = "https://wa.me/{}?text={}".format(WA_NUMBER, wa_msg.replace(" ","%20"))

st.markdown("""
<div style="background:linear-gradient(135deg,rgba(91,158,244,0.12),rgba(0,229,160,0.08));
  border:1px solid rgba(91,158,244,0.25);border-radius:14px;padding:16px 24px;
  display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;flex-wrap:wrap;gap:12px;">
  <div>
    <div style="font-size:13px;font-weight:700;color:#5B9EF4;margin-bottom:4px">
      ⚡ You are viewing a DEMO — Sample data only
    </div>
    <div style="font-size:12px;color:#8899AA;">
      This is not real data. Get your own private account to track your actual customers.
    </div>
  </div>
  <a href="{}" target="_blank"
    style="background:#00E5A0;color:#04080F;padding:10px 20px;border-radius:10px;
    font-weight:700;font-size:13px;text-decoration:none;white-space:nowrap;">
    💬 Get My Account →
  </a>
</div>
""".format(wa_url), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="padding:8px 0 20px;position:relative;">
  <div style="position:absolute;top:0;left:0;right:0;height:3px;
    background:linear-gradient(90deg,#5B9EF4,#00E5A0,#FFD166,#FF3860);
    border-radius:2px;opacity:0.7;"></div>
  <div style="padding-top:16px;display:inline-flex;align-items:center;gap:12px;
    background:linear-gradient(135deg,rgba(91,158,244,0.1),rgba(0,229,160,0.06));
    border:1px solid rgba(91,158,244,0.2);border-radius:16px;padding:10px 20px;">
    <span style="font-size:24px;">&#9889;</span>
    <span style="font-family:'Syne',sans-serif;font-size:26px;font-weight:800;letter-spacing:-0.03em;
      background:linear-gradient(135deg,#5B9EF4 0%,#00E5A0 60%,#FFD166 100%);
      -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">CreditPulse</span>
    <span style="width:1px;height:20px;background:rgba(255,255,255,0.15);"></span>
    <span style="font-size:12px;color:#8899AA;letter-spacing:0.06em;">DEMO MODE</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚡ CreditPulse Demo")
    st.markdown("---")
    st.markdown("""
    <div style="background:rgba(0,229,160,0.08);border:1px solid rgba(0,229,160,0.2);
      border-radius:10px;padding:12px;margin-bottom:12px;">
      <div style="color:#00E5A0;font-size:12px;font-weight:700;margin-bottom:6px">
        &#9679; Demo Mode — Sample Data
      </div>
      <div style="color:#8899AA;font-size:11px;line-height:1.6;">
        This demo uses 8 fictional FMCG customers. Your real account will use your actual invoice data.
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Risk Grade Legend**")
    for gk,m in GRADE_META.items():
        st.markdown('<span style="color:'+m["color"]+'">&#9632;</span> **Grade '+gk+'** — '+m["label"],unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**Scoring — FMCG India**")
    st.caption("Overdue cap: 45 days\nOverdue: 40 pts · Outstanding: 40 pts · Behaviour: 20 pts")
    st.markdown("---")

    wa_msg_side = "Hi Sanskar! I tried the CreditPulse demo and want to know more."
    wa_url_side = "https://wa.me/{}?text={}".format(WA_NUMBER, wa_msg_side.replace(" ","%20"))
    st.markdown("""
    <a href="{}" target="_blank"
      style="display:block;background:#00E5A0;color:#04080F;padding:12px 16px;
      border-radius:10px;font-weight:700;font-size:13px;text-decoration:none;
      text-align:center;margin-top:8px;">
      💬 Get My Own Account
    </a>
    """.format(wa_url_side), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  KPI CARDS — custom HTML, never truncate
# ══════════════════════════════════════════════════════════════════════════════
def kpi_card(label, value, color="#F0F4F8", sub=None):
    sub_html = '<div style="font-size:11px;color:#FF3860;margin-top:4px;">'+sub+'</div>' if sub else ''
    return (
        '<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);'
        'border-radius:14px;padding:16px 18px;">'
        '<div style="font-size:11px;color:#8899AA;letter-spacing:0.08em;'
        'text-transform:uppercase;margin-bottom:8px;">'+label+'</div>'
        '<div style="font-family:\'DM Mono\',monospace;font-size:clamp(13px,1.6vw,20px);'
        'font-weight:700;color:'+color+';word-break:break-word;line-height:1.3;">'+value+'</div>'
        +sub_html+
        '</div>'
    )

k1,k2,k3,k4,k5 = st.columns(5)
k1.markdown(kpi_card("Customers",    str(len(summary))), unsafe_allow_html=True)
k2.markdown(kpi_card("Total Credit", fmt_full(summary["Total Credit"].sum()), "#5B9EF4"), unsafe_allow_html=True)
k3.markdown(kpi_card("Total Paid",   fmt_full(summary["Total Paid"].sum()),   "#00E5A0"), unsafe_allow_html=True)
k4.markdown(kpi_card("Outstanding",  fmt_full(summary["Outstanding"].sum()),  "#FFD166"), unsafe_allow_html=True)
k5.markdown(kpi_card("Critical (D)", str(int((summary["Risk Grade"]=="D").sum())), "#FF3860", "⚠ Immediate action needed"), unsafe_allow_html=True)
st.markdown("<div style='height:16px'/>",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  CHARTS
# ══════════════════════════════════════════════════════════════════════════════
ch1,ch2 = st.columns([1,2])
with ch1:
    st.markdown("**Risk Grade Breakdown**")
    gc = summary["Risk Grade"].value_counts().reindex(["A","B","C","D"],fill_value=0)
    for gk,cnt in gc.items():
        m  = GRADE_META[gk]
        pv = round((cnt/len(summary))*100) if len(summary)>0 else 0
        st.markdown(
            '<div style="margin-bottom:12px;">'
            '<div style="display:flex;justify-content:space-between;margin-bottom:4px;">'
            '<span style="color:'+m["color"]+';font-weight:600;font-size:13px">Grade '+gk+' — '+m["label"]+'</span>'
            '<span style="color:#8899AA;font-size:12px">'+str(cnt)+' ('+str(pv)+'%)</span></div>'
            '<div style="background:rgba(255,255,255,0.06);border-radius:6px;height:10px;">'
            '<div style="width:'+str(max(pv,2))+'%;background:'+m["color"]+';height:10px;border-radius:6px;"></div>'
            '</div></div>', unsafe_allow_html=True)

with ch2:
    st.markdown("**Outstanding Amount by Customer**")
    # Only show customers with outstanding > 0
    bar_df = summary[summary["Outstanding"] > 0][["Customer","Outstanding","Risk Grade"]]\
             .copy().sort_values("Outstanding", ascending=True)

    if len(bar_df) == 0:
        st.markdown(
            '<div style="background:rgba(0,229,160,0.06);border:1px solid rgba(0,229,160,0.2);'
            'border-radius:12px;padding:32px;text-align:center;">'
            '<div style="font-size:28px;margin-bottom:8px">🎉</div>'
            '<div style="color:#00E5A0;font-weight:700;font-size:15px">All customers are fully paid!</div>'
            '<div style="color:#8899AA;font-size:12px;margin-top:4px">No outstanding amounts.</div>'
            '</div>', unsafe_allow_html=True)
    else:
        bar_colors = [GRADE_META[g]["color"] for g in bar_df["Risk Grade"]]
        bar_labels = [fmt_full(v) for v in bar_df["Outstanding"]]
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=bar_df["Outstanding"],
            y=bar_df["Customer"],
            orientation="h",
            marker=dict(color=bar_colors, line=dict(width=0), opacity=0.9),
            text=bar_labels,
            textposition="outside",
            textfont=dict(size=11, color="#C8D8E8", family="DM Mono"),
            hovertemplate="<b>%{y}</b><br>Outstanding: %{text}<br>Grade: %{customdata}<extra></extra>",
            customdata=bar_df["Risk Grade"],
        ))
        chart_height = max(280, len(bar_df) * 42 + 60)
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#C8D8E8",
            margin=dict(t=10, b=20, l=10, r=140),
            height=chart_height, bargap=0.35,
            xaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickformat=",.0f",
                       title="", tickfont=dict(size=10), showline=False, zeroline=False),
            yaxis=dict(gridcolor="rgba(0,0,0,0)", title="",
                       automargin=True, tickfont=dict(size=12, family="Inter")),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

st.markdown("---")
rc = st.columns(4)
for col,(gk,m) in zip(rc,GRADE_META.items()):
    col.markdown(card_html(gk,int((summary["Risk Grade"]==gk).sum())),unsafe_allow_html=True)
st.markdown("<div style='height:20px'/>",unsafe_allow_html=True)

grade_filter = st.selectbox("Filter by Risk Grade",["ALL","A","B","C","D"])
filtered = summary.copy() if grade_filter=="ALL" else summary[summary["Risk Grade"]==grade_filter].copy()
st.caption("Showing {} of {} customers".format(len(filtered),len(summary)))

# ══════════════════════════════════════════════════════════════════════════════
#  TABS
# ══════════════════════════════════════════════════════════════════════════════
tab_risk,tab_beh,tab_call,tab_age,tab_inv = st.tabs([
    "📊 Risk Analysis","🔮 Behaviour Predictor",
    "📞 Call Table","📅 Ageing Report","🧾 Invoice Detail",
])

with tab_risk:
    disp = filtered[["Customer","Invoices","Risk Score","Risk Grade","Grade Label",
                      "Total Credit","Total Paid","Outstanding","Max Overdue(d)",
                      "Avg Delay(d)","Suggested Limit","Credit Action","Behaviour Trend"]].copy()
    for c in ["Total Credit","Total Paid","Outstanding","Suggested Limit"]:
        disp[c] = disp[c].apply(fmt_full)
    st.dataframe(disp,use_container_width=True,hide_index=True,
        column_config={
            "Risk Score":      st.column_config.ProgressColumn("Score",min_value=0,max_value=100,format="%d"),
            "Risk Grade":      st.column_config.TextColumn("Grade",width="small"),
            "Max Overdue(d)":  st.column_config.NumberColumn("Max Overdue",format="%d days"),
            "Avg Delay(d)":    st.column_config.NumberColumn("Avg Delay",format="%.1f days"),
            "Invoices":        st.column_config.NumberColumn("Invoices",format="%d"),
            "Behaviour Trend": st.column_config.TextColumn("Trend"),
        })
    out = io.BytesIO()
    with pd.ExcelWriter(out,engine="openpyxl") as w:
        summary.to_excel(w,sheet_name="Customer Risk",index=False)
        df_inv.to_excel(w, sheet_name="Invoice Data", index=False)
        ageing.to_excel(w, sheet_name="Ageing Report",index=False)
    st.download_button("⬇ Download Sample Excel Report",out.getvalue(),"sample_credit_report.xlsx")

with tab_beh:
    st.markdown("### 🔮 Payment Behaviour Predictor")
    st.caption("Analyses invoice history to predict if customers will pay late. More history = more accurate.")
    tc1,tc2,tc3,tc4 = st.columns(4)
    tc = filtered["Behaviour Trend"].value_counts()
    tc1.metric("Improving",      str(tc.get("Improving",0)), delta="Good trend")
    tc2.metric("Stable",         str(tc.get("Stable",0)))
    tc3.metric("Worsening",      str(tc.get("Worsening",0)), delta="Watch these", delta_color="inverse")
    tc4.metric("New / Low Data", str(tc.get("New",0)))
    st.markdown("<div style='height:12px'/>",unsafe_allow_html=True)
    for _,row in filtered.iterrows():
        m      = GRADE_META[row["Risk Grade"]]
        tc_clr = "#00E5A0" if row["Behaviour Trend"]=="Improving" else "#FF3860" if row["Behaviour Trend"]=="Worsening" else "#FFD166" if row["Behaviour Trend"]=="Stable" else "#8899AA"
        st.markdown(
            '<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:16px;margin-bottom:10px;">'
            '<div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;">'
            '<div style="font-weight:700;color:#C8D8E8;font-size:14px;">'+str(row["Customer"])+'</div>'
            +trend_badge(row["Behaviour Trend"])+
            '<div style="margin-left:auto;font-size:12px;color:'+m["color"]+'">Grade '+row["Risk Grade"]+'</div></div>'
            '<div style="font-size:13px;color:#C8D8E8;margin-bottom:10px;">'+row["Behaviour Insight"]+'</div>'
            '<div style="display:flex;gap:20px;">'
            '<span style="font-size:11px;color:#8899AA">Overall avg delay: <b style="color:#C8D8E8">'+str(row["Avg Delay(d)"])+'d</b></span>'
            '<span style="font-size:11px;color:#8899AA">Recent avg delay: <b style="color:'+tc_clr+'">'+str(row["Recent Avg Delay"])+'d</b></span>'
            '<span style="font-size:11px;color:#8899AA">Outstanding: <b style="color:'+m["color"]+'">'+fmt(row["Outstanding"])+'</b></span>'
            '</div></div>', unsafe_allow_html=True)

with tab_call:
    cd = filtered[["Customer","Risk Grade","Outstanding","Max Overdue(d)","Call Type","Credit Action","Call Script"]].copy()
    cd.insert(0,"Priority",range(1,len(cd)+1))
    cd["Outstanding"]    = cd["Outstanding"].apply(fmt_full)
    cd["Max Overdue(d)"] = cd["Max Overdue(d)"].apply(lambda x:"{} days".format(int(x)) if x>0 else "On time")
    st.dataframe(cd,use_container_width=True,hide_index=True,
        column_config={
            "Priority":   st.column_config.NumberColumn("#",width="small"),
            "Risk Grade": st.column_config.TextColumn("Grade",width="small"),
            "Call Script":st.column_config.TextColumn("Script",width="large"),
        })
    st.markdown("---")
    st.markdown("### Call Scripts")
    for _,row in filtered.iterrows():
        gk = row["Risk Grade"]
        with st.expander("{} | {} | {} | {}".format(gk,row["Customer"],row["Call Type"],fmt(row["Outstanding"]))):
            st.markdown(script_html(gk,row["Call Script"],fmt(row["Outstanding"]),row["Max Overdue(d)"],row["Credit Action"]),unsafe_allow_html=True)
            st.info("In your real account, you can log call outcomes here and download them as Excel.")

with tab_age:
    st.markdown("### Ageing Report")
    st.caption("FMCG India buckets: Current / 1-15 / 16-30 / 31-45 / 45+ days")
    ad = ageing.copy()
    for c in ["Current","1-15 days","16-30 days","31-45 days","45+ days","Total Outstanding"]:
        if c in ad.columns: ad[c]=ad[c].apply(fmt_full)
    ad.rename(columns={"customer_name":"Customer"},inplace=True)
    st.dataframe(ad,use_container_width=True,hide_index=True)
    buckets = ["Current","1-15 days","16-30 days","31-45 days","45+ days"]
    melt    = ageing.melt(id_vars="customer_name",value_vars=buckets,var_name="Bucket",value_name="Amount")
    colors  = {"Current":"#8899AA","1-15 days":"#FFD166","16-30 days":"#FF8C42","31-45 days":"#FF5733","45+ days":"#FF3860"}
    fig_age = go.Figure()
    for b in buckets:
        sub = melt[melt["Bucket"]==b]
        fig_age.add_trace(go.Bar(x=sub["customer_name"],y=sub["Amount"],name=b,marker_color=colors[b]))
    fig_age.update_layout(barmode="stack",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        font_color="#C8D8E8",legend=dict(font=dict(color="#C8D8E8"),orientation="h",y=-0.2),
        xaxis=dict(tickangle=-20,gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        margin=dict(t=10,b=60,l=0,r=0),height=max(320,len(ageing)*28+80))
    st.plotly_chart(fig_age,use_container_width=True)

with tab_inv:
    st.markdown("### Customer Invoice Detail")
    sel      = st.selectbox("Select Customer",summary["Customer"].tolist(),key="inv_cust")
    cust_inv = df_inv[df_inv["customer_name"]==sel].copy()
    cust_row = summary[summary["Customer"]==sel].iloc[0]
    m        = GRADE_META[cust_row["Risk Grade"]]
    ic1,ic2,ic3,ic4,ic5 = st.columns(5)
    ic1.metric("Risk Grade",     "{} — {}".format(cust_row["Risk Grade"],cust_row["Grade Label"]))
    ic2.metric("Risk Score",     str(cust_row["Risk Score"]))
    ic3.metric("Total Invoices", str(cust_row["Invoices"]))
    ic4.metric("Outstanding",    fmt(cust_row["Outstanding"]))
    ic5.metric("Suggested Limit",fmt(cust_row["Suggested Limit"]))
    paid_pct = round((float(cust_row["Total Paid"])/float(cust_row["Total Credit"]))*100) if cust_row["Total Credit"]>0 else 0
    st.markdown(
        '<div style="margin:12px 0 16px;"><div style="display:flex;justify-content:space-between;margin-bottom:4px;">'
        '<span style="color:#8899AA;font-size:12px">Payment Progress</span>'
        '<span style="color:#C8D8E8;font-size:12px">'+str(paid_pct)+'% paid</span></div>'
        '<div style="background:rgba(255,56,96,0.25);border-radius:6px;height:8px;">'
        '<div style="width:'+str(paid_pct)+'%;background:#00E5A0;height:8px;border-radius:6px;"></div>'
        '</div></div>', unsafe_allow_html=True)
    trend = cust_row["Behaviour Trend"]
    st.markdown(
        '<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);'
        'border-radius:10px;padding:14px;margin-bottom:16px;display:flex;align-items:center;gap:12px;">'
        +trend_badge(trend)+
        '<div style="font-size:13px;color:#C8D8E8;">'+cust_row["Behaviour Insight"]+'</div></div>',
        unsafe_allow_html=True)
    id_ = cust_inv[["invoice_no","invoice_date","due_date","amount","paid_amount","outstanding","overdue_days","paid_late","fully_paid"]].copy()
    id_.columns = ["Invoice","Invoice Date","Due Date","Amount","Paid","Outstanding","Overdue(d)","Paid Late","Fully Paid"]
    for c in ["Amount","Paid","Outstanding"]: id_[c]=id_[c].apply(fmt_full)
    st.dataframe(id_,use_container_width=True,hide_index=True,
        column_config={
            "Overdue(d)": st.column_config.NumberColumn("Overdue",format="%d days"),
            "Paid Late":  st.column_config.CheckboxColumn("Paid Late"),
            "Fully Paid": st.column_config.CheckboxColumn("Fully Paid"),
        })

# ══════════════════════════════════════════════════════════════════════════════
#  BOTTOM CTA BANNER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("<div style='height:32px'/>", unsafe_allow_html=True)
st.markdown("""
<div style="background:linear-gradient(135deg,rgba(0,229,160,0.08),rgba(91,158,244,0.08));
  border:1px solid rgba(0,229,160,0.2);border-radius:16px;padding:32px;text-align:center;">
  <div style="font-size:22px;font-weight:800;color:#F0F4F8;margin-bottom:8px;letter-spacing:-0.02em;">
    Ready to track your real customers?
  </div>
  <div style="font-size:14px;color:#8899AA;margin-bottom:24px;">
    Get your own private CreditPulse account. Upload your invoices and see risk scores in seconds.
  </div>
  <a href="{}" target="_blank"
    style="display:inline-block;background:#00E5A0;color:#04080F;padding:14px 32px;
    border-radius:10px;font-weight:800;font-size:15px;text-decoration:none;">
    💬 Message Sanskar on WhatsApp →
  </a>
</div>
""".format(wa_url), unsafe_allow_html=True)
