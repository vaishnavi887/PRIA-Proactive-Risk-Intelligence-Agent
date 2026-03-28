import streamlit as st

st.set_page_config(page_title="PRIA - Risk Intelligence", page_icon="🚨")

st.title("🚨 PRIA - Proactive Risk Intelligence Agent")
st.markdown("### Context-Aware Threat Detection System")

st.markdown("---")

st.subheader("🔍 Simulate Environment Inputs")

motion = st.selectbox("Motion Pattern", ["Normal Movement", "Running / Sudden Movement"])
audio = st.selectbox("Audio Input", ["Quiet", "Loud Noise", "Scream / Distress"])
location = st.selectbox("Location Type", ["Safe Zone", "Crowded Area", "Isolated Area"])

st.markdown("---")

def calculate_threat(motion, audio, location):
    score = 0
    reasons = []

    if motion == "Running / Sudden Movement":
        score += 20
        reasons.append("Sudden movement detected (+20%)")

    if audio == "Loud Noise":
        score += 20
        reasons.append("High noise level (+20%)")

    if audio == "Scream / Distress":
        score += 40
        reasons.append("Distress signal detected (+40%)")

    if location == "Isolated Area":
        score += 30
        reasons.append("User in isolated area (+30%)")

    if location == "Crowded Area":
        score += 10
        reasons.append("Crowded environment (+10%)")

    return min(score, 100), reasons


if st.button("🚀 Analyze Situation"):
    score, reasons = calculate_threat(motion, audio, location)

    st.markdown(f"## 📊 Threat Score: **{score}%**")

    if score >= 70:
        st.error("🚨 HIGH THREAT DETECTED! Alert Triggered")
    elif score >= 40:
        st.warning("⚠️ Moderate Risk - Stay Alert")
    else:
        st.success("✅ Situation Safe")

    st.markdown("### 🧠 Explainability (Why this result?)")

    if reasons:
        for r in reasons:
            st.write(f"- {r}")
    else:
        st.write("- No significant risk factors detected")

    st.markdown("---")
    st.info("🔐 This system uses multi-factor context analysis to determine threat levels.")
