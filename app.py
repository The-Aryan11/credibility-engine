import streamlit as st
import requests
import pandas as pd
import pydeck as pdk
from fpdf import FPDF
import os
import json
from datetime import datetime
import time

# --- CONFIGURATION ---
BACKEND_URL = os.getenv("BACKEND_URL", "https://aryan12345ark-credibility-backend.hf.space")

st.set_page_config(
    page_title="Credibility Engine",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 2rem;
        border-radius: 1rem;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }
    .metric-card {
        background-color: #f8fafc;
        border-left: 5px solid #3b82f6;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .verdict-box {
        text-align: center;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        color: white;
        font-weight: bold;
    }
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: white;
        text-align: center;
        padding: 10px;
        border-top: 1px solid #eee;
        font-size: 12px;
        color: #666;
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        height: 3em;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "history" not in st.session_state:
    st.session_state.history = []

# --- HEADER ---
st.markdown("""
<div class="main-header">
    <h1>🛡️ Real-Time Credibility Engine</h1>
    <p>Powered by Pathway (Streaming RAG) + Groq (LLM)</p>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/verified-account.png", width=50)
    st.title("Control Panel")
    
    # Health Check
    st.markdown("### 🔌 System Status")
    try:
        start_time = time.time()
        res = requests.get(f"{BACKEND_URL}/", timeout=5)
        latency = round((time.time() - start_time) * 1000)
        
        if res.status_code == 200:
            st.success(f"🟢 **Online** ({latency}ms)")
            data = res.json()
            st.caption(f"Backend: {data.get('platform', 'Unknown')}")
        else:
            st.warning("🟡 **Degraded**")
    except:
        st.error("🔴 **Offline**")
        st.caption("Check Backend URL")

    st.markdown("---")
    
    # Ingest Tool
    st.markdown("### 📰 Live Data Ingestion")
    with st.expander("Inject New Evidence"):
        ingest_text = st.text_area("Article Content:", height=150)
        ingest_source = st.text_input("Source Name:", value="Reuters")
        if st.button("🚀 Process Stream"):
            if ingest_text:
                try:
                    with st.spinner("Streaming to Pathway..."):
                        requests.post(f"{BACKEND_URL}/ingest", json={"text": ingest_text, "source": ingest_source})
                    st.toast("✅ Indexed! Pathway is updating vectors...", icon="🌊")
                except:
                    st.error("Ingestion Failed")

    st.markdown("---")
    st.info("© 2025 Aryan & Khushboo")

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["🔎 **Analysis**", "📊 **Dashboard**", "🗺️ **Global View**"])

# --- TAB 1: ANALYSIS ---
with tab1:
    col1, col2 = st.columns([3, 1])
    with col1:
        claim = st.text_area("Enter a claim to verify:", height=100, placeholder="e.g. The earth is flat because...")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_btn = st.button("✨ Analyze Now", type="primary")

    if analyze_btn and claim:
        with st.spinner("🧠 Querying Vector Store & AI Models..."):
            try:
                response = requests.post(f"{BACKEND_URL}/analyze", json={"claim": claim}, timeout=60)
                result = response.json()
                
                # Save to history
                st.session_state.history.append({
                    "claim": claim, "score": result.get('score'), "time": datetime.now().strftime("%H:%M")
                })

                # Metrics Row
                score = result.get('score', 50)
                verdict = result.get('verdict', 'UNKNOWN')
                sentiment = result.get('sentiment', 'Neutral')
                
                # Dynamic Color
                color = "#22c55e" if score >= 75 else "#ef4444" if score < 25 else "#eab308"
                
                # Score Banner
                st.markdown(f"""
                <div class="verdict-box" style="background-color: {color};">
                    <h1 style="margin:0">{score}% CREDIBLE</h1>
                    <p style="margin:0; opacity:0.9">{verdict.upper()}</p>
                </div>
                """, unsafe_allow_html=True)

                # Details Grid
                c1, c2, c3 = st.columns(3)
                c1.metric("Confidence", f"{result.get('confidence_score', 0)}%")
                c2.metric("Category", result.get('category', 'General'))
                c3.metric("Sentiment", sentiment.title())

                st.divider()

                # Analysis Content
                col_analysis, col_evidence = st.columns(2)
                
                with col_analysis:
                    st.subheader("📝 AI Reasoning")
                    st.write(result.get('reasoning'))
                    
                    st.subheader("💡 Key Points")
                    for point in result.get('key_evidence', []):
                        st.success(f"• {point}")

                with col_evidence:
                    st.subheader("📚 RAG Retrieval (Pathway)")
                    sources = result.get('sources', [])
                    if sources:
                        for idx, s in enumerate(sources):
                            with st.expander(f"📄 Source Document {idx+1}"):
                                st.write(s) # In a real app this would be the source name
                                st.caption("Retrieved from Vector Store")
                    else:
                        st.info("No direct matches in knowledge base. AI used internal knowledge.")

                # Export
                st.divider()
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.cell(200, 10, txt="Credibility Report", ln=1, align='C')
                pdf.cell(200, 10, txt=f"Claim: {claim}", ln=1)
                pdf.cell(200, 10, txt=f"Verdict: {verdict} ({score}%)", ln=1)
                pdf.multi_cell(0, 10, txt=f"Reasoning: {result.get('reasoning')}")
                
                st.download_button(
                    label="📄 Download PDF Report",
                    data=pdf.output(dest='S').encode('latin-1'),
                    file_name="report.pdf",
                    mime="application/pdf"
                )

            except Exception as e:
                st.error(f"Analysis Error: {e}")

# --- TAB 2: DASHBOARD ---
with tab2:
    st.subheader("📈 Session Activity")
    
    if st.session_state.history:
        # Metrics
        total = len(st.session_state.history)
        avg_score = sum([x['score'] for x in st.session_state.history]) / total
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Claims Checked", total)
        m2.metric("Avg Credibility", f"{int(avg_score)}%")
        m3.metric("Backend", "Hugging Face")
        
        # DataFrame
        df = pd.DataFrame(st.session_state.history)
        st.dataframe(df, use_container_width=True)
        
        # Chart
        st.bar_chart(df.set_index('time')['score'])
    else:
        st.info("No activity yet. Analyze some claims!")

# --- TAB 3: MAP ---
with tab3:
    st.subheader("🌍 Misinformation Heatmap")
    
    # Fake data for demo (replace with real if available)
    import numpy as np
    data = pd.DataFrame({
        'lat': [20.5937 + np.random.uniform(-5, 5) for _ in range(100)],
        'lon': [78.9629 + np.random.uniform(-5, 5) for _ in range(100)],
        'intensity': np.random.randint(1, 100, 100)
    })

    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(
            latitude=20.5937,
            longitude=78.9629,
            zoom=3,
            pitch=50,
        ),
        layers=[
            pdk.Layer(
                'HexagonLayer',
                data=data,
                get_position='[lon, lat]',
                radius=20000,
                elevation_scale=4,
                elevation_range=[0, 1000],
                pickable=True,
                extruded=True,
            ),
            pdk.Layer(
                'ScatterplotLayer',
                data=data,
                get_position='[lon, lat]',
                get_color='[200, 30, 0, 160]',
                get_radius=20000,
            ),
        ],
    ))
    st.caption("Visualization of claim origins and spread intensity.")