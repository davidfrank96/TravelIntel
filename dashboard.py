import streamlit as st

st.set_page_config(page_title="TravelIntel", layout="wide")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Outfit:wght@300;400;500;600;700&display=swap');

:root {
  --bg: #071024;
  --bg-2: #0b1b34;
  --panel: rgba(18, 30, 55, 0.7);
  --panel-2: rgba(16, 22, 38, 0.9);
  --line: rgba(255,255,255,0.06);
  --glow: #23d3a2;
  --accent: #36d399;
  --accent-2: #0ea5a3;
  --text: #e9eef9;
  --muted: #9fb0c9;
  --warm: #f6c37a;
  --danger: #f97316;
  --card: rgba(9, 16, 31, 0.8);
}

html, body, [class*="css"]  {
  font-family: 'Outfit', sans-serif;
  color: var(--text);
}

.stApp {
  background: radial-gradient(1200px 600px at 50% -10%, rgba(31, 170, 175, 0.2), transparent 60%),
              radial-gradient(1200px 600px at 50% 0%, rgba(36, 211, 162, 0.15), transparent 55%),
              linear-gradient(180deg, var(--bg), var(--bg-2));
}

.grid-bg {
  background-image:
    linear-gradient(to right, rgba(255,255,255,0.05) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(255,255,255,0.05) 1px, transparent 1px);
  background-size: 60px 60px;
}

.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 36px;
  border-bottom: 1px solid var(--line);
  position: sticky;
  top: 0;
  backdrop-filter: blur(8px);
  z-index: 10;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 700;
  letter-spacing: 0.3px;
}

.nav-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--glow);
  box-shadow: 0 0 12px var(--glow);
}

.nav-links {
  display: flex;
  gap: 24px;
  color: var(--muted);
  font-weight: 500;
}

.nav-cta {
  padding: 10px 18px;
  background: linear-gradient(135deg, #11998e, #38ef7d);
  color: #051018;
  border-radius: 10px;
  font-weight: 700;
  text-decoration: none;
}

.hero {
  padding: 80px 12vw 60px;
  text-align: center;
}

.pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(21, 164, 170, 0.15);
  color: #7ef3e1;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  border: 1px solid rgba(126, 243, 225, 0.35);
}

.hero h1 {
  font-family: 'Space Grotesk', sans-serif;
  font-size: clamp(2.6rem, 5vw, 4.6rem);
  line-height: 1.05;
  margin: 24px 0 12px;
}

.hero h1 span {
  color: var(--accent);
}

.hero p {
  max-width: 720px;
  margin: 0 auto 28px;
  color: var(--muted);
}

.panel {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 28px;
  box-shadow: 0 10px 40px rgba(3, 10, 25, 0.6);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.form-cta {
  margin-top: 18px;
  width: 100%;
  padding: 14px 18px;
  border-radius: 12px;
  background: linear-gradient(135deg, #10b981, #14b8a6);
  border: none;
  color: #031016;
  font-weight: 700;
  font-size: 16px;
}

.stat-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 24px;
  margin: 30px auto 0;
  max-width: 900px;
}

.stat {
  text-align: center;
  color: var(--muted);
}

.stat strong {
  color: var(--text);
  font-size: 22px;
}

.section {
  padding: 70px 10vw;
}

.light {
  background: #f7f7f2;
  color: #0a0f1f;
}

.card {
  background: #ffffff;
  border-radius: 18px;
  padding: 26px;
  border: 1px solid #e7e7e0;
  box-shadow: 0 20px 60px rgba(9, 16, 31, 0.08);
}

.preview-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 28px;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 999px;
  background: #e6f6f2;
  color: #0f766e;
  font-size: 12px;
  font-weight: 600;
}

.risk-bar {
  height: 8px;
  background: linear-gradient(90deg, #22c55e, #eab308, #f97316, #ef4444);
  border-radius: 999px;
  position: relative;
  margin: 12px 0 6px;
}

.risk-marker {
  position: absolute;
  top: -4px;
  left: 38%;
  width: 14px;
  height: 14px;
  border-radius: 999px;
  background: #ffffff;
  border: 2px solid #f59e0b;
}

.preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.preview-panel {
  background: #f9f8f3;
  border-radius: 14px;
  padding: 16px;
  border: 1px solid #eee9dd;
}

.full-section {
  background: linear-gradient(180deg, #0a142a, #0b1630);
  color: #e6edf7;
}

.full-card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 22px;
  box-shadow: 0 20px 60px rgba(3, 10, 25, 0.6);
}

.full-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 18px;
}

.tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(250, 204, 21, 0.15);
  color: #facc15;
  font-size: 12px;
  font-weight: 600;
}

.download-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  background: rgba(18, 38, 64, 0.9);
  border: 1px solid var(--line);
  padding: 18px 22px;
  border-radius: 16px;
  margin-top: 18px;
}

.download-btn {
  background: linear-gradient(135deg, #0ea5a3, #22c55e);
  border-radius: 10px;
  padding: 10px 16px;
  font-weight: 700;
  color: #031016;
}

.steps {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.step {
  text-align: center;
  padding: 16px;
}

.step-badge {
  display: inline-flex;
  width: 34px;
  height: 34px;
  border-radius: 999px;
  align-items: center;
  justify-content: center;
  background: #111827;
  color: #f9fafb;
  font-weight: 700;
  margin-bottom: 10px;
}

.pricing {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 22px;
}

.price-card {
  border-radius: 18px;
  padding: 24px;
  border: 1px solid #e7e7e0;
  background: #ffffff;
}

.price-card.featured {
  border: 2px solid #10b981;
  position: relative;
}

.ribbon {
  position: absolute;
  top: -12px;
  right: 16px;
  background: #10b981;
  color: #051018;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
}

.fade-in {
  animation: fadeIn 1.2s ease forwards;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 800px) {
  .navbar { padding: 12px 18px; flex-direction: column; gap: 12px; }
  .hero { padding: 60px 8vw 40px; }
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

st.markdown(
    """
<div class="navbar grid-bg">
  <div class="nav-left">
    <div class="nav-dot"></div>
    <div>TravelIntel</div>
  </div>
  <div class="nav-links">
    <div>How it works</div>
    <div>Sample briefing</div>
    <div>Pricing</div>
  </div>
  <a class="nav-cta" href="#briefing-form">Get briefing →</a>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<section class="hero grid-bg fade-in">
  <span class="pill">CIA-style intelligence • 260+ countries</span>
  <h1>Your destination.<br><span>Fully briefed.</span></h1>
  <p>
    Enter your travel details and receive a complete, personalised intelligence briefing
    — security, consulates, hospitals, laws, and emergency contacts — in seconds.
  </p>
</section>
""",
    unsafe_allow_html=True,
)

st.markdown('<div id="briefing-form"></div>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("**Generate your briefing**")
    with st.form("briefing_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            name = st.text_input("Full name", "Juno Lee")
            destination_country = st.text_input("Destination country", "United Arab Emirates")
        with col2:
            nationality = st.selectbox("Citizenship / Nationality", ["United States", "Nigeria", "United Kingdom", "Canada", "United Arab Emirates"])
            destination_city = st.text_input("Destination city", "Dubai")
        with col3:
            travel_date = st.date_input("Travel date")
            trip_type = st.selectbox("Trip type", ["Business visit", "Leisure", "Study", "Medical", "Family"])
        submitted = st.form_submit_button("Generate intelligence briefing →")
    st.markdown("<div style='color: #8aa2c1; font-size: 12px; text-align:center; margin-top: 6px;'>Free preview available. Full PDF report unlocked after payment.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    """
<div class="stat-row">
  <div class="stat"><strong>260+</strong><br>Countries covered</div>
  <div class="stat"><strong>50+</strong><br>Intelligence sources</div>
  <div class="stat"><strong>&lt;30s</strong><br>Briefing generated</div>
  <div class="stat"><strong>7-day</strong><br>Data freshness</div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<section class="section light">
  <div class="card fade-in">
    <div class="badge">FREE PREVIEW</div>
    <div class="preview-title" style="margin-top: 10px;">Your destination snapshot</div>
    <p>Every briefing begins with a free risk overview and security snapshot. Full intelligence unlocked after payment.</p>

    <div style="margin-top: 16px;" class="badge">Free tier — Dubai, UAE</div>

    <div style="margin-top: 22px; background:#0a1425; color:#e8f0ff; padding: 18px; border-radius: 14px;">
      <div style="display:flex; justify-content: space-between; align-items:center;">
        <div style="font-weight:600;">Travel Intelligence Debrief — Dubai</div>
        <div class="badge" style="background:#0f2f2f; color:#5eead4;">FREE PREVIEW</div>
      </div>
      <div style="font-size: 12px; color: #9fb0c9; margin-top: 6px;">Juno Lee • US Citizen • Business visit • Generated 16 Mar 2026</div>
    </div>

    <div style="margin-top:16px;">
      <div style="font-weight:600; font-size:12px; text-transform:uppercase; letter-spacing:1px;">Overall threat level</div>
      <div class="risk-bar"><span class="risk-marker"></span></div>
      <div class="badge" style="background:#fff4d6; color:#a16207;">Risk grade: Low–Moderate • Score 2.1 / 5.0</div>
    </div>

    <div class="preview-grid">
      <div class="preview-panel">
        <strong>Security Overview</strong>
        <div style="margin-top:8px; color:#5b554a;">
          Overall threat level: Low–Moderate. Dubai is one of the safest major cities globally due to heavy policing and surveillance.
        </div>
      </div>
      <div class="preview-panel">
        <strong>Emergency Numbers</strong>
        <div style="margin-top:8px; color:#5b554a;">
          Police Emergency: 999<br>Ambulance: 998<br>Fire Department: 997<br>Tourist Police Hotline: +971 4 223 2323
        </div>
      </div>
    </div>
  </div>
</section>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<section class="section full-section grid-bg">
  <div class="fade-in">
    <div style="text-transform:uppercase; letter-spacing:2px; color:#7dd3fc; font-size:12px;">Full Intelligence Briefing — Paid Tier</div>
    <h2 style="font-family:'Space Grotesk', sans-serif; font-size: 34px; margin-top: 10px;">Complete travel debrief</h2>
    <p style="color:#9fb0c9;">This is what unlocks after payment. All sections fully populated.</p>

    <div class="full-card" style="margin-top: 22px;">
      <div style="font-size: 20px; font-weight: 600;">Dubai, United Arab Emirates</div>
      <div style="font-size: 12px; color:#94a3b8; margin-top:4px;">Traveler: Juno Lee • US Citizen • Business visit • 16 Mar 2026</div>
      <div style="margin-top: 12px;">
        <span class="tag">Low–Moderate Risk</span>
        <span class="tag" style="margin-left:8px;">Grade: B+</span>
        <span class="tag" style="margin-left:8px;">Freshness: 2h ago</span>
        <span class="tag" style="margin-left:8px;">4 sources</span>
      </div>
    </div>

    <div class="full-grid" style="margin-top: 18px;">
      <div class="full-card">
        <strong>Security Conditions</strong>
        <div style="margin-top:8px; color:#cbd5f1;">Heavy CCTV coverage and policing citywide. Low violent crime rate but increased pickpocketing in tourist markets.</div>
      </div>
      <div class="full-card">
        <strong>Emergency Numbers</strong>
        <div style="margin-top:8px; color:#cbd5f1;">Police: 999<br>Ambulance: 998<br>Fire: 997<br>Tourist Police: +971 4 223 2323</div>
      </div>
      <div class="full-card">
        <strong>Consulate Support</strong>
        <div style="margin-top:8px; color:#cbd5f1;">U.S. Consulate General Dubai<br>Phone: +971 4 309 4000<br>Emergency assistance & passport services</div>
      </div>
      <div class="full-card">
        <strong>Medical Facilities</strong>
        <div style="margin-top:8px; color:#cbd5f1;">American Hospital Dubai — 24h emergency<br>Rashid Hospital — major public hospital</div>
      </div>
      <div class="full-card">
        <strong>Legal & Cultural Awareness</strong>
        <div style="margin-top:8px; color:#cbd5f1;">Drug laws are extremely strict. Respect local dress standards in religious areas.</div>
      </div>
      <div class="full-card">
        <strong>Operational Guidance</strong>
        <div style="margin-top:8px; color:#cbd5f1;">Use registered taxis or rideshare. Carry passport copy. Avoid political discussions in public.</div>
      </div>
    </div>

    <div class="download-bar">
      <div>
        <strong>Download your intelligence briefing as PDF</strong>
        <div style="color:#94a3b8; font-size: 12px;">CIA-style formatted report • 7-day validity</div>
      </div>
      <div class="download-btn">Download PDF Report</div>
    </div>
  </div>
</section>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<section class="section light">
  <div class="steps">
    <div class="step">
      <div class="step-badge">1</div>
      <strong>Enter travel details</strong>
      <div style="color:#64748b;">Name, nationality, destination city, travel date, and trip type.</div>
    </div>
    <div class="step">
      <div class="step-badge">2</div>
      <strong>System gathers intelligence</strong>
      <div style="color:#64748b;">50+ sources scanned. Structured facts cached for 7 days.</div>
    </div>
    <div class="step">
      <div class="step-badge">3</div>
      <strong>Free preview delivered</strong>
      <div style="color:#64748b;">Risk grade, security overview, and emergency numbers.</div>
    </div>
    <div class="step">
      <div class="step-badge">4</div>
      <strong>Unlock full PDF</strong>
      <div style="color:#64748b;">One-time payment unlocks full briefing and PDF.</div>
    </div>
  </div>
</section>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<section class="section light">
  <div style="text-align:center; margin-bottom: 30px;">
    <div style="font-size:12px; letter-spacing:2px; text-transform:uppercase; color:#64748b;">Pricing</div>
    <h2 style="font-family:'Space Grotesk', sans-serif; font-size: 32px;">Simple, one-time pricing</h2>
    <p style="color:#64748b;">No subscription. Pay per briefing. Free preview always included.</p>
  </div>
  <div class="pricing">
    <div class="price-card">
      <div style="color:#64748b; font-weight:600;">Free</div>
      <div style="font-size: 28px; font-weight:700;">$0<span style="font-size:14px;"> / briefing</span></div>
      <div style="margin-top:10px; color:#64748b;">Instant risk overview for every destination.</div>
      <div style="margin-top:14px; color:#0f172a;">
        ✓ Overall risk grade (A–E)<br>
        ✓ Security overview snapshot<br>
        ✓ Emergency phone numbers<br>
        ✕ Consulate contacts<br>
        ✕ Hospital listings<br>
        ✕ Legal & cultural guide<br>
        ✕ Operational guidance<br>
        ✕ PDF download
      </div>
      <div style="margin-top:18px;" class="download-btn">Generate free preview</div>
    </div>
    <div class="price-card featured">
      <div class="ribbon">Most popular</div>
      <div style="color:#0f172a; font-weight:600;">Full briefing</div>
      <div style="font-size: 28px; font-weight:700;">$9.99<span style="font-size:14px;"> / destination</span></div>
      <div style="margin-top:10px; color:#64748b;">Complete pre-travel intelligence report.</div>
      <div style="margin-top:14px; color:#0f172a;">
        ✓ Everything in Free<br>
        ✓ Consulate matched to your passport<br>
        ✓ Nearest hospitals & medical contacts<br>
        ✓ Legal restrictions & cultural guide<br>
        ✓ Operational travel guidance<br>
        ✓ Key locations & infrastructure<br>
        ✓ Downloadable PDF report<br>
        ✓ Valid 7 days from generation
      </div>
      <div style="margin-top:18px;" class="download-btn">Get full briefing — $9.99</div>
    </div>
  </div>
</section>
""",
    unsafe_allow_html=True,
)

if submitted:
    st.success("Briefing request captured. Hook this form to the /briefings/preview API when ready.")
