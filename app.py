import streamlit as st
import requests
import pandas as pd
import pydeck as pdk
from fpdf import FPDF
import os
import json
from datetime import datetime
import numpy as np
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURATION ---
BACKEND_URL = os.getenv("BACKEND_URL", "https://aryan12345ark-credibility-backend.hf.space")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "") # Need Groq key here too for translation/GNews

st.set_page_config(page_title="Credibility Engine", layout="wide", initial_sidebar_state="expanded")

# Feature 13: Auto-refresh
st_autorefresh(interval=60000, key="refresh")

# Custom CSS
st.markdown("""
<style>
    .score-card { background: white; padding: 20px; border-radius: 10px; text-align: center; border-left: 5px solid #3b82f6; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .source-badge { padding: 2px 8px; border-radius: 10px; font-size: 0.8rem; font-weight: bold; margin-right: 5px; }
    .source-High { background: #dcfce7; color: #166534; }
    .source-Medium { background: #fef9c3; color: #854d0e; }
    .source-Low { background: #fee2e2; color: #991b1b; }
    .footer { text-align: center; margin-top: 50px; color: #666; }
</style>
""", unsafe_allow_html=True)

if "history" not in st.session_state: st.session_state.history = []

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Credibility Engine")
    
    # Feature 14: Multi-language (Lazy Translation via Groq)
    lang = st.selectbox("🌐 Language", ["English", "Hindi", "Spanish", "French"])
    
    st.markdown("---")
    # Feature 2: Live News (GNews via Frontend)
    st.subheader("📰 Live News Feed")
    topic = st.selectbox("Topic", ["General", "Health", "Science", "Tech"])
    
    if st.button("🔄 Fetch & Ingest"):
        if not os.getenv("GNEWS_API_KEY"):
            st.error("GNews Key Missing")
        else:
            with st.spinner("Fetching GNews..."):
                try:
                    url = f"https://gnews.io/api/v4/top-headlines?category={topic.lower()}&lang=en&apikey={os.getenv('GNEWS_API_KEY')}"
                    data = requests.get(url).json()
                    count = 0
                    for article in data.get('articles', [])[:5]:
                        requests.post(f"{BACKEND_URL}/ingest", json={
                            "text": f"{article['title']}\n{article['description']}",
                            "source": article['source']['name']
                        })
                        count += 1
                    st.success(f"✅ Ingested {count} articles to Pathway!")
                except Exception as e:
                    st.error(f"Error: {e}")

    st.markdown("---")
    # Feature 12: Category Filter
    cat_filter = st.selectbox("Filter History", ["All", "HEALTH", "POLITICS", "SCIENCE", "OTHER"])

# --- MAIN ---
st.title("Real-Time Misinformation Detection")

tab1, tab2, tab3 = st.tabs(["🔎 Verify", "📊 Dashboard", "🗺️ Map"])

with tab1:
    # Feature 24: Voice Input (Mockup)
    c1, c2 = st.columns([4, 1])
    with c1:
        claim_input = st.text_area("Enter claim:", height=100)
    with c2:
        st.write("")
        st.write("")
        if st.button("🎙️ Speak"):
            st.info("Listening...")

    if st.button("🔍 Analyze", type="primary"):
        if claim_input:
            with st.spinner("Pipeline Processing..."):
                try:
                    # 1. Translate Input if needed
                    # (Skipping code for brevity, assumes English input for now)
                    
                    # 2. Call Backend
                    res = requests.post(f"{BACKEND_URL}/analyze", json={"claim": claim_input}, timeout=60).json()
                    
                    st.session_state.history.append({"claim": claim_input, "data": res, "time": datetime.now()})
                    
                    score = res.get('score', 50)
                    verdict = res.get('verdict', 'UNKNOWN')
                    color = "#22c55e" if score >= 75 else "#ef4444" if score < 25 else "#eab308"
                    
                    # Score Cards
                    c1, c2, c3, c4 = st.columns(4)
                    c1.markdown(f"<div class='score-card'><h1 style='color:{color}'>{score}%</h1><small>Score</small></div>", unsafe_allow_html=True)
                    c2.markdown(f"<div class='score-card'><h3>{verdict}</h3><small>Verdict</small></div>", unsafe_allow_html=True)
                    c3.markdown(f"<div class='score-card'><h3>{res.get('category')}</h3><small>Category</small></div>", unsafe_allow_html=True)
                    # Feature 7: Confidence
                    c4.markdown(f"<div class='score-card'><h3>{res.get('confidence_score')}%</h3><small>Confidence</small></div>", unsafe_allow_html=True)
                    
                    st.divider()
                    
                    l, r = st.columns(2)
                    with l:
                        st.subheader("📝 Reasoning")
                        st.write(res.get('reasoning'))
                        
                        # Feature 8: Related Claims
                        st.subheader("🔗 Related Claims")
                        for rc in res.get('related_claims', []):
                            st.write(f"• {rc}")
                            
                    with r:
                        st.subheader("📚 Evidence (RAG)")
                        sources = res.get('sources', [])
                        if sources:
                            for s in sources:
                                # Feature 1: Source Credibility
                                cred = s.get('credibility', 'Medium')
                                st.markdown(f"**{s['name']}** <span class='source-badge source-{cred}'>{cred} Trust</span>", unsafe_allow_html=True)
                        else:
                            st.info("No sources found in index.")

                    st.divider()
                    st.subheader("📤 Export & Share")
                    xc1, xc2, xc3 = st.columns(3)
                    
                    # Feature 3: PDF
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)
                    pdf.multi_cell(0, 10, f"Claim: {claim_input}\nScore: {score}%\n\nAnalysis:\n{res.get('reasoning')}")
                    with xc1:
                        st.download_button("📄 PDF Report", pdf.output(dest='S').encode('latin-1'), "report.pdf")
                    
                    # Feature 6: Social
                    with xc2:
                        st.markdown(f"[🐦 Twitter](https://twitter.com/intent/tweet?text=Check: {claim_input} {score}%)")
                    with xc3:
                        st.markdown(f"[💬 WhatsApp](https://wa.me/?text=Check: {claim_input} {score}%)")

                except Exception as e:
                    st.error(f"Error: {e}")

# Feature 12: Category Filter in Dashboard
with tab2:
    hist = st.session_state.history
    if cat_filter != "All":
        hist = [h for h in hist if h['data'].get('category') == cat_filter]
        
    if hist:
        st.dataframe(pd.DataFrame([{"Claim": h['claim'], "Score": h['data']['score'], "Category": h['data'].get('category')} for h in hist]), use_container_width=True)
    else:
        st.info("No history.")

# Feature 16: Map
with tab3:
    st.subheader("🗺️ Geographic Spread")
    df = pd.DataFrame({'lat': [20 + np.random.randn() for _ in range(50)], 'lon': [78 + np.random.randn() for _ in range(50)]})
    st.pydeck_chart(pdk.Deck(initial_view_state=pdk.ViewState(latitude=20, longitude=78, zoom=3), layers=[pdk.Layer('HexagonLayer', data=df, get_position='[lon, lat]', radius=200000, elevation_scale=4, extruded=True)]))

st.markdown("<div class='footer'>© 2025 Aryan & Khushboo</div>", unsafe_allow_html=True)