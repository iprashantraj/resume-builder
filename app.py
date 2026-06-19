"""AI Resume & Portfolio Builder — Streamlit UI.

Generates tailored resumes, cover letters, and portfolio pages from a single
student profile. Run with:  streamlit run app.py
"""

from __future__ import annotations

from typing import Callable, Optional

import streamlit as st
import streamlit.components.v1 as components

from resume_generator import GenerationError, StudentProfile, generate_resume
from cover_letter_generator import generate_cover_letter
from portfolio_generator import generate_portfolio

try:
    from pdf_export import markdown_to_pdf
except Exception:  # fpdf optional at runtime
    markdown_to_pdf = None  # type: ignore


st.set_page_config(
    page_title="AI Resume & Portfolio Builder", page_icon="📄", layout="wide"
)

# Number of free generations allowed on the app's built-in (owner) key before a
# user must supply their own Groq key.
FREE_TRIAL_LIMIT = 5


def _owner_key() -> str:
    """The app owner's key from secrets. Never displayed to the user."""
    try:
        return st.secrets.get("GROQ_API_KEY", "") or ""  # type: ignore[attr-defined]
    except Exception:
        return ""


def _render_sidebar() -> str:
    """Render settings + trial status. Returns the user's own key (if any)."""
    st.session_state.setdefault("trials_used", 0)
    trials_left = max(0, FREE_TRIAL_LIMIT - st.session_state["trials_used"])

    with st.sidebar:
        st.header("⚙️ Settings")
        user_key = st.text_input(
            "Your Groq API key (optional)",
            type="password",
            help="Get one free at console.groq.com. Used only for this session, "
            "never stored or logged.",
        ).strip()

        if user_key:
            st.success("Using your own API key — unlimited generations.")
        elif _owner_key():
            if trials_left > 0:
                st.info(f"🎁 Free trials left: **{trials_left} / {FREE_TRIAL_LIMIT}**")
            else:
                st.warning(
                    "Free trials used up. Add your own Groq API key above to "
                    "keep generating."
                )
        else:
            st.warning("Enter your Groq API key above to generate.")
        st.caption(
            "Trials are shared across resume, cover letter, and portfolio, and "
            "counted per browser session. Your key is never shown or stored."
        )
    return user_key


def _collect_profile() -> StudentProfile:
    with st.expander("📝 Your details (fill these once — used everywhere)", expanded=True):
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("Full name *", placeholder="Jane Doe")
        email = c2.text_input("Email", placeholder="jane@example.com")
        phone = c3.text_input("Phone", placeholder="+1 555 123 4567")

        c4, c5 = st.columns(2)
        location = c4.text_input("Location", placeholder="Bengaluru, India")
        target_role = c5.text_input(
            "Target role / internship", placeholder="Software Engineering Intern"
        )

        links = st.text_input(
            "Links",
            placeholder="github.com/jane  •  linkedin.com/in/jane  •  jane.dev",
        )
        summary = st.text_area(
            "Short summary about you (optional)",
            placeholder="Final-year CS student passionate about backend systems...",
            height=70,
        )

        education = st.text_area(
            "Education *",
            placeholder="B.Tech in Computer Science, XYZ University, 2022–2026, CGPA 8.7",
            height=80,
        )
        skills = st.text_area(
            "Skills",
            placeholder="Python, JavaScript, React, SQL, Git, Docker, problem-solving",
            height=70,
        )
        projects = st.text_area(
            "Projects",
            placeholder="- Expense Tracker: React + Firebase app used by 200+ students\n"
            "- ML spam classifier with 95% accuracy on 10k emails",
            height=110,
        )
        experience = st.text_area(
            "Experience (internships, part-time, volunteering)",
            placeholder="- Web Dev Intern, ABC Corp, Summer 2025: built REST APIs in Flask",
            height=90,
        )
        achievements = st.text_area(
            "Achievements / awards",
            placeholder="- Winner, University Hackathon 2025\n- Dean's list 2024",
            height=70,
        )
        job_description = st.text_area(
            "🎯 Target job description (optional — tailors resume & cover letter)",
            placeholder="We're looking for a backend intern with Python and SQL...",
            height=90,
        )

    return StudentProfile(
        name=name,
        email=email,
        phone=phone,
        location=location,
        links=links,
        target_role=target_role,
        summary=summary,
        education=education,
        skills=skills,
        projects=projects,
        experience=experience,
        achievements=achievements,
        job_description=job_description,
    )


def _generate(user_key: str, fn: Callable[[str], str], busy: str) -> Optional[str]:
    """Resolve the key (with trial gating), run fn(api_key), handle errors.

    Returns the generated text, or None if blocked/failed. Increments the trial
    counter only on success when running on the owner key.
    """
    owner_key = _owner_key()
    trials_left = max(0, FREE_TRIAL_LIMIT - st.session_state.get("trials_used", 0))

    if user_key:
        key, on_trial = user_key, False
    elif owner_key and trials_left > 0:
        key, on_trial = owner_key, True
    elif owner_key:
        st.error(
            f"You've used all {FREE_TRIAL_LIMIT} free trials. Add your own Groq "
            "API key in the sidebar to keep generating."
        )
        return None
    else:
        st.error("Add a Groq API key in the sidebar to generate.")
        return None

    with st.spinner(busy):
        try:
            result = fn(key)
        except GenerationError as exc:
            st.error(str(exc))
            return None

    if on_trial:
        st.session_state["trials_used"] = st.session_state.get("trials_used", 0) + 1
    return result


def _show_markdown_output(md: str, base_name: str, kind: str) -> None:
    """Preview + Markdown tabs and MD/PDF downloads for resume & cover letter."""
    preview_tab, md_tab = st.tabs(["Preview", "Markdown"])
    with preview_tab:
        st.markdown(md)
    with md_tab:
        st.code(md, language="markdown")

    dl1, dl2 = st.columns(2)
    dl1.download_button(
        "⬇️ Download Markdown",
        data=md,
        file_name=f"{base_name}_{kind}.md",
        mime="text/markdown",
        use_container_width=True,
    )
    if markdown_to_pdf is not None:
        try:
            pdf_bytes = markdown_to_pdf(md)
            dl2.download_button(
                "⬇️ Download PDF",
                data=pdf_bytes,
                file_name=f"{base_name}_{kind}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as exc:
            dl2.caption(f"PDF export unavailable: {exc}")


def _base_name(profile: StudentProfile) -> str:
    return (profile.name or "output").strip().replace(" ", "_").lower() or "output"


def main() -> None:
    st.title("📄 AI Resume & Portfolio Builder")
    st.write(
        "Turn your details into a tailored **resume**, **cover letter**, and "
        "**portfolio page** — generated from your own data. Powered by Groq."
    )

    user_key = _render_sidebar()
    profile = _collect_profile()
    base = _base_name(profile)

    resume_tab, cover_tab, portfolio_tab = st.tabs(
        ["📄 Resume", "✉️ Cover Letter", "🌐 Portfolio"]
    )

    # ---- Resume ----------------------------------------------------------
    with resume_tab:
        if st.button("✨ Generate resume", type="primary", use_container_width=True):
            md = _generate(
                user_key,
                lambda k: generate_resume(profile, api_key=k),
                "Writing your resume...",
            )
            if md:
                st.session_state["resume_md"] = md
        if st.session_state.get("resume_md"):
            st.divider()
            _show_markdown_output(st.session_state["resume_md"], base, "resume")

    # ---- Cover letter ----------------------------------------------------
    with cover_tab:
        c1, c2 = st.columns(2)
        company = c1.text_input("Company name", placeholder="Acme Corp")
        hiring_manager = c2.text_input(
            "Hiring manager (optional)", placeholder="Ms. Rao"
        )
        st.caption("Tip: paste the job description in 'Your details' above to tailor it.")
        if st.button(
            "✨ Generate cover letter", type="primary", use_container_width=True
        ):
            md = _generate(
                user_key,
                lambda k: generate_cover_letter(
                    profile, company=company, hiring_manager=hiring_manager, api_key=k
                ),
                "Writing your cover letter...",
            )
            if md:
                st.session_state["cover_md"] = md
        if st.session_state.get("cover_md"):
            st.divider()
            _show_markdown_output(st.session_state["cover_md"], base, "cover_letter")

    # ---- Portfolio -------------------------------------------------------
    with portfolio_tab:
        st.caption(
            "Generates a self-contained HTML page you can open in a browser or "
            "host anywhere (GitHub Pages, Netlify, etc.)."
        )
        if st.button(
            "✨ Generate portfolio", type="primary", use_container_width=True
        ):
            html_page = _generate(
                user_key,
                lambda k: generate_portfolio(profile, api_key=k),
                "Building your portfolio...",
            )
            if html_page:
                st.session_state["portfolio_html"] = html_page
        if st.session_state.get("portfolio_html"):
            st.divider()
            st.subheader("Live preview")
            components.html(
                st.session_state["portfolio_html"], height=620, scrolling=True
            )
            st.download_button(
                "⬇️ Download portfolio (HTML)",
                data=st.session_state["portfolio_html"],
                file_name=f"{base}_portfolio.html",
                mime="text/html",
                use_container_width=True,
            )


if __name__ == "__main__":
    main()
