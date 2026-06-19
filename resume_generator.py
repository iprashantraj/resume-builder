"""Resume generation logic backed by the Groq API.

Keeps all LLM / prompt concerns out of the Streamlit UI layer so they can be
tested and swapped independently.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

try:
    from groq import Groq
except ImportError:  # pragma: no cover - surfaced to the user in the UI
    Groq = None  # type: ignore


# A fast, high-quality general model available on Groq. Override with the
# GROQ_MODEL env var if you want to experiment with others.
DEFAULT_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")


@dataclass
class StudentProfile:
    """Everything we collect from the student to build a resume."""

    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    links: str = ""  # e.g. GitHub, LinkedIn, portfolio (free text / newlines)
    target_role: str = ""  # role/internship they're aiming for
    summary: str = ""  # optional self-description
    education: str = ""
    skills: str = ""
    projects: str = ""
    experience: str = ""
    achievements: str = ""
    job_description: str = ""  # optional: tailor the resume to this posting

    def is_minimally_complete(self) -> bool:
        """Enough signal to write something useful."""
        return bool(self.name.strip()) and bool(
            self.education.strip() or self.skills.strip() or self.projects.strip()
        )


class GenerationError(Exception):
    """Raised when resume generation fails for a reason worth showing the user."""


def complete(
    system: str,
    user: str,
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.6,
    max_tokens: int = 2000,
) -> str:
    """Shared Groq chat-completion helper used by every generator.

    Raises GenerationError with a user-friendly message on any failure.
    """
    if Groq is None:
        raise GenerationError(
            "The 'groq' package isn't installed. Run: pip install -r requirements.txt"
        )

    key = api_key or os.environ.get("GROQ_API_KEY")
    if not key:
        raise GenerationError(
            "No Groq API key found. Add it in the sidebar or set the "
            "GROQ_API_KEY environment variable."
        )

    client = Groq(api_key=key)
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as exc:  # groq raises a variety of error types
        # Never echo the key; keep this generic on purpose.
        raise GenerationError(f"Groq API call failed: {exc}") from exc

    content = (completion.choices[0].message.content or "").strip()
    if not content:
        raise GenerationError("The model returned an empty response. Try again.")
    return content


def _build_prompt(profile: StudentProfile) -> str:
    """Turn the structured profile into a single instruction block."""

    def section(label: str, value: str) -> str:
        value = value.strip()
        return f"{label}:\n{value}\n" if value else ""

    tailoring = ""
    if profile.job_description.strip():
        tailoring = (
            "\nTAILORING TARGET — tailor wording, ordering, and emphasis of the "
            "resume to this specific job description. Mirror its key terminology "
            "where the candidate genuinely matches it; never invent experience:\n"
            f"{profile.job_description.strip()}\n"
        )

    fields = "".join(
        [
            section("Full name", profile.name),
            section("Email", profile.email),
            section("Phone", profile.phone),
            section("Location", profile.location),
            section("Links", profile.links),
            section("Target role", profile.target_role),
            section("Self summary", profile.summary),
            section("Education", profile.education),
            section("Skills", profile.skills),
            section("Projects", profile.projects),
            section("Experience", profile.experience),
            section("Achievements / awards", profile.achievements),
        ]
    )

    return (
        "You are an expert career coach and professional resume writer who helps "
        "students land internships and entry-level jobs.\n\n"
        "Write a polished, ATS-friendly resume in clean Markdown using ONLY the "
        "candidate information provided. Rules:\n"
        "- Do NOT fabricate employers, dates, metrics, or credentials. If a "
        "detail is missing, simply omit it.\n"
        "- Lead bullet points with strong action verbs and quantify impact when "
        "the candidate provided numbers.\n"
        "- Use standard sections (Contact, Summary, Education, Skills, Projects, "
        "Experience, Achievements) and drop any section with no content.\n"
        "- Keep it concise — one page of content for a student.\n"
        "- Output ONLY the resume in Markdown. No preamble, no commentary.\n"
        f"{tailoring}\n"
        "CANDIDATE INFORMATION:\n"
        f"{fields}"
    )


def generate_resume(
    profile: StudentProfile,
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
) -> str:
    """Generate a Markdown resume from a student profile via Groq.

    Raises GenerationError with a user-friendly message on any failure.
    """
    if not profile.is_minimally_complete():
        raise GenerationError(
            "Please provide at least your name plus some education, skills, or "
            "projects before generating."
        )

    return complete(
        system="You write concise, truthful, ATS-friendly resumes.",
        user=_build_prompt(profile),
        api_key=api_key,
        model=model,
        temperature=0.6,
        max_tokens=2000,
    )
