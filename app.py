"""Streamlit Web UI for Tamil Reel Script Agent (VG Digital Falcon).

Provides an interactive dashboard for generating, fine-tuning, and exporting
research-backed Tamil & Tanglish short-form video scripts.
"""

import sys
import io
from pathlib import Path
import streamlit as st

from src.utils import setup_utf8_console

setup_utf8_console()

from src.models import ScriptInput, FullDeliverable
from src.pipeline import TamilReelScriptPipeline
from src.config import WORD_COUNT_LIMITS, DELIVERABLES_DIR

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Tamil Reel Script Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CUSTOM CSS FOR MODERN AESTHETICS ---
st.markdown(
    """
    <style>
    /* Main Layout Styling */
    .main-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #1E293B 0%, #3B82F6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    
    /* Status Badges */
    .badge-pass {
        background-color: #DCFCE7;
        color: #15803D;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
        margin-right: 6px;
    }
    .badge-flag {
        background-color: #FEE2E2;
        color: #B91C1C;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
        margin-right: 6px;
    }
    
    /* Content Blocks */
    .script-block {
        background: #F8FAFC;
        border-left: 4px solid #3B82F6;
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin-bottom: 12px;
        font-size: 1.02rem;
        line-height: 1.6;
    }
    .source-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px 14px;
        margin-bottom: 10px;
    }
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
    '<div class="subtitle">Research-backed, duration-calibrated Tamil & Tanglish short-form video scripts (VG Digital Falcon)</div>',
    unsafe_allow_html=True,
)

# --- PRESET SAMPLES ---
PRESETS = {
    "Select a preset topic (Optional)...": None,
    "Topic 1: Why websites fail to get leads (30s, Tanglish)": {
        "topic": "Why are businesses not getting leads from their websites?",
        "duration": 30,
        "tone": "Tanglish",
        "objective": "Get agency leads",
        "audience": "Small business owners",
        "niche": "Digital Marketing / Web Development",
    },
    "Topic 2: SEO mistakes & ranking myths (45s, Tanglish)": {
        "topic": "Common SEO mistakes and ranking myths for small businesses",
        "duration": 45,
        "tone": "Tanglish",
        "objective": "awareness",
        "audience": "Local business owners and Tamil entrepreneurs",
        "niche": "Search Engine Optimization",
    },
    "Topic 3: Germany Opportunity Card (60s, Spoken Tamil)": {
        "topic": "Germany Opportunity Card (Chancenkarte) and job seeker visa requirements",
        "duration": 60,
        "tone": "conversational spoken Tamil",
        "objective": "awareness",
        "audience": "Tamil graduates and tech professionals looking to work in Germany",
        "niche": "Abroad Careers & Immigration",
    },
}

# --- SIDEBAR: PARAMETERS ---
with st.sidebar:
    st.header("⚙️ Script Generator")

    chosen_preset = st.selectbox("Quick Presets", options=list(PRESETS.keys()), index=0)

    if chosen_preset and PRESETS[chosen_preset]:
        preset_data = PRESETS[chosen_preset]
        default_topic = preset_data["topic"]
        default_duration = preset_data["duration"]
        default_tone = preset_data["tone"]
        default_objective = preset_data["objective"]
        default_audience = preset_data["audience"]
        default_niche = preset_data["niche"]
    else:
        default_topic = "Why are businesses not getting leads from their websites?"
        default_duration = 30
        default_tone = "Tanglish"
        default_objective = "Get agency leads"
        default_audience = "Small business owners"
        default_niche = "Digital Marketing / Web"

    topic = st.text_area(
        "Primary Video Topic *",
        value=default_topic,
        placeholder="Enter your topic in English, Tamil, or Tanglish...",
        height=90,
    )

    platform = st.selectbox(
        "Platform",
        options=["Instagram Reels", "YouTube Shorts", "Facebook Reels"],
        index=0,
    )

    duration = st.select_slider(
        "Target Duration (seconds)",
        options=[30, 45, 60],
        value=default_duration,
        help="Calibrated to natural spoken Tamil/Tanglish pacing (~2.2 words/second).",
    )

    limits = WORD_COUNT_LIMITS.get(duration, {"min": 60, "max": 75})
    st.caption(f"⏱️ Spoken target window: **{limits['min']} – {limits['max']} words**")

    tone_options = ["Tanglish", "conversational spoken Tamil", "Tamil"]
    tone_index = tone_options.index(default_tone) if default_tone in tone_options else 0
    tone = st.radio(
        "Script Language & Tone",
        options=tone_options,
        index=tone_index,
        help="Tanglish: Spoken Tamil written in English letters. Conversational Tamil: Natural spoken Tamil script.",
    )

    objective = st.text_input(
        "Marketing Objective",
        value=default_objective,
        placeholder="e.g., Get agency leads, awareness, book consultation",
    )

    with st.expander("Target Persona & Niche (Optional)"):
        audience = st.text_input("Target Audience", value=default_audience)
        niche = st.text_input("Niche / Category", value=default_niche)

    generate_btn = st.button("🚀 Generate Reel Script", type="primary", use_container_width=True)

# --- ACTION: GENERATION ---
if generate_btn:
    if not topic.strip():
        st.error("Please provide a valid topic to proceed.")
    else:
        with st.status("Executing 3-Step Agent Pipeline...", expanded=True) as status:
            st.write("🔍 **Step 1/3:** Running live DuckDuckGo searches & extracting verified facts...")
            inp = ScriptInput.create_with_defaults(
                topic=topic.strip(),
                audience=audience.strip() if audience else None,
                niche=niche.strip() if niche else None,
                platform=platform,
                duration=duration,
                tone=tone,
                objective=objective.strip(),
                mode="full_script",
            )
            st.write("✍️ **Step 2/3:** Formulating 3 hook options and duration-calibrated script...")
            st.write("🛡️ **Step 3/3:** Running 5-point quality audit & self-correction check...")
            try:
                deliverable_result = pipeline.run(inp)
                st.session_state.deliverable = deliverable_result
                status.update(label="✅ Reel script generated and certified!", state="complete", expanded=False)
            except Exception as e:
                status.update(label=f"❌ Error during generation: {e}", state="error")
                st.error(f"Generation error: {e}")

# --- DISPLAY OUTPUT ---
deliverable: FullDeliverable = st.session_state.deliverable

if deliverable:
    actual_words = deliverable.script.word_count
    limits = WORD_COUNT_LIMITS.get(deliverable.input_data.duration, {"min": 60, "max": 75})
    is_duration_ok = limits["min"] <= actual_words <= limits["max"]

    # Top Overview Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Topic", deliverable.input_data.topic[:28] + ("..." if len(deliverable.input_data.topic) > 28 else ""))
    m2.metric("Duration", f"{deliverable.input_data.duration}s")
    m3.metric(
        "Spoken Words",
        f"{actual_words}w",
        delta=f"Range: {limits['min']}-{limits['max']}w",
        delta_color="normal" if is_duration_ok else "inverse",
    )
    m4.metric("Tone", deliverable.input_data.tone)

    # Main Tabs
    tab_script, tab_research, tab_qc, tab_export = st.tabs(
        ["🎬 Script & Hooks", "🔍 Research & Sources", "🛡️ Quality Audit", "📥 Raw & Export"]
    )

    # --- TAB 1: SCRIPT & HOOKS ---
    with tab_script:
        st.subheader("🎣 3 Hook Options (Curiosity & Pattern Interrupt)")
        h_cols = st.columns(3)
        for idx, h in enumerate(deliverable.script.hooks):
            with h_cols[idx]:
                badge = "⭐ **[RECOMMENDED]**" if h.is_recommended else ""
                st.markdown(f"**Hook {idx+1} ({h.type.title()})** {badge}")
                st.info(f"\"{h.text}\"")
                if h.reason:
                    st.caption(f"💡 *Why:* {h.reason}")

        # Hook Regeneration Button
        c_h1, c_h2 = st.columns([1, 3])
        with c_h1:
            if st.button("⚡ Regenerate 3 Fresh Hooks", use_container_width=True):
                with st.spinner("Generating 3 new hooks..."):
                    updated_inp = deliverable.input_data.model_copy(deep=True)
                    updated_inp.mode = "regenerate_hook"
                    st.session_state.deliverable = pipeline.run(updated_inp, previous_deliverable=deliverable)
                    st.rerun()
        with c_h2:
            st.caption("Re-generates fresh hooks instantly while preserving the body and verified research.")

        st.divider()

        st.subheader("📜 Spoken Script Breakdown")
        st.markdown(
            f"*(Duration: **{deliverable.input_data.duration}s** | Word Count: **{actual_words} words** | Target: **{limits['min']}–{limits['max']} words**)*"
        )

        st.markdown(f"**[Hook]**\n<div class='script-block'>{deliverable.script.hook}</div>", unsafe_allow_html=True)
        st.markdown(f"**[Context]**\n<div class='script-block'>{deliverable.script.context}</div>", unsafe_allow_html=True)

        st.markdown("**[Body Points]**")
        for pt in deliverable.script.body_points:
            st.markdown(f"<div class='script-block'>• {pt}</div>", unsafe_allow_html=True)

        st.markdown(f"**[Engagement Question]**\n<div class='script-block'>{deliverable.script.engagement}</div>", unsafe_allow_html=True)
        st.markdown(f"**[Call To Action (CTA)]**\n<div class='script-block'><strong>{deliverable.script.cta}</strong></div>", unsafe_allow_html=True)

        # CTA Regeneration
        st.divider()
        st.subheader("🎯 Regenerate Call To Action (CTA)")
        cta_col1, cta_col2 = st.columns([2, 1])
        with cta_col1:
            new_cta_obj = st.text_input(
                "Customize Objective for New CTA (Optional):",
                value=deliverable.input_data.objective,
                key="new_cta_obj_input",
            )
        with cta_col2:
            st.write("")
            st.write("")
            if st.button("🎯 Regenerate CTA Options", use_container_width=True):
                with st.spinner("Regenerating CTA matching objective..."):
                    updated_inp = deliverable.input_data.model_copy(deep=True)
                    if new_cta_obj.strip():
                        updated_inp.objective = new_cta_obj.strip()
                    updated_inp.mode = "regenerate_cta"
                    st.session_state.deliverable = pipeline.run(updated_inp, previous_deliverable=deliverable)
                    st.rerun()

        st.divider()
        st.subheader("🎥 Production Notes")
        p1, p2 = st.columns(2)
        with p1:
            st.markdown("**On-Screen Text Overlays:**")
            for ost in deliverable.script.on_screen_texts:
                st.markdown(f"• `{ost}`")
        with p2:
            st.markdown("**Caption & Suggested Hashtags:**")
            st.caption(f"> {deliverable.script.caption}")
            st.code(" ".join(deliverable.script.hashtags))

    # --- TAB 2: RESEARCH & SOURCES ---
    with tab_research:
        st.subheader("💡 Key Research Findings")
        for finding in deliverable.research.key_findings:
            st.markdown(f"- {finding}")

        st.markdown(f"**Chosen Content Angle:** {deliverable.research.chosen_angle}")
        st.caption(f"Reason: {deliverable.research.angle_reason}")

        st.divider()
        st.subheader("⚠️ Audience Pain Points Identified")
        for pp in deliverable.research.pain_points:
            st.markdown(f"- 🔸 {pp}")

        st.divider()
        st.subheader("🔗 Verified Web Citations (Zero Hallucination)")
        if deliverable.research.sources:
            for s in deliverable.research.sources:
                v_badge = "✅ Verified" if s.is_verified else "⚠️ Unverified"
                st.markdown(
                    f"""
                    <div class="source-card">
                        <strong><a href="{s.url}" target="_blank">{s.title or s.url}</a></strong> &nbsp;<small>({v_badge})</small><br>
                        <em>Supports Claim:</em> {s.claim_supported}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No external web links logged.")

        if deliverable.research.uncertainties:
            st.warning("**⚠️ Official Verification Alert:**\n" + "\n".join(f"- {u}" for u in deliverable.research.uncertainties))

    # --- TAB 3: QUALITY AUDIT ---
    with tab_qc:
        st.subheader("🛡️ 5-Point Quality Compliance Report")
        qc = deliverable.quality_check

        audit_criteria = [
            ("1. Unsupported Claims", qc.unsupported_claims),
            ("2. Repetition", qc.repetition),
            ("3. Weak Call-to-Action", qc.weak_cta),
            ("4. Natural Spoken Tamil", qc.unnatural_tamil),
            ("5. Duration Fit Calibration", qc.duration_fit),
        ]

        for name, item in audit_criteria:
            b_class = "badge-pass" if item.status == "PASS" else "badge-flag"
            st.markdown(
                f'<span class="{b_class}">[{item.status}]</span> <strong>{name}</strong>: {item.notes}',
                unsafe_allow_html=True,
            )
            st.write("")

        if qc.fixes_applied:
            st.info("**🛠️ Automatic Corrections Applied Before Delivery:**\n" + "\n".join(f"- {f}" for f in qc.fixes_applied))
        else:
            st.success("🌟 All 5 quality criteria passed on first audit with zero defects!")

    # --- TAB 4: RAW DELIVERABLE & EXPORT ---
    with tab_export:
        st.subheader("📥 Export Deliverable Files")
        md_text = deliverable.to_markdown()
        json_text = deliverable.model_dump_json(indent=2)

        exp_c1, exp_c2 = st.columns(2)
        with exp_c1:
            st.download_button(
                label="📄 Download Markdown (.md)",
                data=md_text,
                file_name=f"tamil_reel_{deliverable.input_data.duration}s.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with exp_c2:
            st.download_button(
                label="💾 Download State JSON (.json)",
                data=json_text,
                file_name=f"tamil_reel_{deliverable.input_data.duration}s.json",
                mime="application/json",
                use_container_width=True,
            )

        st.subheader("📄 Raw Markdown Preview")
        st.code(md_text, language="markdown")

else:
    st.info("👈 Enter your topic in the sidebar and click **'🚀 Generate Reel Script'** to start creating!")
