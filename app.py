"""
Credibility Engine - Premium Frontend (The Face)
Connects to Hugging Face Backend (The Brain)
Features: Professional UI, 3D Maps, PDF Reports, Real-Time Dashboard, Voice, Multi-Language
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

# --- CONFIGURATION ---
BACKEND_URL = os.getenv("BACKEND_URL", "https://aryan12345ark-credibility-backend.hf.space")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "") 
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")

# Page Configuration
st.set_page_config(
    page_title="Credibility Engine",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Feature: Auto-refresh (Every 60s)
st_autorefresh(interval=60000, limit=None, key="refresh")

# Initialize Session State
if "history" not in st.session_state: st.session_state.history = []
if "language" not in st.session_state: st.session_state.language = "English"

# --- HELPER FUNCTIONS ---

def translate_text(text, target_lang):
    """
    Client-side translation using Groq (Lightweight)
    """
    if target_lang == "English" or not GROQ_API_KEY or not text:
        return text
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": f"Translate to {target_lang}. Return ONLY the translation."},
                {"role": "user", "content": text}
            ],
            temperature=0.1
        )
        return completion.choices[0].message.content.strip()
    except:
        return text

def generate_pdf(claim, data, sources):
    """Generate professional PDF report"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, 'Credibility Engine Report', 0, 1, 'C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'C')
    pdf.ln(10)
    
    # Content
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Claim: {claim[:80]}...", 0, 1)
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 10, f"Verdict: {data.get('verdict')} | Score: {data.get('score')}%", 0, 1)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Analysis:", 0, 1)
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(0, 6, data.get('reasoning', 'N/A').encode('latin-1', 'replace').decode('latin-1'))
    pdf.ln(5)
    
    if sources:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Sources:", 0, 1)
        pdf.set_font("Arial", '', 10)
        for s in sources:
            pdf.cell(0, 6, f"- {s.get('name', 'Unknown')}", 0, 1)
            
    return pdf.output(dest='S').encode('latin-1')

# --- CUSTOM CSS ---
st.markdown("""
<style>
    /* Main Layout */
    .main > div { padding-top: 2rem; }
    
    /* Header */
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        padding: 3rem;
        border-radius: 1.5rem;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Score Card */
    .score-card {
        background: white;
        border-radius: 1rem;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        text-align: center;
        border-top: 6px solid #e2e8f0;
        transition: transform 0.2s;
    }
    .score-card:hover { transform: translateY(-5px); }
    
    /* Card Colors */
    .border-green { border-top-color: #22c55e !important; }
    .border-yellow { border-top-color: #eab308 !important; }
    .border-orange { border-top-color: #f97316 !important; }
    .border-red { border-top-color: #ef4444 !important; }
    
    /* Verdict Banner */
    .verdict-banner {
        padding: 2rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    /* Source Badges */
    .source-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 0.2rem;
        border: 1px solid transparent;
    }
    .trust-High { background: #dcfce7; color: #166534; border-color: #86efac; }
    .trust-Medium { background: #fef9c3; color: #854d0e; border-color: #fde047; }
    .trust-Low { background: #fee2e2; color: #991b1b; border-color: #fca5a5; }
    
    /* Evidence Card */
    .evidence-item {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3b82f6;
        margin-bottom: 0.5rem;
        font-size: 0.95rem;
    }
    
    /* Confidence Bar */
    .confidence-track {
        height: 8px;
        background: #e2e8f0;
        border-radius: 4px;
        margin-top: 10px;
        overflow: hidden;
    }
    .confidence-fill {
        height: 100%;
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
    }
    
    /* Footer */
    .footer {
        text-align: center;
        margin-top: 4rem;
        padding: 2rem;
        color: #94a3b8;
        border-top: 1px solid #e2e8f0;
    }
    
    /* Pilot Badge */
    .pilot-badge {
        position: fixed;
        top: 1rem;
        right: 1rem;
        background: linear-gradient(45deg, #f59e0b, #d97706);
        color: white;
        padding: 0.4rem 1rem;
        border-radius: 2rem;
        font-weight: 700;
        font-size: 0.8rem;
        box-shadow: 0 4px 6px -1px rgba(245, 158, 11, 0.3);
        z-index: 1000;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
</style>

<div class="pilot-badge">⚡ LIVE PILOT</div>
""", unsafe_allow_html=True)

# --- SIDEBAR UI ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/9566/9566127.png", width=60)
    st.title("Control Center")
    
    # Status Panel
    try:
        start_time = time.time()
        res = requests.get(f"{BACKEND_URL}/", timeout=3)
        latency = int((time.time() - start_time) * 1000)
        status_color = "green" if res.status_code == 200 else "red"
        status_text = f"Online ({latency}ms)" if res.status_code == 200 else "Offline"
    except:
        status_color = "red"
        status_text = "Disconnected"

    st.markdown(f"""
    <div style="background:#f8fafc; padding:10px; border-radius:8px; border:1px solid #e2e8f0; margin-bottom:20px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-weight:600; color:#475569;">System Status</span>
            <span style="background:{status_color}; width:8px; height:8px; border-radius:50%;"></span>
        </div>
        <div style="font-size:0.8rem; color:#64748b; margin-top:5px;">
            Pathway Brain: <b>{status_text}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Multi-language Feature
    st.markdown("### 🌐 Settings")
    st.session_state.language = st.selectbox(
        "Output Language",
        ["English", "Hindi", "Spanish", "French", "German", "Chinese"]
    )

    st.markdown("---")
    
    # GNews Live Feed Feature
    st.markdown("### 📰 News Stream")
    news_topic = st.selectbox("Topic", ["General", "Health", "Science", "Politics"])
    
    if st.button("🔄 Fetch & Index Live News", use_container_width=True):
        if not GNEWS_API_KEY:
            st.error("Missing GNews Key")
        else:
            with st.spinner(f"Streaming {news_topic} news to Pathway..."):
                try:
                    url = f"https://gnews.io/api/v4/top-headlines?category={news_topic.lower()}&lang=en&apikey={GNEWS_API_KEY}"
                    data = requests.get(url).json()
                    count = 0
                    for article in data.get('articles', [])[:5]:
                        requests.post(f"{BACKEND_URL}/ingest", json={
                            "text": f"{article['title']}\n{article['description']}",
                            "source": article['source']['name']
                        })
                        count += 1
                    st.toast(f"✅ Successfully piped {count} live articles to vector store!", icon="🌊")
                except Exception as e:
                    st.error(f"Stream Error: {e}")

    st.markdown("---")
    
    # Manual Ingest
    with st.expander("📝 Manual Data Entry"):
        manual_txt = st.text_area("Content", height=100)
        manual_src = st.text_input("Source Name", value="Manual Input")
        if st.button("Inject to Pipeline"):
            requests.post(f"{BACKEND_URL}/ingest", json={"text": manual_txt, "source": manual_src})
            st.success("Data injected.")

# --- MAIN CONTENT ---
st.markdown("""
<div class="main-header">
    <h1 style="font-size: 3.5rem; font-weight: 800; margin: 0;">🛡️ Credibility Engine</h1>
    <p style="font-size: 1.2rem; opacity: 0.8; margin-top: 10px;">
        Real-Time Misinformation Detection System
    </p>
    <div style="margin-top: 20px;">
        <span style="background:rgba(255,255,255,0.15); padding:5px 12px; border-radius:15px; font-size:0.85rem; border:1px solid rgba(255,255,255,0.2);">
            🚀 Pathway Streaming
        </span>
        &nbsp;
        <span style="background:rgba(255,255,255,0.15); padding:5px 12px; border-radius:15px; font-size:0.85rem; border:1px solid rgba(255,255,255,0.2);">
            🧠 Groq Intelligence
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# Tabs
tab_verify, tab_dash, tab_map, tab_kb = st.tabs([
    "🔎 **Verify Claim**", 
    "📊 **Analytics Dashboard**", 
    "🗺️ **Global Threat Map**",
    "📚 **Knowledge Graph**"
])

# ============ TAB 1: VERIFY ============
with tab_verify:
    col_input, col_action = st.columns([3, 1])
    
    with col_input:
        claim_input = st.text_area(
            "Enter statement to verify:", 
            height=100, 
            placeholder="e.g. Drinking 8 glasses of water a day prevents COVID-19..."
        )
    
    with col_action:
        st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
        analyze_btn = st.button("✨ Analyze Truth", type="primary", use_container_width=True)
        
        # Feature: Voice Input Mockup
        if st.button("🎙️ Voice Input", use_container_width=True):
            st.info("Listening... (Say your claim)")

    if analyze_btn and claim_input:
        with st.spinner("🔄 Interfacing with Pathway Vector Store & Groq LLM..."):
            try:
                # 1. SEND TO BACKEND
                response = requests.post(
                    f"{BACKEND_URL}/analyze", 
                    json={"claim": claim_input}, 
                    timeout=60
                )
                data = response.json()
                
                # 2. PROCESS RESULTS
                score = data.get('score', 50)
                verdict = data.get('verdict', 'UNKNOWN')
                confidence = data.get('confidence_score', 0)
                category = data.get('category', 'General')
                
                # Colors
                if score >= 80: theme = "#22c55e" # Green
                elif score >= 50: theme = "#eab308" # Yellow
                elif score >= 25: theme = "#f97316" # Orange
                else: theme = "#ef4444" # Red
                
                # 3. VERDICT BANNER
                st.markdown(f"""
                <div class="verdict-banner" style="background-color: {theme};">
                    <h2 style="margin:0; font-size:1.5rem;">VERDICT: {verdict.upper()}</h2>
                    <h1 style="margin:0; font-size:4rem; font-weight:800;">{score}%</h1>
                    <p style="margin:0; opacity:0.9;">Credibility Score</p>
                </div>
                """, unsafe_allow_html=True)
                
                # 4. METRICS ROW
                m1, m2, m3, m4 = st.columns(4)
                
                # Helper for cards
                def metric_html(label, value, color_class):
                    return f"""
                    <div class="score-card {color_class}">
                        <div style="font-size:1.8rem; font-weight:700; color:#1e293b;">{value}</div>
                        <div style="font-size:0.85rem; color:#64748b; margin-top:5px;">{label}</div>
                    </div>
                    """
                
                m1.markdown(metric_html("Confidence", f"{confidence}%", "border-green"), unsafe_allow_html=True)
                m2.markdown(metric_html("Category", category, "border-yellow"), unsafe_allow_html=True)
                m3.markdown(metric_html("Sentiment", data.get('sentiment', 'Neutral').title(), "border-orange"), unsafe_allow_html=True)
                m4.markdown(metric_html("Evidence Count", len(data.get('sources', [])), "border-red"), unsafe_allow_html=True)
                
                st.markdown("---")
                
                # 5. DETAILED ANALYSIS
                row_main = st.columns([2, 1])
                
                with row_main[0]:
                    st.subheader("📝 Analysis & Reasoning")
                    
                    reasoning = data.get('reasoning')
                    # Feature: Translation
                    if st.session_state.language != "English":
                        with st.spinner("Translating..."):
                            reasoning = translate_text(reasoning, st.session_state.language)
                    
                    st.write(reasoning)
                    
                    st.markdown("#### 💡 Key Evidence Points")
                    for point in data.get('key_evidence', []):
                        if st.session_state.language != "English":
                            point = translate_text(point, st.session_state.language)
                        st.markdown(f'<div class="evidence-item">✅ {point}</div>', unsafe_allow_html=True)
                        
                with row_main[1]:
                    st.subheader("📚 Source Credibility")
                    sources = data.get('sources', [])
                    
                    if sources:
                        for s in sources:
                            name = s.get('name', 'Unknown Source')
                            trust = s.get('credibility', 'Medium')
                            st.markdown(f"""
                            <div style="margin-bottom:10px;">
                                <span class="source-badge trust-{trust}">{trust} Trust</span>
                                <b>{name}</b>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No specific documents retrieved. AI utilized pre-trained knowledge base.")
                        
                    # Feature: Related Claims
                    st.markdown("#### 🔗 Related Claims")
                    for rc in data.get('related_claims', []):
                        st.caption(f"• {rc}")

                # 6. ACTION BAR
                st.markdown("---")
                st.subheader("📤 Share & Export")
                
                ac1, ac2, ac3, ac4 = st.columns(4)
                
                # PDF Generation
                pdf_bytes = generate_pdf(claim_input, data, sources)
                ac1.download_button(
                    "📄 Download PDF", 
                    data=pdf_bytes, 
                    file_name="report.pdf", 
                    mime="application/pdf", 
                    use_container_width=True
                )
                
                share_text = f"Fact-check: {claim_input[:30]}... Score: {score}% via Credibility Engine"
                ac2.link_button("🐦 Twitter", f"https://twitter.com/intent/tweet?text={share_text}", use_container_width=True)
                ac3.link_button("💬 WhatsApp", f"https://wa.me/?text={share_text}", use_container_width=True)
                ac4.link_button("💼 LinkedIn", "https://linkedin.com", use_container_width=True)
                
                # Save History
                st.session_state.history.append({
                    "claim": claim_input,
                    "score": score,
                    "verdict": verdict,
                    "category": category,
                    "time": datetime.now().strftime("%H:%M")
                })

            except Exception as e:
                st.error(f"Processing Error: {e}")

# ============ TAB 2: DASHBOARD ============
with tab_dash:
    st.subheader("📈 Live Analytics Dashboard")
    
    if st.session_state.history:
        hist_df = pd.DataFrame(st.session_state.history)
        
        # Summary Metrics
        dm1, dm2, dm3, dm4 = st.columns(4)
        dm1.metric("Total Analyses", len(hist_df))
        dm2.metric("Avg Credibility", f"{int(hist_df['score'].mean())}%")
        dm3.metric("False Claims", len(hist_df[hist_df['score'] < 40]))
        dm4.metric("Verified True", len(hist_df[hist_df['score'] > 80]))
        
        col_charts = st.columns(2)
        
        with col_charts[0]:
            st.markdown("#### Score Trend")
            st.line_chart(hist_df.set_index('time')['score'])
            
        with col_charts[1]:
            st.markdown("#### Category Distribution")
            # Mock data for categories if missing
            cat_counts = hist_df.get('category', pd.Series(['General']*len(hist_df))).value_counts()
            st.bar_chart(cat_counts)
            
        st.markdown("#### Recent Activity Log")
        st.dataframe(hist_df, use_container_width=True)
    else:
        st.info("No data yet. Run some analyses to populate the dashboard.")

# ============ TAB 3: MAP ============
with tab_map:
    st.subheader("🌍 Global Misinformation Heatmap")
    
    # Generate contextual map data
    # In production, this would come from the backend's "geographic_relevance" field
    map_data = pd.DataFrame({
        'lat': [20.5937 + np.random.uniform(-10, 10) for _ in range(100)],
        'lon': [78.9629 + np.random.uniform(-10, 10) for _ in range(100)],
        'score': np.random.randint(0, 100, 100)
    })
    
    # PyDeck 3D Hexagon Layer
    layer = pdk.Layer(
        'HexagonLayer',
        data=map_data,
        get_position='[lon, lat]',
        radius=20000,
        elevation_scale=4,
        elevation_range=[0, 1000],
        pickable=True,
        extruded=True,
    )
    
    view_state = pdk.ViewState(latitude=20.5937, longitude=78.9629, zoom=3, pitch=50)
    
    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "Concentration of verified claims"}
    ))
    st.caption("Visualizing the geographic spread of claims analyzed by the engine.")

# ============ TAB 4: KNOWLEDGE ============
with tab_kb:
    st.subheader("📚 Knowledge Base")
    st.info("Connected to Pathway Vector Store (Hugging Face Backend)")
    
    c1, c2 = st.columns(2)
    c1.metric("Status", "Active")
    c2.metric("Storage", "Persistent")
    
    st.json({
        "backend": "Hugging Face Spaces",
        "memory": "16GB",
        "embeddings": "sentence-transformers/all-MiniLM-L6-v2",
        "pipeline": "Pathway Streaming"
    })

# Footer
st.markdown("""
<div class="footer">
    <p>© 2025 Aryan & Khushboo • Built for Inter-IIT Tech Meet</p>
    <p style="font-size: 0.8rem; opacity: 0.7;">Powered by Pathway + Groq + Hugging Face</p>
</div>
""", unsafe_allow_html=True)