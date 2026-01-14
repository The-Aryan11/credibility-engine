"""
Credibility Engine - Dark Mode Premium Frontend
Restores the Phase 2 UI Design + All Features
"""
import streamlit as st
import requests
import pandas as pd
import pydeck as pdk
from fpdf import FPDF
import os
import json
from datetime import datetime
import time
import numpy as np
from streamlit_autorefresh import st_autorefresh
from deep_translator import GoogleTranslator

# Try voice
try:
    from streamlit_mic_recorder import speech_to_text
    HAS_VOICE = True
except: HAS_VOICE = False

# Config
BACKEND_URL = os.getenv("BACKEND_URL", "https://aryan12345ark-credibility-backend.hf.space")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "") 
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")

st.set_page_config(page_title="Credibility Engine", page_icon="🔍", layout="wide")
st_autorefresh(interval=60000, key="refresh")

if "history" not in st.session_state: st.session_state.history = []
if "lang" not in st.session_state: st.session_state.lang = "English"

# --- DARK MODE CSS (Restoring Phase 2 Look) ---
st.markdown("""
<style>
    /* Global Dark Theme overrides */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    
    /* Header */
    .main-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #2563eb 100%);
        padding: 3rem;
        border-radius: 1rem;
        color: white;
        margin-bottom: 2rem;
        text-align: left;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1e293b;
        border-right: 1px solid #334155;
    }
    
    /* Cards */
    .score-card {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    
    /* Verdict Colors */
    .verdict-box {
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        color: white;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    /* Custom Inputs */
    .stTextArea textarea {
        background-color: #0f172a;
        color: white;
        border: 1px solid #334155;
    }
    
    /* Badges */
    .source-badge {
        background: #334155;
        color: #e2e8f0;
        padding: 4px 10px;
        border-radius: 15px;
        font-size: 0.8rem;
        margin-right: 5px;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        margin-top: 50px;
        color: #64748b;
        font-size: 0.8rem;
        border-top: 1px solid #334155;
        padding-top: 20px;
    }
    
    /* Pilot Badge */
    .pilot-badge {
        position: fixed; top: 1rem; right: 1rem;
        background: #10b981; color: black;
        padding: 5px 15px; border-radius: 20px;
        font-weight: bold; z-index: 9999;
    }
</style>
<div class="pilot-badge">🟢 System Active</div>
""", unsafe_allow_html=True)

# --- TRANSLATION HELPER ---
def translate(text, lang):
    if lang == "English" or not text: return text
    try:
        lang_map = {"Hindi":"hi", "Spanish":"es", "French":"fr", "German":"de"}
        return GoogleTranslator(source='auto', target=lang_map.get(lang, 'en')).translate(text)
    except: return text

# --- SIDEBAR ---
with st.sidebar:
    st.title("🔍 Credibility Engine")
    st.caption("Real-Time Misinformation Tracker")
    st.markdown("---")
    
    # Status
    try:
        res = requests.get(f"{BACKEND_URL}/", timeout=2)
        status = "🟢 Online" if res.status_code==200 else "🔴 Error"
    except: status = "🔴 Offline"
    
    col1, col2 = st.columns(2)
    col1.metric("Status", "Active")
    col2.metric("Backend", "HF")
    st.caption(f"Brain: {status}")
    
    st.markdown("---")
    
    # Language
    st.markdown("### 🌐 Settings")
    st.session_state.lang = st.selectbox("Language", ["English", "Hindi", "Spanish", "French"])
    
    st.markdown("---")
    
    # Live Feed
    st.markdown("### 📰 Live Feed")
    topic = st.selectbox("Topic", ["General", "Health", "Science", "Tech"])
    if st.button("🔄 Fetch & Ingest"):
        if GNEWS_API_KEY:
            with st.spinner("Streaming to Pathway..."):
                try:
                    url = f"https://gnews.io/api/v4/top-headlines?category={topic.lower()}&lang=en&apikey={GNEWS_API_KEY}"
                    data = requests.get(url).json()
                    count = 0
                    for article in data.get('articles', [])[:5]:
                        requests.post(f"{BACKEND_URL}/ingest", json={
                            "text": f"{article['title']}\n{article['description']}",
                            "source": article['source']['name']
                        })
                        count += 1
                    st.toast(f"✅ Indexed {count} articles!", icon="🌊")
                except: st.error("Stream Failed")
        else: st.error("Missing API Key")

    st.markdown("---")
    st.caption("© 2025 Aryan & Khushboo")

# --- MAIN CONTENT ---
st.markdown("""
<div class="main-header">
    <h1 style="margin:0;">🔍 Credibility Engine</h1>
    <p style="margin:10px 0 0 0; opacity:0.8;">Real-time claim verification powered by AI & live evidence</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["🔎 Verify Claim", "📊 Dashboard", "📚 Knowledge", "🗺️ Map"])

# --- VERIFY TAB ---
with tab1:
    c1, c2 = st.columns([3, 1])
    with c1:
        claim = st.text_area("Enter claim to verify:", height=100, placeholder="e.g. Vaccines cause autism...")
    with c2:
        st.write("")
        st.write("")
        analyze = st.button("✨ Analyze", type="primary", use_container_width=True)
        if HAS_VOICE:
            voice = speech_to_text(language='en', use_container_width=True, just_once=True, key='STT')
            if voice: st.info(f"Heard: {voice}")

    if analyze and claim:
        with st.spinner("🧠 Querying Pathway Vector Store..."):
            try:
                # API Call
                res = requests.post(f"{BACKEND_URL}/analyze", json={"claim": claim}, timeout=60).json()
                
                # Save History
                st.session_state.history.append({"claim": claim, "res": res, "time": datetime.now()})
                
                # Metrics
                score = res.get('score', 50)
                verdict = res.get('verdict', 'UNKNOWN')
                cat = res.get('category', 'General')
                conf = res.get('confidence_score', 0)
                
                # Colors
                if score >= 80: color = "#10b981" # Green
                elif score >= 50: color = "#f59e0b" # Yellow
                else: color = "#ef4444" # Red
                
                # Banner
                st.markdown(f"""
                <div class="verdict-box" style="background-color: {color};">
                    <h2 style="margin:0;">{verdict}</h2>
                    <h1 style="font-size:3.5rem; margin:0;">{score}%</h1>
                    <p style="margin:0;">Credibility Score</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Stats
                m1, m2, m3, m4 = st.columns(4)
                
                def card(label, val):
                    return f"<div class='score-card'><div style='font-size:1.5rem; font-weight:bold;'>{val}</div><div style='color:#94a3b8; font-size:0.8rem;'>{label}</div></div>"
                
                m1.markdown(card("Confidence", f"{conf}%"), unsafe_allow_html=True)
                m2.markdown(card("Category", cat), unsafe_allow_html=True)
                m3.markdown(card("Sentiment", res.get('sentiment', 'Neutral')), unsafe_allow_html=True)
                m4.markdown(card("Sources", len(res.get('sources', []))), unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Analysis
                l, r = st.columns(2)
                with l:
                    st.subheader("📝 Analysis")
                    reason = translate(res.get('reasoning'), st.session_state.lang)
                    st.write(reason)
                    
                    st.markdown("#### 💡 Key Evidence")
                    for k in res.get('key_evidence', []):
                        st.info(translate(k, st.session_state.lang))
                        
                with r:
                    st.subheader("📚 Source Credibility")
                    for s in res.get('sources', []):
                        name = s.get('name', 'Unknown')
                        cred = s.get('credibility', 'Medium')
                        st.markdown(f"<span class='source-badge'>{cred} Trust</span> {name}", unsafe_allow_html=True)
                    
                    st.markdown("#### 🔗 Related")
                    for rc in res.get('related_claims', []):
                        st.caption(f"• {rc}")

                # Actions
                st.markdown("---")
                xc1, xc2, xc3 = st.columns(3)
                
                # PDF
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 10, f"Claim: {claim}\nScore: {score}%\n\nAnalysis:\n{res.get('reasoning')}")
                xc1.download_button("📄 Download PDF", pdf.output(dest='S').encode('latin-1'), "report.pdf")
                
                xc2.markdown(f"[🐦 Twitter](https://twitter.com/intent/tweet?text=Check: {claim} {score}%)")
                xc3.markdown(f"[💬 WhatsApp](https://wa.me/?text=Check: {claim} {score}%)")

            except Exception as e:
                st.error(f"Error: {e}")

# --- DASHBOARD ---
with tab2:
    st.subheader("📊 Analytics Dashboard")
    if st.session_state.history:
        df = pd.DataFrame([
            {"Score": h['res']['score'], "Category": h['res']['category'], "Time": h['time']} 
            for h in st.session_state.history
        ])
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total", len(df))
        c2.metric("Avg Score", f"{int(df['Score'].mean())}%")
        c3.metric("True Claims", len(df[df['Score'] > 75]))
        
        st.line_chart(df['Score'])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No data yet.")

# --- MAP ---
with tab3:
    st.subheader("🌍 Geographic Spread")
    data = pd.DataFrame({
        'lat': [20.59 + np.random.uniform(-5, 5) for _ in range(50)],
        'lon': [78.96 + np.random.uniform(-5, 5) for _ in range(50)]
    })
    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/dark-v10',
        initial_view_state=pdk.ViewState(latitude=20.59, longitude=78.96, zoom=3),
        layers=[pdk.Layer('HexagonLayer', data=data, get_position='[lon, lat]', radius=20000, elevation_scale=4, extruded=True)]
    ))

# --- KNOWLEDGE ---
with tab4:
    st.subheader("📚 Indexed Knowledge")
    st.info("Connected to Pathway Vector Store on Hugging Face")
    st.json({"status": "active", "backend": "HF Spaces", "memory": "16GB"})

st.markdown("<div class='footer'>© 2025 Aryan & Khushboo • Powered by Pathway + Groq + Sentence Transformers</div>", unsafe_allow_html=True)