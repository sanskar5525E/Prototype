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
