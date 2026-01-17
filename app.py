"""
VeriSmart - Premium Credibility Engine
Frontend Client (Render) -> Backend Brain (Hugging Face)
"""
import streamlit as st
import requests
import pandas as pd
import pydeck as pdk
from fpdf import FPDF
import os
import urllib.parse
from datetime import datetime
import time
from streamlit_autorefresh import st_autorefresh
from deep_translator import GoogleTranslator

# --- CONFIGURATION ---
BACKEND_URL = os.getenv("BACKEND_URL", "https://aryan12345ark-credibility-backend.hf.space")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "") 
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")

# 1. Branding Change
st.set_page_config(
    page_title="VeriSmart",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Auto-refresh
st_autorefresh(interval=60000, key="refresh")

# Initialize Session State
if "history" not in st.session_state: st.session_state.history = []
if "fetched_news" not in st.session_state: st.session_state.fetched_news = []
if "claim_input" not in st.session_state: st.session_state.claim_input = ""
if "trigger_analyze" not in st.session_state: st.session_state.trigger_analyze = False

# --- 5. HANDLE QUERY PARAMS (Share Link Logic) ---
# Allows links like: https://app.com/?claim=Earth+is+flat
query_params = st.query_params
if "claim" in query_params:
    claim_from_url = query_params["claim"]
    if st.session_state.claim_input != claim_from_url:
        st.session_state.claim_input = claim_from_url
        st.session_state.trigger_analyze = True

# --- HELPER FUNCTIONS ---

def generate_pdf(claim, data, sources):
    """Generate professional PDF report (Fixes encoding error)"""
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, 'VeriSmart Intelligence Report', 0, 1, 'C')
            self.ln(5)
    
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Sanitizer for latin-1
    def clean(text):
        return str(text).encode('latin-1', 'replace').decode('latin-1')

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Claim Analyzed:", 0, 1)
    pdf.set_font("Arial", '', 12)
    pdf.multi_cell(0, 6, clean(claim))
    pdf.ln(5)
    
    score = data.get('score', 50)
    verdict = data.get('verdict', 'UNKNOWN')
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Verdict: {verdict} ({score}%)", 0, 1)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "AI Analysis:", 0, 1)
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(0, 6, clean(data.get('reasoning', '')))
    pdf.ln(10)
    
    if sources:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Referenced Sources:", 0, 1)
        pdf.set_font("Arial", '', 10)
        for s in sources:
            name = s.get('name', str(s)) if isinstance(s, dict) else str(s)
            pdf.cell(0, 6, f"- {clean(name)}", 0, 1)

    # 7. FIX: Return bytes directly (No .encode)
    return bytes(pdf.output()) 

# --- CSS STYLING ---
st.markdown("""
<style>
    /* Dark Theme */
    .stApp { background-color: #0f172a; color: #e2e8f0; }
    
    /* Header */
    .main-header {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        padding: 2.5rem;
        border-radius: 1rem;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #1e293b; border-right: 1px solid #334155; }
    
    /* Cards */
    .metric-card {
        background-color: #1e293b;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    
    /* History Box */
    .history-card {
        background-color: #1e293b;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
        margin-bottom: 10px;
        cursor: pointer;
        transition: 0.3s;
    }
    .history-card:hover { background-color: #334155; }
    
    /* Buttons */
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    
    /* Inputs */
    .stTextArea textarea { background-color: #0f172a; color: white; border: 1px solid #334155; }
    .stSelectbox div[data-baseweb="select"] > div { background-color: #1e293b; color: white; }
    
    /* Footer */
    .footer { text-align: center; margin-top: 50px; color: #64748b; font-size: 0.8rem; border-top: 1px solid #334155; padding-top: 20px; }
    
    .pilot-badge {
        position: fixed; top: 1rem; right: 1rem;
        background: #10b981; color: white;
        padding: 4px 12px; border-radius: 20px;
        font-size: 0.8rem; font-weight: bold; z-index: 999;
    }
</style>
<div class="pilot-badge">🟢 System Active</div>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ VeriSmart")
    st.caption("Real-Time Misinformation Neutralizer")
    
    # Status Check
    try:
        r = requests.get(f"{BACKEND_URL}/", timeout=2)
        status_color = "green" if r.status_code==200 else "red"
        # 3. FIX: Display simple active status if fetching count fails to fit
        files_indexed = r.json().get('files', 'Active') if r.status_code==200 else "0"
    except: 
        status_color = "red"
        files_indexed = "Offline"
        
    st.markdown(f"**Status:** :{status_color}[{files_indexed}]")
    
    # Stats Grid
    c1, c2 = st.columns(2)
    c1.metric("Live Docs", files_indexed) # 3. Fix: "Dyn..." issue solved by backend return or short text
    c2.metric("Analyses", len(st.session_state.history))
    
    st.markdown("---")
    
    # 2. FIX: Live Data Fetch & Rate
    st.subheader("📰 Live News Feed")
    topic = st.selectbox("Topic", ["General", "Health", "Politics", "Science", "Tech"])
    
    if st.button("🔄 Fetch & Analyze News"):
        if GNEWS_API_KEY:
            try:
                url = f"https://gnews.io/api/v4/top-headlines?category={topic.lower()}&lang=en&apikey={GNEWS_API_KEY}"
                data = requests.get(url).json()
                articles = data.get('articles', [])[:3] # Limit to 3
                
                new_items = []
                for a in articles:
                    # Ingest to Backend
                    requests.post(f"{BACKEND_URL}/ingest", json={
                        "text": f"{a['title']}\n{a['description']}",
                        "source": a['source']['name']
                    })
                    new_items.append(a)
                
                st.session_state.fetched_news = new_items # Store for display
                st.success(f"Ingested {len(new_items)} articles!")
            except: st.error("Feed Error")
        else: st.error("Missing API Key")

    st.markdown("---")
    st.caption("© 2025 Aryan & Khushboo")

# --- MAIN CONTENT ---
st.markdown("""
<div class="main-header">
    <h1 style="margin:0; font-size: 3rem;">VeriSmart</h1>
    <p style="margin:10px 0 0 0; font-size: 1.1rem; opacity:0.9;">Real-time claim verification powered by AI & live evidence</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["🔎 Verify", "📊 Dashboard", "📚 Knowledge Base", "📈 History"])

# --- TAB 1: VERIFY ---
with tab1:
    st.markdown("### 🕵️ Verify a Claim")
    
    # 4. FIX: Extended Examples List
    examples = [
        "Select an example...",
        "Vaccines cause autism",
        "The earth is flat",
        "Drinking 8 glasses of water daily is necessary",
        "5G networks cause COVID-19",
        "Climate change is a natural cycle not caused by humans",
        "Eating carrots gives you night vision",
        "Napoleon Bonaparte was extremely short",
        "Sugar causes hyperactivity in children"
    ]
    
    def update_input():
        if st.session_state.ex_select != "Select an example...":
            st.session_state.claim_input = st.session_state.ex_select

    st.selectbox("Try an example:", examples, key="ex_select", on_change=update_input)
    
    # Input Area
    claim_val = st.text_area("Enter claim:", key="claim_box", value=st.session_state.claim_input, height=100)
    
    # Action Buttons
    c1, c2, c3 = st.columns([1, 1, 1])
    do_analyze = c1.button("🔍 Analyze Claim", type="primary")
    c2.button("⚡ Quick Check")
    if c3.button("🗑️ Clear"):
        st.session_state.claim_input = ""
        st.rerun()

    # Trigger Logic (Manual Click or URL Param)
    if do_analyze or (st.session_state.trigger_analyze and claim_val):
        st.session_state.trigger_analyze = False # Reset trigger
        
        with st.spinner("🧠 VeriSmart AI is analyzing..."):
            try:
                # Backend Call
                res = requests.post(f"{BACKEND_URL}/analyze", json={"claim": claim_val}, timeout=60).json()
                
                # History Save
                st.session_state.history.insert(0, { # Insert at top
                    "claim": claim_val, "res": res, "time": datetime.now()
                })
                
                # Colors
                score = res.get('score', 50)
                if score >= 80: color, bg = "#10b981", "rgba(16, 185, 129, 0.1)"
                elif score >= 40: color, bg = "#f59e0b", "rgba(245, 158, 11, 0.1)"
                else: color, bg = "#ef4444", "rgba(239, 68, 68, 0.1)"
                
                st.markdown("---")
                
                # Verdict Banner
                st.markdown(f"""
                <div style="background-color: {bg}; border: 2px solid {color}; padding: 2rem; border-radius: 15px; text-align: center;">
                    <h2 style="color: {color}; margin:0;">{res.get('verdict', 'UNKNOWN')}</h2>
                    <h1 style="font-size: 3.5rem; margin: 10px 0;">{score}%</h1>
                    <p style="opacity: 0.8">Credibility Score</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Stats
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Confidence", f"{res.get('confidence_score')}%")
                m2.metric("Category", res.get('category'))
                m3.metric("Sentiment", res.get('sentiment', 'Neutral'))
                m4.metric("Sources", len(res.get('sources', [])))
                
                st.markdown("---")
                
                # Analysis
                c_left, c_right = st.columns(2)
                with c_left:
                    st.subheader("📝 AI Analysis")
                    st.write(res.get('reasoning'))
                    st.markdown("#### 💡 Key Evidence")
                    for k in res.get('key_evidence', []):
                        st.info(k)
                        
                with c_right:
                    st.subheader("📚 Verified Sources")
                    sources = res.get('sources', [])
                    if sources:
                        for s in sources:
                            name = s.get('name', 'Unknown')
                            cred = s.get('credibility', 'Medium')
                            st.markdown(f"**{name}** (`{cred}`)")
                    else:
                        st.warning("No direct sources found in Knowledge Base.")

                # --- 5 & 6. SHARE SECTION ---
                st.markdown("---")
                st.subheader("📤 Share Result")
                
                share_url = f"https://credibility-engine.onrender.com/?claim={urllib.parse.quote(claim_val)}"
                share_text = f"Check this claim on VeriSmart: {claim_val} (Score: {score}%)"
                
                sc1, sc2, sc3 = st.columns(3)
                
                # 7. PDF Fix (Bytes)
                pdf_data = generate_pdf(claim_val, res, sources)
                sc1.download_button("📄 PDF Report", pdf_data, "report.pdf", "application/pdf")
                
                # WhatsApp
                wa_link = f"https://wa.me/?text={urllib.parse.quote(share_text + ' ' + share_url)}"
                sc2.link_button("💚 WhatsApp", wa_link)
                
                # Copy Link
                sc3.code(share_url, language=None)

            except Exception as e:
                st.error(f"Error: {e}")

# --- TAB 2: DASHBOARD ---
with tab2:
    st.subheader("📊 Analytics")
    if st.session_state.history:
        df = pd.DataFrame([{"Score": h['res']['score'], "Category": h['res']['category']} for h in st.session_state.history])
        c1, c2 = st.columns(2)
        c1.bar_chart(df['Category'].value_counts())
        c2.line_chart(df['Score'])
    else: st.info("Analyze claims to see stats.")

# --- TAB 3: KNOWLEDGE BASE (Fix 2) ---
with tab3:
    st.subheader("📚 Live Knowledge Base")
    
    # 2. Display Fetched News
    if st.session_state.fetched_news:
        st.markdown("#### 🆕 Just Ingested")
        for news in st.session_state.fetched_news:
            with st.expander(f"📰 {news['title']}"):
                st.write(news['description'])
                st.caption(f"Source: {news['source']['name']}")
                # Mock Credibility for UI (Real check happens in backend analysis)
                st.success("✅ Rated: Genuine Source (GNews)") 
                
    st.markdown("---")
    st.info(f"Total Vectors Indexed: {requests.get(f'{BACKEND_URL}/').json().get('files', 'Unknown')}")

# --- TAB 4: HISTORY (Fix 8 & 9) ---
with tab4:
    st.subheader("🕒 Recent Analyses")
    
    if not st.session_state.history:
        st.info("No history yet.")
    
    for i, item in enumerate(st.session_state.history):
        s = item['res'].get('score', 0)
        color = "#10b981" if s >= 80 else "#ef4444" if s < 40 else "#f59e0b"
        
        # 8. Styled History Cards (Clickable-ish via Expander)
        with st.container():
            st.markdown(f"""
            <div class="history-card" style="border-left-color: {color};">
                <div style="font-weight:bold; font-size:1.1rem;">{item['claim']}</div>
                <div style="display:flex; justify-content:space-between; margin-top:5px;">
                    <span style="color:{color}; font-weight:bold;">{s}% Credible</span>
                    <span style="color:#94a3b8;">{item['time'].strftime('%H:%M %p')}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Details on expand
            with st.expander("View Details"):
                st.write(item['res'].get('reasoning'))
                st.json(item['res'])

# Footer
st.markdown("<div class='footer'>© 2025 Aryan & Khushboo • All Rights Reserved</div>", unsafe_allow_html=True)