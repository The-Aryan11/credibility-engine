"""
VeriSmart - Final Polish
"""
import streamlit as st
import requests
import pandas as pd
from fpdf import FPDF
import os
import urllib.parse
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- CONFIG ---
BACKEND_URL = os.getenv("BACKEND_URL", "https://aryan12345ark-credibility-backend.hf.space")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "") 
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")

st.set_page_config(page_title="VeriSmart", page_icon="🛡️", layout="wide")
st_autorefresh(interval=60000, key="refresh")

# Initialize State
if "history" not in st.session_state: st.session_state.history = []
if "fetched_news" not in st.session_state: st.session_state.fetched_news = [] # List to accumulate
if "claim_input" not in st.session_state: st.session_state.claim_input = ""
if "trigger_analyze" not in st.session_state: st.session_state.trigger_analyze = False

# --- QUERY PARAMS (Share Link) ---
if "claim" in st.query_params:
    st.session_state.claim_input = st.query_params["claim"]
    st.session_state.trigger_analyze = True

# --- PDF GENERATOR (Fixed) ---
def generate_pdf(claim, data, sources):
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, 'VeriSmart Intelligence Report', 0, 1, 'C')
            self.ln(5)
    
    try:
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        def clean(t): return str(t).encode('latin-1', 'replace').decode('latin-1')

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Claim:", 0, 1)
        pdf.set_font("Arial", '', 12)
        pdf.multi_cell(0, 6, clean(claim))
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"Verdict: {data.get('verdict')} ({data.get('score')}%)", 0, 1)
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Analysis:", 0, 1)
        pdf.set_font("Arial", '', 11)
        pdf.multi_cell(0, 6, clean(data.get('reasoning')))
        pdf.ln(5)
        
        if sources:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "Sources:", 0, 1)
            pdf.set_font("Arial", '', 10)
            for s in sources:
                name = s.get('name', 'Unknown') if isinstance(s, dict) else str(s)
                pdf.cell(0, 6, f"- {clean(name)}", 0, 1)

        return bytes(pdf.output())
    except:
        return None

# --- CSS ---
st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: #e2e8f0; }
    .main-header { background: linear-gradient(135deg, #1e40af, #3b82f6); padding: 2rem; border-radius: 15px; text-align: center; margin-bottom: 20px; }
    [data-testid="stSidebar"] { background-color: #1e293b; border-right: 1px solid #334155; }
    .metric-card { background: #1e293b; padding: 15px; border-radius: 10px; border: 1px solid #334155; text-align: center; }
    .history-card { background: #1e293b; padding: 15px; border-radius: 8px; border-left: 4px solid #3b82f6; margin-bottom: 10px; }
    .footer { text-align: center; margin-top: 50px; color: #64748b; font-size: 0.8rem; border-top: 1px solid #334155; padding: 20px; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    .pilot-badge { position: fixed; top: 1rem; right: 1rem; background: #10b981; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: bold; }
</style>
<div class="pilot-badge">🟢 Active</div>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ VeriSmart")
    
    # Live News Fetch (Cumulative)
    st.subheader("📰 Live Feed")
    topic = st.selectbox("Topic", ["General", "Health", "Politics", "Science"])
    if st.button("🔄 Fetch News"):
        if GNEWS_API_KEY:
            try:
                url = f"https://gnews.io/api/v4/top-headlines?category={topic.lower()}&lang=en&apikey={GNEWS_API_KEY}"
                data = requests.get(url).json()
                articles = data.get('articles', [])[:3]
                
                # Ingest to Backend
                for a in articles:
                    requests.post(f"{BACKEND_URL}/ingest", json={"text": f"{a['title']}\n{a['description']}", "source": a['source']['name']})
                
                # Accumulate in Session State (Fix 1)
                st.session_state.fetched_news.extend(articles)
                st.success(f"Added {len(articles)} articles!")
            except: st.error("Feed Error")
    
    st.markdown("---")
    st.caption("© 2026 Aryan & Khushboo")

# --- MAIN ---
st.markdown('<div class="main-header"><h1>VeriSmart</h1><p>Real-time AI Verification</p></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["🔎 Verify", "📊 Dashboard", "📚 Knowledge Base", "📈 History"])

with tab1:
    # Example Selector
    ex = ["Select...", "The earth is flat", "Vaccines cause autism", "5G causes COVID-19"]
    sel = st.selectbox("Example:", ex)
    if sel != "Select...": st.session_state.claim_input = sel
    
    claim = st.text_area("Claim:", key="claim_input_box", value=st.session_state.claim_input, height=100)
    
    c1, c2, c3 = st.columns(3)
    b1 = c1.button("🔍 Analyze", type="primary")
    b2 = c2.button("⚡ Quick Check")
    if c3.button("🗑️ Clear"): 
        st.session_state.claim_input = ""
        st.rerun()

    # Trigger
    if (b1 or b2 or st.session_state.trigger_analyze) and claim:
        st.session_state.trigger_analyze = False
        
        with st.spinner("Analyzing..."):
            try:
                res = requests.post(f"{BACKEND_URL}/analyze", json={"claim": claim}, timeout=60).json()
                st.session_state.history.insert(0, {"claim": claim, "res": res, "time": datetime.now()})
                
                score = res.get('score', 50)
                verdict = res.get('verdict', 'UNKNOWN')
                
                # Banner
                color = "#10b981" if score >= 80 else "#ef4444" if score < 40 else "#f59e0b"
                st.markdown(f'<div style="background:{color}20; border:2px solid {color}; padding:20px; border-radius:15px; text-align:center;">'
                            f'<h2 style="color:{color}; margin:0">{verdict}</h2><h1 style="margin:5px 0">{score}%</h1></div>', unsafe_allow_html=True)
                
                # Stats
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Confidence", f"{res.get('confidence_score')}%")
                m2.metric("Category", res.get('category'))
                m3.metric("Sentiment", res.get('sentiment'))
                m4.metric("Sources", len(res.get('sources', [])))
                
                st.markdown("---")
                
                # Analysis
                l, r = st.columns(2)
                l.subheader("📝 Analysis")
                l.write(res.get('reasoning'))
                
                r.subheader("📚 Sources")
                # Fix 'str object' error
                sources = res.get('sources', [])
                if sources:
                    for s in sources:
                        name = s.get('name', str(s)) if isinstance(s, dict) else str(s)
                        r.markdown(f"- **{name}**")
                else:
                    r.info("No sources found.")

                # Share
                st.markdown("---")
                sc1, sc2, sc3 = st.columns(3)
                
                # PDF
                pdf = generate_pdf(claim, res, sources)
                if pdf: sc1.download_button("📄 PDF", pdf, "report.pdf")
                
                # WhatsApp
                link = f"https://verismart.onrender.com/?claim={urllib.parse.quote(claim)}"
                sc2.link_button("💚 WhatsApp", f"https://wa.me/?text={link}")
                
                # Copy Link (Fix)
                sc3.code(link, language=None)

            except Exception as e: st.error(f"Error: {e}")

# Knowledge Base (Live Accumulation)
with tab3:
    st.subheader("📚 Live Knowledge Base")
    if st.session_state.fetched_news:
        for news in reversed(st.session_state.fetched_news):
            with st.expander(f"📰 {news['title']}"):
                st.write(news['description'])
                st.caption(f"Source: {news['source']['name']}")
    else:
        st.info("Fetch news to populate.")

# History (Styled)
with tab4:
    st.subheader("🕒 Recent")
    for item in st.session_state.history:
        s = item['res'].get('score', 0)
        c = "#10b981" if s >= 80 else "#ef4444"
        st.markdown(f'<div class="history-card" style="border-left-color:{c}"><b>{item["claim"]}</b><br><small>{s}% Credible</small></div>', unsafe_allow_html=True)

st.markdown("<div class='footer'>© 2026 Aryan & Khushboo • All Rights Reserved</div>", unsafe_allow_html=True)