import streamlit as st
import time
from datetime import datetime

st.set_page_config(
    page_title="PRIA - Proactive Risk Intelligence Agent",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================
# Session State
# =========================
defaults = {
    "alert_log": [],
    "last_score": 0,
    "last_level": "LOW",
    "last_scan_reasons": [],
    "emergency_triggered": False,
    "countdown_done": False,
    "location_shared": False,
    "assistant_active": False,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================
# Helpers
# =========================
def log_event(text: str) -> None:
    st.session_state.alert_log.insert(
        0,
        {"time": datetime.now().strftime("%H:%M:%S"), "text": text}
    )
    st.session_state.alert_log = st.session_state.alert_log[:8]


def calculate_threat(
    motion: str,
    audio: str,
    location: str,
    time_context: str,
    phone_motion: str,
    user_response: str,
) -> tuple[int, list[str]]:
    score = 0
    reasons = []

    if motion == "Running / Sudden Movement":
        score += 20
        reasons.append("Sudden movement anomaly detected (+20%)")

    if audio == "Loud Noise":
        score += 15
        reasons.append("Elevated noise level detected (+15%)")

    if audio == "Scream / Distress":
        score += 35
        reasons.append("Distress audio pattern detected (+35%)")

    if location == "Isolated Area":
        score += 25
        reasons.append("User located in isolated zone (+25%)")

    if location == "Crowded Area":
        score += 8
        reasons.append("Crowded environment raises uncertainty (+8%)")

    if time_context == "Late Night":
        score += 10
        reasons.append("Late-night contextual vulnerability (+10%)")

    if phone_motion == "Dropped / Violent Shake":
        score += 18
        reasons.append("Phone impact / violent shake detected (+18%)")

    if user_response == "No Response":
        score += 22
        reasons.append("No user response after contextual trigger (+22%)")

    return min(score, 100), reasons


def risk_level_from_score(score: int) -> str:
    if score >= 70:
        return "HIGH"
    if score >= 40:
        return "MODERATE"
    return "LOW"


def gauge_color(score: int) -> str:
    if score >= 70:
        return "#ef4444"
    if score >= 40:
        return "#facc15"
    return "#22c55e"


def assistant_message(score: int, emergency: bool, shared: bool) -> str:
    if emergency and shared:
        return "Emergency mode active. Location shared. Simulated responders have been notified."
    if emergency:
        return "Emergency alert active. Preparing escalation workflow and high-priority safety routing."
    if score >= 70:
        return "Critical risk detected. Recommend immediate escalation and trusted-contact notification."
    if score >= 40:
        return "Moderate risk observed. Stay alert, remain visible, and prepare to escalate if conditions worsen."
    return "Environment appears stable. Passive monitoring remains active."


# =========================
# Styling
# =========================
st.markdown("""
<style>
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(239,68,68,0.10), transparent 22%),
            radial-gradient(circle at top right, rgba(56,189,248,0.08), transparent 20%),
            linear-gradient(135deg, #08111f 0%, #0b1220 45%, #111827 100%);
        color: #f8fafc;
    }

    section.main > div {
        padding-top: 1rem;
    }

    .hero {
        position: relative;
        overflow: hidden;
        padding: 1.5rem 1.6rem;
        border-radius: 24px;
        background: linear-gradient(135deg, rgba(15,23,42,0.95), rgba(30,41,59,0.92));
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 12px 28px rgba(0,0,0,0.30);
        margin-bottom: 0.8rem;
    }

    .hero::before {
        content: "";
        position: absolute;
        width: 180px;
        height: 180px;
        top: -30px;
        right: -30px;
        background: radial-gradient(circle, rgba(239,68,68,0.28), transparent 65%);
        animation: floatGlow 5s ease-in-out infinite;
    }

    .hero-title {
        font-size: 2.3rem;
        font-weight: 800;
        line-height: 1.1;
        color: #f8fafc;
        margin-bottom: 0.35rem;
        position: relative;
        z-index: 2;
    }

    .hero-sub {
        color: #cbd5e1;
        font-size: 1rem;
        position: relative;
        z-index: 2;
    }

    .status-chip {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 0.5rem 0.85rem;
        border-radius: 999px;
        background: rgba(15,23,42,0.65);
        border: 1px solid rgba(255,255,255,0.10);
        color: #e2e8f0;
        font-size: 0.88rem;
        margin-top: 0.9rem;
        position: relative;
        z-index: 2;
    }

    .pulse-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #22c55e;
        box-shadow: 0 0 0 rgba(34,197,94,0.7);
        animation: pulse 1.6s infinite;
    }

    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(34,197,94,0.7); }
        70% { box-shadow: 0 0 0 12px rgba(34,197,94,0); }
        100% { box-shadow: 0 0 0 0 rgba(34,197,94,0); }
    }

    @keyframes floatGlow {
        0% { transform: translateY(0px) scale(1); }
        50% { transform: translateY(10px) scale(1.04); }
        100% { transform: translateY(0px) scale(1); }
    }

    .glass, .dashboard-panel, .gps-card, .assistant-card, .emergency-panel {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.22);
    }

    .glass, .dashboard-panel, .gps-card, .assistant-card, .emergency-panel {
        padding: 0.95rem 1rem;
        margin-bottom: 0.85rem;
    }

    .section-title {
        font-size: 1.12rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 0.75rem;
    }

    .metric-card {
        background: linear-gradient(145deg, rgba(15,23,42,0.92), rgba(30,41,59,0.92));
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        padding: 0.9rem 1rem;
        box-shadow: 0 8px 20px rgba(0,0,0,0.2);
        min-height: 100px;
    }

    .metric-value {
        font-size: 1.9rem;
        font-weight: 800;
        color: #f8fafc;
        margin-bottom: 0.15rem;
    }

    .metric-label {
        color: #94a3b8;
        font-size: 0.92rem;
    }

    .metric-accent-red { color: #f87171; }
    .metric-accent-blue { color: #38bdf8; }
    .metric-accent-green { color: #4ade80; }
    .metric-accent-yellow { color: #facc15; }

    .radar-box {
        position: relative;
        height: 180px;
        border-radius: 18px;
        overflow: hidden;
        background:
            radial-gradient(circle, rgba(34,197,94,0.12) 0%, rgba(34,197,94,0.04) 30%, transparent 60%),
            linear-gradient(180deg, rgba(2,6,23,0.95), rgba(15,23,42,0.95));
        border: 1px solid rgba(255,255,255,0.08);
    }

    .radar-grid {
        position: absolute;
        inset: 0;
        background:
          radial-gradient(circle at center, transparent 18%, rgba(255,255,255,0.06) 19%, transparent 20%),
          radial-gradient(circle at center, transparent 38%, rgba(255,255,255,0.06) 39%, transparent 40%),
          radial-gradient(circle at center, transparent 58%, rgba(255,255,255,0.06) 59%, transparent 60%),
          linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px),
          linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px);
        background-size: 100% 100%, 100% 100%, 100% 100%, 36px 36px, 36px 36px;
    }

    .radar-sweep {
        position: absolute;
        width: 180%;
        height: 180%;
        top: -40%;
        left: -40%;
        background: conic-gradient(from 0deg, transparent 0deg, rgba(34,197,94,0.00) 300deg, rgba(34,197,94,0.28) 340deg, rgba(34,197,94,0.65) 360deg);
        animation: spinRadar 4s linear infinite;
        transform-origin: center center;
    }

    @keyframes spinRadar {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    .radar-center {
        position: absolute;
        width: 14px;
        height: 14px;
        border-radius: 50%;
        background: #4ade80;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        box-shadow: 0 0 20px rgba(74,222,128,0.8);
    }

    .radar-dot {
        position: absolute;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #f87171;
        box-shadow: 0 0 16px rgba(248,113,113,0.8);
        animation: ping 1.5s infinite;
    }

    @keyframes ping {
        0% { transform: scale(1); opacity: 1; }
        80% { transform: scale(1.8); opacity: 0.15; }
        100% { transform: scale(1); opacity: 1; }
    }

    .siren-banner {
        border-radius: 16px;
        padding: 0.95rem 1rem;
        font-weight: 800;
        letter-spacing: 0.4px;
        margin-top: 0.8rem;
        margin-bottom: 0.8rem;
        text-align: center;
        animation: sirenFlash 1s infinite;
        border: 1px solid rgba(255,255,255,0.12);
    }

    @keyframes sirenFlash {
        0% { background: rgba(127,29,29,0.75); color: #fee2e2; }
        50% { background: rgba(239,68,68,0.95); color: white; }
        100% { background: rgba(127,29,29,0.75); color: #fee2e2; }
    }

    .moderate-banner {
        background: rgba(120,53,15,0.35);
        border: 1px solid rgba(250,204,21,0.35);
        color: #fef9c3;
        border-radius: 16px;
        padding: 0.9rem 1rem;
        font-weight: 700;
        text-align: center;
        margin-top: 0.8rem;
    }

    .safe-banner {
        background: rgba(22,101,52,0.35);
        border: 1px solid rgba(74,222,128,0.35);
        color: #dcfce7;
        border-radius: 16px;
        padding: 0.9rem 1rem;
        font-weight: 700;
        text-align: center;
        margin-top: 0.8rem;
    }

    .gauge-wrap {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 0.3rem;
        margin-bottom: 0.6rem;
    }

    .gauge {
        --value: 0;
        --gauge-color: #22c55e;
        width: 210px;
        height: 210px;
        border-radius: 50%;
        background:
            radial-gradient(closest-side, #0f172a 72%, transparent 73% 100%),
            conic-gradient(var(--gauge-color) calc(var(--value) * 1%), rgba(255,255,255,0.08) 0);
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        box-shadow: 0 0 24px rgba(0,0,0,0.22);
    }

    .gauge::before {
        content: "";
        position: absolute;
        width: 78%;
        height: 78%;
        border-radius: 50%;
        background: radial-gradient(circle at top, rgba(255,255,255,0.06), rgba(15,23,42,0.98));
        border: 1px solid rgba(255,255,255,0.06);
    }

    .gauge-inner {
        position: relative;
        z-index: 2;
        text-align: center;
    }

    .gauge-score {
        font-size: 2.3rem;
        font-weight: 800;
        color: #f8fafc;
        line-height: 1;
    }

    .gauge-label {
        margin-top: 0.3rem;
        color: #94a3b8;
        font-size: 0.92rem;
    }

    .countdown-box {
        text-align: center;
        border-radius: 16px;
        padding: 0.8rem;
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        margin-top: 0.7rem;
    }

    .countdown-number {
        font-size: 2rem;
        font-weight: 800;
        color: #f87171;
    }

    .fullscreen-alert {
        border-radius: 18px;
        padding: 1rem;
        text-align: center;
        font-weight: 800;
        font-size: 1.05rem;
        margin-bottom: 0.8rem;
        animation: fullFlash 0.8s infinite;
        border: 1px solid rgba(255,255,255,0.12);
    }

    @keyframes fullFlash {
        0% { background: rgba(127,29,29,0.80); color: #fff1f2; }
        50% { background: rgba(220,38,38,0.98); color: white; }
        100% { background: rgba(127,29,29,0.80); color: #fff1f2; }
    }

    .gps-card, .assistant-card {
        min-height: 255px;
    }

    .gps-map {
        position: relative;
        height: 150px;
        border-radius: 16px;
        overflow: hidden;
        background:
            linear-gradient(rgba(255,255,255,0.06) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.06) 1px, transparent 1px),
            radial-gradient(circle at 50% 45%, rgba(56,189,248,0.16), transparent 30%),
            linear-gradient(180deg, rgba(15,23,42,1), rgba(2,6,23,1));
        background-size: 28px 28px, 28px 28px, 100% 100%, 100% 100%;
        border: 1px solid rgba(255,255,255,0.08);
        margin-bottom: 0.75rem;
    }

    .gps-pin {
        position: absolute;
        width: 18px;
        height: 18px;
        border-radius: 50%;
        background: #38bdf8;
        top: 46%;
        left: 52%;
        transform: translate(-50%, -50%);
        box-shadow: 0 0 0 rgba(56,189,248,0.7);
        animation: gpsPulse 1.7s infinite;
    }

    .gps-pin::after {
        content: "";
        position: absolute;
        width: 30px;
        height: 30px;
        border: 2px solid rgba(56,189,248,0.55);
        border-radius: 50%;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
    }

    @keyframes gpsPulse {
        0% { box-shadow: 0 0 0 0 rgba(56,189,248,0.7); }
        70% { box-shadow: 0 0 0 16px rgba(56,189,248,0); }
        100% { box-shadow: 0 0 0 0 rgba(56,189,248,0); }
    }

    .gps-status, .assistant-bubble, .log-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 0.75rem 0.85rem;
        margin-bottom: 0.6rem;
    }

    .gps-status {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .gps-ok {
        color: #4ade80;
        font-weight: 700;
    }

    .gps-wait {
        color: #facc15;
        font-weight: 700;
    }

    .assistant-visual {
        display: flex;
        justify-content: center;
        align-items: end;
        gap: 8px;
        height: 90px;
        margin: 0.3rem 0 0.8rem 0;
    }

    .bar {
        width: 12px;
        background: linear-gradient(180deg, #a855f7, #38bdf8);
        border-radius: 999px;
        animation: voiceWave 1.1s ease-in-out infinite;
    }

    .bar:nth-child(1) { height: 34px; animation-delay: 0.0s; }
    .bar:nth-child(2) { height: 68px; animation-delay: 0.15s; }
    .bar:nth-child(3) { height: 92px; animation-delay: 0.3s; }
    .bar:nth-child(4) { height: 54px; animation-delay: 0.45s; }
    .bar:nth-child(5) { height: 82px; animation-delay: 0.6s; }
    .bar:nth-child(6) { height: 42px; animation-delay: 0.75s; }

    @keyframes voiceWave {
        0% { transform: scaleY(0.55); opacity: 0.75; }
        50% { transform: scaleY(1.1); opacity: 1; }
        100% { transform: scaleY(0.55); opacity: 0.75; }
    }

    .small-muted {
        color: #94a3b8;
        font-size: 0.88rem;
    }

    .log-time {
        color: #38bdf8;
        font-size: 0.88rem;
        font-weight: 700;
    }

    div.stButton > button {
        width: 100%;
        border-radius: 14px;
        border: none;
        background: linear-gradient(90deg, #ef4444, #f97316);
        color: white;
        font-weight: 800;
        padding: 0.85rem 1rem;
        box-shadow: 0 10px 24px rgba(249,115,22,0.20);
    }

    div[data-baseweb="select"] > div {
        background: rgba(255,255,255,0.92) !important;
        color: black !important;
        border-radius: 12px !important;
    }

    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #ef4444, #f97316, #facc15) !important;
    }

    hr {
        border: none;
        height: 1px;
        background: rgba(255,255,255,0.10);
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# =========================
# Header
# =========================
st.markdown("""
<div class="hero">
    <div class="hero-title">🚨 PRIA - Proactive Risk Intelligence Agent</div>
    <div class="hero-sub">
        AI-powered context-aware threat detection for smart personal safety monitoring and rapid escalation awareness.
    </div>
    <div class="status-chip">
        <div class="pulse-dot"></div>
        System Status: Live Monitoring Ready
    </div>
</div>
""", unsafe_allow_html=True)

top1, top2, top3, top4 = st.columns(4)

with top1:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-value metric-accent-blue">24/7</div>
        <div class="metric-label">Monitoring Uptime</div>
    </div>
    """, unsafe_allow_html=True)

with top2:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-value metric-accent-green">PASSIVE</div>
        <div class="metric-label">Detection Mode</div>
    </div>
    """, unsafe_allow_html=True)

with top3:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-value metric-accent-yellow">LIVE</div>
        <div class="metric-label">Threat Scanner</div>
    </div>
    """, unsafe_allow_html=True)

with top4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value metric-accent-red">{st.session_state.last_score}%</div>
        <div class="metric-label">Last Threat Confidence Score</div>
    </div>
    """, unsafe_allow_html=True)

if st.session_state.emergency_triggered:
    st.markdown("""
    <div class="fullscreen-alert">
        🚨 EMERGENCY ALERT ACTIVE • SIREN MODE ENABLED • CONTACTING SAFETY CHANNEL 🚨
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# =========================
# Input + Radar
# =========================
left, right = st.columns([1.05, 0.95])

with left:
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🔍 Threat Input Console</div>', unsafe_allow_html=True)

    motion = st.selectbox(
        "Motion Pattern",
        ["Normal Movement", "Running / Sudden Movement"]
    )

    audio = st.selectbox(
        "Audio Input",
        ["Quiet", "Loud Noise", "Scream / Distress"]
    )

    location = st.selectbox(
        "Location Type",
        ["Safe Zone", "Crowded Area", "Isolated Area"]
    )

    input_col1, input_col2 = st.columns(2)

    with input_col1:
        time_context = st.selectbox(
            "Time Context",
            ["Daytime", "Evening", "Late Night"]
        )

    with input_col2:
        phone_motion = st.selectbox(
            "Phone Motion",
            ["Stable", "Dropped / Violent Shake"]
        )

    user_response = st.selectbox(
        "User Response Check",
        ["Responsive", "No Response"]
    )

    analyze = st.button("🚀 Analyze Situation")
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="dashboard-panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📡 Live Activity Radar</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="radar-box">
        <div class="radar-grid"></div>
        <div class="radar-sweep"></div>
        <div class="radar-center"></div>
        <div class="radar-dot" style="top: 28%; left: 68%;"></div>
        <div class="radar-dot" style="top: 66%; left: 32%; animation-delay:0.6s;"></div>
        <div class="radar-dot" style="top: 42%; left: 48%; animation-delay:1s;"></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(
        '<div class="small-muted" style="margin-top:0.65rem;">Scanning motion, sound intensity, environmental vulnerability, and response status.</div>',
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# Analyze
# =========================
if analyze:
    st.session_state.emergency_triggered = False
    st.session_state.countdown_done = False
    st.session_state.location_shared = False
    st.session_state.assistant_active = False

    with st.spinner("Analyzing context and verifying threat confidence..."):
        time.sleep(1.0)
        score, reasons = calculate_threat(
            motion=motion,
            audio=audio,
            location=location,
            time_context=time_context,
            phone_motion=phone_motion,
            user_response=user_response,
        )

    st.session_state.last_score = score
    st.session_state.last_scan_reasons = reasons
    st.session_state.last_level = risk_level_from_score(score)

    log_event(f"Threat scan complete — Risk {st.session_state.last_level} ({score}%).")

    # Autonomous escalation for high-confidence threat
    if score >= 70:
        st.session_state.emergency_triggered = True
        st.session_state.assistant_active = True
        log_event("High-confidence threat detected. Autonomous emergency workflow started.")

score = st.session_state.last_score
level = st.session_state.last_level
reasons = st.session_state.last_scan_reasons

# =========================
# Dashboard
# =========================
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown('<div class="section-title">🛡 Security Dashboard</div>', unsafe_allow_html=True)
st.caption("PRIA autonomously fuses motion, audio, location, time, and response context to estimate threat confidence.")

c1, c2, c3 = st.columns([0.9, 0.85, 1.25])

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value metric-accent-red">{score}%</div>
        <div class="metric-label">Threat Confidence Score</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    level_class = "metric-accent-green" if level == "LOW" else "metric-accent-yellow" if level == "MODERATE" else "metric-accent-red"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value {level_class}">{level}</div>
        <div class="metric-label">Risk Category</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value metric-accent-blue">{len(reasons)}</div>
        <div class="metric-label">Triggered Factors</div>
    </div>
    """, unsafe_allow_html=True)

st.progress(score / 100 if score else 0)

if score >= 70:
    st.markdown("""
    <div class="siren-banner">
        🚨 HIGH THREAT DETECTED — SILENT VERIFIED ALERT AUTONOMOUSLY ACTIVATED 🚨
    </div>
    """, unsafe_allow_html=True)
elif score >= 40:
    st.markdown("""
    <div class="moderate-banner">
        ⚠️ Moderate risk detected. Watch mode active and escalation is on standby.
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="safe-banner">
        ✅ Low-risk environment detected. No immediate escalation required.
    </div>
    """, unsafe_allow_html=True)

# =========================
# Gauge + Emergency
# =========================
g1, g2 = st.columns([1, 1])

with g1:
    st.markdown('<div class="dashboard-panel">', unsafe_allow_html=True)
    st.markdown("### 🎯 Live Risk Meter")

    current_color = gauge_color(score)
    st.markdown(f"""
    <div class="gauge-wrap">
        <div class="gauge" style="--value:{score}; --gauge-color:{current_color};">
            <div class="gauge-inner">
                <div class="gauge-score">{score}%</div>
                <div class="gauge-label">Risk Intensity</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if score == 0:
        st.info("No scan yet. Run a threat scan to populate the live risk meter.")
    elif score >= 70:
        st.markdown('<div class="small-muted" style="text-align:center;">Critical threat band reached. Escalation path activated.</div>', unsafe_allow_html=True)
    elif score >= 40:
        st.markdown('<div class="small-muted" style="text-align:center;">Elevated threat band detected. Active monitoring recommended.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="small-muted" style="text-align:center;">Baseline safety band. Passive monitoring active.</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

with g2:
    st.markdown('<div class="emergency-panel">', unsafe_allow_html=True)
    st.markdown('<div class="emergency-title">🚑 Emergency Response Console</div>', unsafe_allow_html=True)
    st.markdown("Autonomous escalation starts on high-confidence threat. You can also trigger it manually for demo purposes.")

    emergency_col1, emergency_col2 = st.columns(2)

    with emergency_col1:
        trigger_emergency = st.button("🚨 Trigger Emergency Alert")

    with emergency_col2:
        clear_emergency = st.button("🛑 Reset Alert State")

    if trigger_emergency:
        st.session_state.emergency_triggered = True
        st.session_state.countdown_done = False
        st.session_state.assistant_active = True
        log_event("Emergency alert manually triggered by user.")

    if clear_emergency:
        st.session_state.emergency_triggered = False
        st.session_state.countdown_done = False
        st.session_state.location_shared = False
        st.session_state.assistant_active = False
        log_event("Emergency alert state reset.")
        st.rerun()

    if st.session_state.emergency_triggered and not st.session_state.countdown_done:
        countdown_placeholder = st.empty()
        progress_placeholder = st.empty()

        for i in [5, 4, 3, 2, 1]:
            countdown_placeholder.markdown(f"""
            <div class="countdown-box">
                <div class="small-muted">Dispatching emergency workflow in</div>
                <div class="countdown-number">{i}</div>
            </div>
            """, unsafe_allow_html=True)
            progress_placeholder.progress((6 - i) / 5)
            time.sleep(0.55)

        st.session_state.countdown_done = True
        st.session_state.location_shared = True

        countdown_placeholder.markdown("""
        <div class="countdown-box">
            <div class="small-muted">Emergency workflow status</div>
            <div class="countdown-number" style="font-size:1.3rem;color:#4ade80;">ALERT SENT</div>
        </div>
        """, unsafe_allow_html=True)
        progress_placeholder.progress(1.0)

        st.error("Emergency alert sent to simulated safety network.")
        st.warning("Siren mode enabled. Location sharing and rapid contact escalation simulated.")
        log_event("Emergency workflow dispatched successfully.")
        log_event("Live location shared with trusted safety contact.")

    elif st.session_state.emergency_triggered and st.session_state.countdown_done:
        st.success("Emergency workflow is active.")
        if st.session_state.location_shared:
            st.info("Live location sharing is enabled.")
    else:
        st.info("Emergency console is idle.")

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# GPS + Voice Assistant
# =========================
p1, p2 = st.columns(2)

with p1:
    st.markdown('<div class="gps-card">', unsafe_allow_html=True)
    st.markdown("### 📍 Live GPS Relay")
    st.markdown("""
    <div class="gps-map">
        <div class="gps-pin"></div>
    </div>
    """, unsafe_allow_html=True)

    share_status = "SHARED" if st.session_state.location_shared else "STANDBY"
    share_class = "gps-ok" if st.session_state.location_shared else "gps-wait"

    st.markdown(f"""
    <div class="gps-status">
        <span>Location Relay Status</span>
        <span class="{share_class}">{share_status}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="gps-status">
        <span>Approx Zone</span>
        <span>Aurangabad Demo Sector</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="gps-status">
        <span>Trusted Contact Sync</span>
        <span class="{share_class}">{'ACTIVE' if st.session_state.location_shared else 'WAITING'}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="small-muted">This is a hackathon visual simulation, not real GPS tracking.</div>',
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

with p2:
    st.markdown('<div class="assistant-card">', unsafe_allow_html=True)
    st.markdown("### 🎙 Voice Safety Assistant")

    st.markdown("""
    <div class="assistant-visual">
        <div class="bar"></div>
        <div class="bar"></div>
        <div class="bar"></div>
        <div class="bar"></div>
        <div class="bar"></div>
        <div class="bar"></div>
    </div>
    """, unsafe_allow_html=True)

    assistant_text = assistant_message(
        score=score,
        emergency=st.session_state.emergency_triggered,
        shared=st.session_state.location_shared
    )

    st.markdown(f"""
    <div class="assistant-bubble">
        <strong>PRIA Voice Assistant:</strong><br>
        {assistant_text}
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.emergency_triggered:
        st.markdown("""
        <div class="assistant-bubble">
            <strong>Suggested voice prompt:</strong><br>
            “Emergency detected. Stay calm. Help is being alerted. Move to a visible area if possible.”
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="assistant-bubble">
            <strong>Suggested voice prompt:</strong><br>
            “Monitoring active. Environment appears under observation. Re-scan if the situation changes.”
        </div>
        """, unsafe_allow_html=True)

    st.markdown(
        '<div class="small-muted">Animated assistant panel simulates a spoken AI safety guide.</div>',
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# Explainability + Response
# =========================
a, b = st.columns([1.05, 0.95])

with a:
    st.markdown('<div class="dashboard-panel">', unsafe_allow_html=True)
    st.markdown("### 🧠 Explainability Engine")
    if reasons:
        for reason in reasons:
            st.markdown(f"- {reason}")
    else:
        st.info("No risk signals analyzed yet. Run a scan to generate threat intelligence.")
    st.markdown('</div>', unsafe_allow_html=True)

with b:
    st.markdown('<div class="dashboard-panel">', unsafe_allow_html=True)
    st.markdown("### 📋 Response Recommendation")
    if score >= 70:
        st.markdown("""
- Trigger emergency contact workflow
- Share live location with trusted contact
- Escalate to central safety team
- Keep siren alert mode active
        """)
    elif score >= 40:
        st.markdown("""
- Stay in visible/public space
- Keep phone accessible
- Monitor surroundings actively
- Prepare escalation if risk rises
        """)
    else:
        st.markdown("""
- Continue normal activity
- Maintain passive monitoring
- Reassess if surroundings change
        """)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# =========================
# Logs + Notes
# =========================
log_col, note_col = st.columns([1.1, 0.9])

with log_col:
    st.markdown('<div class="dashboard-panel">', unsafe_allow_html=True)
    st.markdown("### 📜 Alert Log")
    if st.session_state.alert_log:
        for item in st.session_state.alert_log:
            st.markdown(f"""
            <div class="log-card">
                <div class="log-time">{item['time']}</div>
                <div>{item['text']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No alert events recorded yet.")
    st.markdown('</div>', unsafe_allow_html=True)

with note_col:
    st.markdown('<div class="dashboard-panel">', unsafe_allow_html=True)
    st.markdown("### 🔐 System Note")
    st.markdown("""
PRIA uses a multi-factor context-aware intelligence engine to estimate risk from:
- motion anomalies
- audio distress signals
- environmental vulnerability
- time-context sensitivity
- user response status

This dashboard is a hackathon demo simulation for proactive detection, silent verified alerts, guided response, and location relay UX.
    """)
    st.markdown('</div>', unsafe_allow_html=True)
