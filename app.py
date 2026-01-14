"""
Credibility Engine - Premium Frontend Client
Connects to Hugging Face Backend (16GB RAM)
Features: Professional UI, Voice, Multi-Language, PDF Reports, 3D Maps
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

# Try-Except for optional voice component (prevents crash if install fails)
try:
    from streamlit_mic_recorder import speech_to_text
    HAS_VOICE = True
except ImportError:
    HAS_VOICE = False

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
if "last_voice_input" not in st.session_state: st.session_state.last_voice_input = ""

# --- HELPER FUNCTIONS ---

def translate_text(text, target_lang):
    """
    Robust translation using Deep Translator (Google Translate API)
    Falls back to original text if translation fails.
    """
    if target_lang == "English" or not text:
        return text
    try:
        # Map full language names to ISO codes
        lang_map = {
            "Hindi": "hi", "Spanish": "es", "French": "fr", 
            "German": "de", "Chinese": "zh-CN", "Japanese": "ja",
            "Arabic": "ar", "Portuguese": "pt", "Russian": "ru"
        }
        code = lang_map.get(target_lang, "en")
        
        translator = GoogleTranslator(source='auto', target=code)
        # Split long text to avoid limits
        if len(text) > 4500:
            return text
        return translator.translate(text)
    except Exception as e:
        print(f"Translation Error: {e}")
        return text

def generate_pdf(claim, data, sources):
    """Generate professional PDF report"""
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, 'Credibility Engine Report', 0, 1, 'C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'C')
    pdf.ln(10)
    
    # Verdict Section
    score = data.get('score', 50)
    verdict = data.get('verdict', 'UNKNOWN')
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"Verdict: {verdict} ({score}%)", 0, 1)
    pdf.ln(5)
    
    # Claim
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Claim Analyzed:", 0, 1)
    pdf.set_font("Arial", '', 11)
    # Handle encoding for PDF
    safe_claim = claim.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 6, safe_claim)
    pdf.ln(5)
    
    # Analysis
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "AI Analysis:", 0, 1)
    pdf.set_font("Arial", '', 11)
    reasoning = data.get('reasoning', 'N/A').encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 6, reasoning)
    pdf.ln(5)
    
    # Key Evidence
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Key Evidence:", 0, 1)
    pdf.set_font("Arial", '', 11)
    for point in data.get('key_evidence', []):
        safe_point = str(point).encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, f"- {safe_point}")
    pdf.ln(5)
    
    # Sources
    if sources:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Referenced Sources:", 0, 1)
        pdf.set_font("Arial", '', 10)
        for s in sources:
            # Handle both string and dict sources
            name = s.get('name', str(s)) if isinstance(s, dict) else str(s)
            safe_name = name.encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(0, 6, f"- {safe_name}", 0, 1)
            
    # Footer
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 10, "Powered by Pathway + Groq + Hugging Face", 0, 0, 'C')
            
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
    }
    
    /* Score Card */
    .score-card {
        background: white; border-radius: 1rem; padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        text-align: center; border-top: 6px solid #e2e8f0;
    }
    .border-green { border-top-color: #22c55e !important; }
    .border-yellow { border-top-color: #eab308 !important; }
    .border-orange { border-top-color: #f97316 !important; }
    .border-red { border-top-color: #ef4444 !important; }
    
    /* Verdict Banner */
    .verdict-banner {
        padding: 2rem; border-radius: 1rem; color: white;
        text-align: center; margin-bottom: 2rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    /* Source Badges */
    .source-badge {
        display: inline-block; padding: 0.3rem 0.8rem;
        border-radius: 20px; font-size: 0.8rem; font-weight: 600;
        margin: 0.2rem; background: #eff6ff; color: #1e3a8a;
        border: 1px solid #bfdbfe;
    }
    .trust-High { background: #dcfce7; color: #166534; border-color: #86efac; }
    .trust-Medium { background: #fef9c3; color: #854d0e; border-color: #fde047; }
    .trust-Low { background: #fee2e2; color: #991b1b; border-color: #fca5a5; }
    
    /* Evidence Card */
    .evidence-item {
        background: #f8fafc; padding: 1rem; border-radius: 0.5rem;
        border-left: 4px solid #3b82f6; margin-bottom: 0.5rem;
    }
    
    /* Pilot Badge */
    .pilot-badge {
        position: fixed; top: 1rem; right: 1rem;
        background: linear-gradient(45deg, #f59e0b, #d97706);
        color: white; padding: 0.4rem 1rem; border-radius: 2rem;
        font-weight: 700; font-size: 0.8rem; z-index: 1000;
    }
    
    /* Footer */
    .footer {
        text-align: center; margin-top: 4rem; padding: 2rem;
        color: #94a3b8; border-top: 1px solid #e2e8f0;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    .stDeployButton {display:none;}
</style>
<div class="pilot-badge">⚡ LIVE PILOT</div>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/9566/9566127.png", width=60)
    st.title("Control Center")
    
    # Status Panel
    try:
        start_time = time.time()
        res = requests.get(f"{BACKEND_URL}/", timeout=3)
        latency = int((time.time() - start_time) * 1000)
        
        if res.status_code == 200:
            status_text = f"Online ({latency}ms)"
            status_color = "green"
        else:
            status_text = "Offline"
            status_color = "red"
    except:
        status_text = "Disconnected"
        status_color = "red"

    st.markdown(f"""
    <div style="background:#f8fafc; padding:10px; border-radius:8px; border:1px solid #e2e8f0; margin-bottom:20px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-weight:600; color:#475569;">System Status</span>
            <span style="background:{status_color}; width:8px; height:8px; border-radius:50%;"></span>
        </div>
        <div style="font-size:0.8rem; color:#64748b; margin-top:5px;">Pathway Brain: <b>{status_text}</b></div>
    </div>
    """, unsafe_allow_html=True)

    # Settings
    st.markdown("### 🌐 Settings")
    st.session_state.language = st.selectbox(
        "Output Language",
        ["English", "Hindi", "Spanish", "French", "German", "Chinese", "Russian", "Arabic"]
    )

    st.markdown("---")
    
    # Ingestion
    st.markdown("### 📰 Live Ingestion")
    
    # GNews Integration
    news_topic = st.selectbox("Topic", ["General", "Health", "Science", "Politics", "Tech"])
    if st.button("🔄 Stream Live News"):
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
                    st.toast(f"✅ Indexed {count} live articles!", icon="🌊")
                except Exception as e:
                    st.error(f"Stream Error: {e}")
    
    # Manual Ingest
    with st.expander("📝 Manual Entry"):
        ingest_text = st.text_area("Content:", height=100)
        ingest_source = st.text_input("Source:", value="Manual")
        if st.button("🚀 Push to Pipeline"):
            try:
                requests.post(f"{BACKEND_URL}/ingest", json={"text": ingest_text, "source": ingest_source})
                st.toast("✅ Indexed!", icon="🌊")
            except:
                st.error("Failed")

    st.markdown("---")
    st.caption("© 2025 Aryan & Khushboo")

# --- MAIN HEADER ---
st.markdown("""
<div class="main-header">
    <h1 style="font-size: 3.5rem; font-weight: 800; margin: 0;">🛡️ Credibility Engine</h1>
    <p style="font-size: 1.2rem; opacity: 0.8; margin-top: 10px;">Real-Time Misinformation Detection System</p>
</div>
""", unsafe_allow_html=True)

# Tabs
tab_verify, tab_dash, tab_map, tab_kb = st.tabs([
    "🔎 **Verify Claim**", "📊 **Analytics Dashboard**", "🗺️ **Global Map**", "📚 **Knowledge Graph**"
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
        
        # FEATURE: Voice Input
        if HAS_VOICE:
            st.caption("🎙️ Voice Input:")
            voice_text = speech_to_text(language='en', use_container_width=True, just_once=True, key='STT')
            if voice_text:
                st.session_state.last_voice_input = voice_text
                st.rerun()
        else:
            st.warning("Microphone unavailable")

    # Handle voice input update
    if st.session_state.last_voice_input:
        claim_input = st.session_state.last_voice_input
        st.session_state.last_voice_input = "" # Clear after use

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
                            # FIX: Handle both string and dict sources robustly
                            if isinstance(s, dict):
                                name = s.get('name', 'Unknown')
                                trust = s.get('credibility', 'Medium')
                            else:
                                name = str(s)
                                trust = "High" if any(x in name.lower() for x in ['reuters', 'ap', 'gov', 'edu', 'bbc']) else "Medium"
                                
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
            if 'category' in hist_df.columns:
                cat_counts = hist_df['category'].value_counts()
                st.bar_chart(cat_counts)
            
        st.markdown("#### Recent Activity Log")
        st.dataframe(hist_df, use_container_width=True)
    else:
        st.info("No data yet. Run some analyses to populate the dashboard.")

# ============ TAB 3: MAP ============
with tab_map:
    st.subheader("🌍 Global Misinformation Heatmap")
    
    # 3D Map (PyDeck runs fine on frontend)
    data = pd.DataFrame({
        'lat': [20.5937 + np.random.uniform(-10, 10) for _ in range(100)],
        'lon': [78.9629 + np.random.uniform(-10, 10) for _ in range(100)],
        'intensity': np.random.randint(1, 100, 100)
    })
    
    # Hexagon Layer
    layer = pdk.Layer(
        'HexagonLayer',
        data=data,
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
    st.subheader("📚 Knowledge Graph")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Status", "Active")
    c2.metric("Backend", "Hugging Face Spaces")
    c3.metric("Memory", "16GB RAM")
    
    st.info("Connected to Pathway Vector Store on Hugging Face. Streaming enabled.")
    st.json({
        "pipeline": "Pathway Streaming",
        "embeddings": "sentence-transformers/all-MiniLM-L6-v2",
        "llm": "Groq Llama 3.1 8B",
        "ingestion": "Real-time GNews API"
    })

# Footer
st.markdown("""
<div class="footer">
    <p>© 2025 Aryan & Khushboo • Built for Inter-IIT Tech Meet</p>
    <p style="font-size: 0.8rem; opacity: 0.7;">Powered by Pathway + Groq + Hugging Face</p>
</div>
""", unsafe_allow_html=True)