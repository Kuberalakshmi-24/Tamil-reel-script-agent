# Python Frontend Integration Plan: Tamil Reel Script Agent

**Objective:** Build a clean, interactive, pure-Python web user interface for the Tamil Reel Script Agent that allows content creators and marketers to generate, inspect, fine-tune, and regenerate video scripts without touching the terminal.

---

## 1. Technology Selection: Why Streamlit?

For a Python-native frontend, **Streamlit** is the ideal solution:
* **100% Python:** No HTML, CSS, JavaScript, or Node.js required.
* **Native Session State (`st.session_state`):** Retains generated scripts in memory so clicking *"⚡ Regenerate Hook"* or *"🎯 Regenerate CTA"* updates immediately without re-running web search or losing the script body.
* **Built-in Rich Formatting:** Native support for Markdown, status badges, expandable source accordions, and 1-click file download buttons (`.md` and `.json`).
* **Direct Integration or REST API:** Can either import `TamilReelScriptPipeline` directly for lightweight single-process execution or connect to the FastAPI backend via HTTP.

---

## 2. UI Layout & Wireframe Design

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│  🎬 Tamil Reel Script Studio (VG Digital Falcon)                             │
├──────────────────────────┬───────────────────────────────────────────────────┤
│  SIDEBAR: PARAMETERS     │  MAIN PANEL (Tabs)                                │
│                          │                                                   │
│  Topic:                  │  [ 🎬 Script & Hooks ] [ 🔍 Research ] [ 🛡️ QC ]   │
│  [Why websites fail...]  │                                                   │
│                          │  ▶ Recommended Hook:                              │
│  Platform:               │  "90% business websites oru brochure maadhiri..." │
│  (o) Instagram Reels     │  [⚡ Regenerate Hooks]                            │
│  ( ) YouTube Shorts      │                                                   │
│                          │  ▶ Spoken Script (Target: 60-75w | Actual: 67w):  │
│  Duration:               │  [Hook] ...                                       │
│  [ 30s | 45s | 60s ]     │  [Context] ...                                    │
│                          │  [Body] ...                                       │
│  Tone:                   │  [Engagement] ...                                 │
│  (o) Tanglish            │  [CTA] ...                                        │
│  ( ) Spoken Tamil Script │  [🎯 Regenerate CTA]                              │
│                          │                                                   │
│  Objective:              │  ▶ Production Notes:                              │
│  [Get agency leads]      │  • On-Screen Overlays  • Caption & Hashtags       │
│                          │                                                   │
│  [ 🚀 Generate Script ]  │  [ 📥 Download Markdown ]  [ 💾 Download JSON ]   │
└──────────────────────────┴───────────────────────────────────────────────────┘
```

---

## 3. Architecture & File Structure

```text
Tamil-reel-script-agent/
├── app.py                     # Streamlit frontend application
├── src/                       # Core pipeline and agent models
│   ├── pipeline.py
│   ├── models.py
│   └── ...
├── deliverables/              # Output files
└── requirements.txt           # Adds: streamlit>=1.35.0
```

---

## 4. Complete Implementation Code (`app.py`)

Create `app.py` in the root of the workspace:

```python
"""Streamlit Web UI for Tamil Reel Script Agent (VG Digital Falcon)."""

import streamlit as st
from pathlib import Path
from src.models import ScriptInput, FullDeliverable
from src.pipeline import TamilReelScriptPipeline
from src.config import WORD_COUNT_LIMITS

# Page Configuration
st.set_page_config(
    page_title="Tamil Reel Script Agent",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling for polished dashboard look
st.markdown(
    """
    <style>
    .main-title { font-size: 2.2rem; font-weight: 700; margin-bottom: 0.2rem; color: #1E293B; }
    .subtitle { font-size: 1.05rem; color: #64748B; margin-bottom: 1.5rem; }
    .badge-pass { background-color: #DCFCE7; color: #15803D; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
    .badge-flag { background-color: #FEE2E2; color: #B91C1C; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
    .metric-card { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 15px; margin-bottom: 15px; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_pipeline():
    """Cache pipeline instance to avoid re-initializing clients on re-render."""
    return TamilReelScriptPipeline()


pipeline = get_pipeline()

# Initialize Session State
if "deliverable" not in st.session_state:
    st.session_state.deliverable = None

# Header
st.markdown('<div class="main-title">🎬 Tamil Reel Script Studio</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Research-backed, duration-calibrated Tamil & Tanglish short-form video scripts</div>',
    unsafe_allow_html=True,
)

# --- SIDEBAR: PARAMETERS ---
with st.sidebar:
    st.header("⚙️ Script Settings")

    topic = st.text_area(
        "Primary Topic / Question *",
        value="Why are businesses not getting leads from their websites?",
        placeholder="Enter your video topic in Tamil, Tanglish, or English...",
        height=100,
    )

    platform = st.selectbox(
        "Platform",
        options=["Instagram Reels", "YouTube Shorts", "Facebook Reels"],
        index=0,
    )

    duration = st.select_slider(
        "Target Duration (seconds)",
        options=[30, 45, 60],
        value=30,
        help="Calibrated to spoken Tamil pace (~2.2 words/sec).",
    )

    limits = WORD_COUNT_LIMITS.get(duration, {"min": 60, "max": 75})
    st.caption(f"⏱️ Spoken target: **{limits['min']} – {limits['max']} words**")

    tone = st.radio(
        "Language & Script Tone",
        options=["Tanglish", "conversational spoken Tamil", "Tamil"],
        index=0,
        help="Tanglish writes Tamil in English alphabet. Conversational Tamil writes natural spoken Tamil script.",
    )

    objective = st.text_input(
        "Marketing Objective",
        value="Get agency leads",
        placeholder="e.g. Get agency leads, awareness, book consultation",
    )

    with st.expander("Target Persona & Niche (Optional)"):
        audience = st.text_input("Audience", value="Small business owners")
        niche = st.text_input("Niche / Industry", value="Digital Marketing / Web")

    generate_btn = st.button("🚀 Generate Reel Script", type="primary", use_container_width=True)

# --- ACTION: FULL GENERATION ---
if generate_btn:
    if not topic.strip():
        st.error("Please enter a topic.")
    else:
        with st.status("Generating research-backed script...", expanded=True) as status:
            st.write("🔍 Running live web searches and finding reputable citations...")
            inp = ScriptInput.create_with_defaults(
                topic=topic,
                audience=audience,
                niche=niche,
                platform=platform,
                duration=duration,
                tone=tone,
                objective=objective,
                mode="full_script",
            )
            st.write("✍️ Writing viral hooks and spoken script segments...")
            st.write("🛡️ Auditing quality and calibrating duration...")
            st.session_state.deliverable = pipeline.run(inp)
            status.update(label="Script generated and certified!", state="complete", expanded=False)

# --- DISPLAY OUTPUT ---
deliverable: FullDeliverable = st.session_state.deliverable

if deliverable:
    # Top stats
    actual_words = deliverable.script.word_count
    limits = WORD_COUNT_LIMITS.get(deliverable.input_data.duration, {"min": 60, "max": 75})
    is_duration_ok = limits["min"] <= actual_words <= limits["max"]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Topic", deliverable.input_data.topic[:30] + "...")
    col2.metric("Duration", f"{deliverable.input_data.duration}s")
    col3.metric("Word Count", f"{actual_words} words", delta="On target" if is_duration_ok else "Review")
    col4.metric("Language Tone", deliverable.input_data.tone)

    tab_script, tab_research, tab_qc, tab_markdown = st.tabs(
        ["🎬 Final Script & Hooks", "🔍 Research & Sources", "🛡️ Quality Audit", "📝 Raw Deliverable"]
    )

    # --- TAB 1: SCRIPT & HOOKS ---
    with tab_script:
        st.subheader("🎣 Hook Options")
        hook_cols = st.columns(3)
        for idx, h in enumerate(deliverable.script.hooks):
            with hook_cols[idx]:
                badge = "⭐ **[RECOMMENDED]**" if h.is_recommended else ""
                st.markdown(f"**Option {idx+1} ({h.type.title()})** {badge}")
                st.info(f"\"{h.text}\"")
                if h.reason:
                    st.caption(f"Reason: {h.reason}")

        # Regenerate Hook button
        if st.button("⚡ Regenerate 3 Fresh Hooks", help="Generates 3 new hooks while preserving research and script body."):
            with st.spinner("Regenerating hook options..."):
                st.session_state.deliverable = pipeline.run(
                    ScriptInput.create_with_defaults(
                        topic=deliverable.input_data.topic,
                        duration=deliverable.input_data.duration,
                        tone=deliverable.input_data.tone,
                        objective=deliverable.input_data.objective,
                        mode="regenerate_hook",
                    ),
                    previous_deliverable=deliverable,
                )
                st.rerun()

        st.divider()

        st.subheader("📜 Spoken Reel Script")
        st.markdown(
            f"*(Duration: **{deliverable.input_data.duration}s** | Spoken Words: **{actual_words}** | Target: {limits['min']}-{limits['max']})*"
        )

        st.markdown(f"**[Hook]**\n> {deliverable.script.hook}")
        st.markdown(f"**[Context]**\n> {deliverable.script.context}")

        st.markdown("**[Body Points]**")
        for p in deliverable.script.body_points:
            st.markdown(f"- {p}")

        st.markdown(f"**[Engagement Question]**\n> {deliverable.script.engagement}")
        st.markdown(f"**[Call To Action (CTA)]**\n> **{deliverable.script.cta}**")

        # Regenerate CTA button
        if st.button("🎯 Regenerate CTA", help="Generates 3 fresh CTAs matching the objective."):
            with st.spinner("Regenerating CTA options..."):
                st.session_state.deliverable = pipeline.run(
                    ScriptInput.create_with_defaults(
                        topic=deliverable.input_data.topic,
                        duration=deliverable.input_data.duration,
                        tone=deliverable.input_data.tone,
                        objective=deliverable.input_data.objective,
                        mode="regenerate_cta",
                    ),
                    previous_deliverable=deliverable,
                )
                st.rerun()

        st.divider()

        st.subheader("🎥 Production Notes")
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            st.markdown("**On-Screen Text Overlays:**")
            for ost in deliverable.script.on_screen_texts:
                st.markdown(f"• `{ost}`")
        with p_col2:
            st.markdown("**Caption & Hashtags:**")
            st.caption(deliverable.script.caption)
            st.code(" ".join(deliverable.script.hashtags))

    # --- TAB 2: RESEARCH & CITATIONS ---
    with tab_research:
        st.subheader("💡 Key Research Findings")
        for kf in deliverable.research.key_findings:
            st.markdown(f"- {kf}")

        st.markdown(f"**Chosen Angle:** {deliverable.research.chosen_angle}")
        st.caption(f"Why chosen: {deliverable.research.angle_reason}")

        st.divider()

        st.subheader("🎯 Audience Pain Points")
        for pp in deliverable.research.pain_points:
            st.markdown(f"- ⚠️ {pp}")

        st.divider()

        st.subheader("🔗 Verified Web Sources")
        if deliverable.research.sources:
            for s in deliverable.research.sources:
                st.markdown(f"- [{s.title or s.url}]({s.url}) — *Supports: {s.claim_supported}*")
        else:
            st.write("No external links logged.")

        if deliverable.research.uncertainties:
            st.warning("**Verification Notice:**\n" + "\n".join(f"- {u}" for u in deliverable.research.uncertainties))

    # --- TAB 3: QUALITY AUDIT ---
    with tab_qc:
        st.subheader("🛡️ 5-Point Quality Compliance Report")
        qc = deliverable.quality_check

        checks = [
            ("Unsupported Claims", qc.unsupported_claims),
            ("Repetition", qc.repetition),
            ("Weak CTA", qc.weak_cta),
            ("Unnatural / Formal Tamil", qc.unnatural_tamil),
            ("Duration Fit", qc.duration_fit),
        ]

        for name, item in checks:
            badge_class = "badge-pass" if item.status == "PASS" else "badge-flag"
            st.markdown(
                f'<span class="{badge_class}">[{item.status}]</span> **{name}**: {item.notes}',
                unsafe_allow_html=True,
            )

        if qc.fixes_applied:
            st.info("**Auto-Corrections Applied Before Delivery:**\n" + "\n".join(f"- {f}" for f in qc.fixes_applied))

    # --- TAB 4: RAW DELIVERABLE & DOWNLOAD ---
    with tab_markdown:
        st.subheader("📥 Export Deliverable")
        md_text = deliverable.to_markdown()
        json_text = deliverable.model_dump_json(indent=2)

        d_col1, d_col2 = st.columns(2)
        with d_col1:
            st.download_button(
                label="📄 Download Markdown (.md)",
                data=md_text,
                file_name=f"tamil_reel_{deliverable.input_data.duration}s.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with d_col2:
            st.download_button(
                label="💾 Download State JSON (.json)",
                data=json_text,
                file_name=f"tamil_reel_{deliverable.input_data.duration}s.json",
                mime="application/json",
                use_container_width=True,
            )

        st.code(md_text, language="markdown")

else:
    st.info("👈 Enter your topic in the sidebar and click **'🚀 Generate Reel Script'** to start.")
```

---

## 5. Step-by-Step Implementation & Run Guide

### Step 1: Install Streamlit
Add `streamlit` to your virtual environment:
```bash
pip install streamlit
```

### Step 2: Create `app.py`
Place the code above into `app.py` in your project root (`c:\Users\kumar\Desktop\Tamil-reel-script-agent\app.py`).

### Step 3: Run the Web App
Launch Streamlit from your terminal:
```bash
streamlit run app.py
```
Streamlit will automatically open your default browser at:
`http://localhost:8501`

---

## 6. Key Advantages of this Python Frontend

1. **State Persistence:** Users can swap hooks or test new CTAs with a single click without restarting the program.
2. **Interactive Word-Count Badge:** Automatically signals if the script is within the calibrated 2.2 words/second threshold.
3. **One-Click Export:** Users can download ready-to-share Markdown deliverables or machine-readable JSON files with one click.
4. **Zero Frontend Tooling:** No `npm`, `package.json`, Webpack, or Babel required—everything runs purely within Python.
