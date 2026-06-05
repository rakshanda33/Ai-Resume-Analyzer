# app.py
import streamlit as st
from analyzer import analyze_resume, check_ats_match, rewrite_bullet
from utils import extract_text_from_pdf, score_to_emoji
from config import APP_TITLE, APP_ICON, APP_VERSION

# ── Page config ────────────────────────────────────────────────────────
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide"
)

# ── Custom CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    .score-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 24px; border-radius: 16px; text-align: center; color: white;
    }
    .score-number { font-size: 56px; font-weight: 900; line-height: 1; }
    .score-label  { font-size: 14px; opacity: 0.85; margin-top: 4px; }
    .verdict-chip {
        display: inline-block; padding: 6px 18px;
        border-radius: 20px; font-weight: 700;
        font-size: 13px; margin-top: 12px;
    }
    .section-card {
        background: #f8fafc; border-left: 4px solid #667eea;
        padding: 16px; border-radius: 8px; margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────
st.title(f"{APP_ICON} {APP_TITLE}")
st.caption(f"v{APP_VERSION} · Powered by Gemini AI · Built by Rakshanda Noor")
st.divider()

# ── Session state init ─────────────────────────────────────────────────
if "resume_text" not in st.session_state:
    st.session_state.resume_text = None
if "analysis"    not in st.session_state:
    st.session_state.analysis    = None

# ── Sidebar ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ About")
    st.markdown("""
    **AI Resume Analyzer** uses Google Gemini to give you:
    - 📊 Resume score & verdict
    - ✅ Strengths & weaknesses
    - 🎯 ATS keyword analysis
    - ✏️ Bullet point rewriter
    - 📥 Downloadable report
    """)
    st.divider()
    st.caption("Built as part of a 50-Day AI Engineering Bootcamp")

# ── File Upload ─────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "📂 Upload your Resume",
    type=["pdf"],
    help="Text-based PDFs only. Max 10 pages."
)

if uploaded_file:
    # Extract text once, store in session state
    if st.session_state.resume_text is None:
        try:
            st.session_state.resume_text = extract_text_from_pdf(uploaded_file)
            st.success(f"✅ **{uploaded_file.name}** loaded successfully")
        except ValueError as e:
            st.error(f"❌ {e}")
            st.stop()

    # ── Analyze button ──────────────────────────────────────────────
    col_btn, col_clear = st.columns([3, 1])
    with col_btn:
        analyze_clicked = st.button(
            "🔍 Analyze Resume",
            type="primary",
            use_container_width=True
        )
    with col_clear:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.resume_text = None
            st.session_state.analysis    = None
            st.rerun()

    if analyze_clicked:
        with st.spinner("🤖 Gemini is reviewing your resume..."):
            try:
                st.session_state.analysis = analyze_resume(
                    st.session_state.resume_text
                )
            except (RuntimeError, ValueError) as e:
                st.error(f"❌ {e}")
                st.stop()

    # ── Display Results ─────────────────────────────────────────────
    if st.session_state.analysis:
        r = st.session_state.analysis
        st.divider()

        # Score card + verdict
        score   = r.get("score", 0)
        verdict = r.get("verdict", "—")
        emoji   = score_to_emoji(score)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(f"""
            <div class="score-card">
                <div class="score-number">{score}</div>
                <div class="score-label">Resume Score / 100</div>
                <div class="verdict-chip">{emoji} {verdict}</div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()
        st.markdown(f"**📋 Summary:** {r.get('summary', '')}")
        st.divider()

        # Strengths / Weaknesses / Missing
        c1, c2, c3 = st.columns(3)
        with c1:
            st.subheader("✅ Strengths")
            for item in r.get("strengths", []):
                st.markdown(f"- {item}")
        with c2:
            st.subheader("⚠️ Weaknesses")
            for item in r.get("weaknesses", []):
                st.markdown(f"- {item}")
        with c3:
            st.subheader("❌ Missing")
            for item in r.get("missing_sections", []):
                st.markdown(f"- {item}")

        st.divider()

        # Improvements + ATS Issues side by side
        c4, c5 = st.columns(2)
        with c4:
            st.subheader("💡 Improvements")
            for i, tip in enumerate(r.get("improvements", []), 1):
                st.markdown(f"**{i}.** {tip}")
        with c5:
            st.subheader("🤖 ATS Issues")
            for item in r.get("ats_issues", []):
                st.markdown(f"- {item}")

        # Skills found
        if r.get("skills_found"):
            st.divider()
            st.subheader("🛠️ Skills Detected")
            st.markdown(" ".join(
                [f"`{s}`" for s in r["skills_found"]]
            ))

        # ── Download report ─────────────────────────────────────────
        st.divider()
        report = f"""# Resume Analysis Report
Score: {score}/100 | Verdict: {verdict}

## Summary
{r.get('summary', '')}

## Strengths
{chr(10).join(f'- {s}' for s in r.get('strengths', []))}

## Weaknesses
{chr(10).join(f'- {w}' for w in r.get('weaknesses', []))}

## Improvement Tips
{chr(10).join(f'{i+1}. {t}' for i, t in enumerate(r.get('improvements', [])))}

## ATS Issues
{chr(10).join(f'- {a}' for a in r.get('ats_issues', []))}

## Skills Found
{', '.join(r.get('skills_found', []))}
"""
        st.download_button(
            "📥 Download Report (.md)",
            data=report,
            file_name="resume_analysis.md",
            mime="text/markdown",
            use_container_width=True
        )

# ── Tab 2: ATS Matcher ──────────────────────────────────────────────────
st.divider()
st.subheader("🎯 ATS Keyword Matcher")
st.caption("Paste a job description to see how well your resume matches it")

if not st.session_state.resume_text:
    st.info("⬆️ Upload your resume first to use the ATS Matcher")
else:
    jd_text = st.text_area(
        "Paste Job Description",
        height=180,
        placeholder="Paste the full job description from LinkedIn, Naukri, etc."
    )
    if jd_text and st.button("🎯 Check ATS Match", type="secondary"):
        with st.spinner("Comparing resume with job description..."):
            try:
                ats = check_ats_match(st.session_state.resume_text, jd_text)
            except (RuntimeError, ValueError) as e:
                st.error(f"❌ {e}")
                st.stop()

        ats_score = ats.get("ats_score", 0)
        st.metric("ATS Match Score", f"{score_to_emoji(ats_score)} {ats_score}%")
        st.info(ats.get("match_summary", ""))
        st.markdown(f"**Recommendation:** {ats.get('recommendation', '')}")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**✅ Matched Keywords**")
            for kw in ats.get("matched_keywords", []):
                st.markdown(f"- `{kw}`")
        with col_b:
            st.markdown("**❌ Missing Keywords**")
            for kw in ats.get("missing_keywords", []):
                st.markdown(f"- `{kw}`")

# ── Tab 3: Bullet Rewriter ──────────────────────────────────────────────
st.divider()
st.subheader("✏️ Resume Bullet Rewriter")
st.caption("Paste a weak bullet point and get 3 stronger versions")

weak = st.text_input(
    "Your bullet point",
    placeholder="e.g. Worked on the company website"
)

if weak and st.button("✨ Rewrite Bullet", type="secondary"):
    with st.spinner("Writing stronger versions..."):
        try:
            rewrites = rewrite_bullet(weak)

        except (RuntimeError, ValueError) as e:
            st.error(str(e))

            with st.expander("🔧 Troubleshooting"):
                st.markdown("""
### Common Fixes

**Rate Limit Error**
- Wait 1-2 minutes
- Try again
- Use another Gemini API key

**Invalid API Key**
- Check your `.env` file
- Restart Streamlit

**PDF Error**
- Upload a text-based PDF
- Avoid scanned image PDFs
                """)

            st.stop()

    st.markdown("**3 stronger versions:**")
    for i, v in enumerate(rewrites, 1):
        st.markdown(f"**{i}.** {v}")