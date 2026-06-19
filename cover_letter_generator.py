"""Cover-letter generation, built on the shared Groq plumbing."""

from __future__ import annotations

from typing import Optional

from resume_generator import (
    DEFAULT_MODEL,
    GenerationError,
    StudentProfile,
    complete,
)


def _build_prompt(profile: StudentProfile, company: str, hiring_manager: str) -> str:
    def section(label: str, value: str) -> str:
        value = value.strip()
        return f"{label}: {value}\n" if value else ""

    greeting_hint = (
        f"Address it to {hiring_manager.strip()}."
        if hiring_manager.strip()
        else "Use a professional greeting (e.g. 'Dear Hiring Manager,') since no "
        "specific recipient was given."
    )

    job_block = ""
    if profile.job_description.strip():
        job_block = (
            "\nJOB DESCRIPTION — align the letter to the most relevant "
            "requirements here, mirroring key terminology where the candidate "
            "genuinely matches it:\n"
            f"{profile.job_description.strip()}\n"
        )

    candidate = "".join(
        [
            section("Name", profile.name),
            section("Target role", profile.target_role),
            section("Location", profile.location),
            section("Summary", profile.summary),
            section("Education", profile.education),
            section("Skills", profile.skills),
            section("Projects", profile.projects),
            section("Experience", profile.experience),
            section("Achievements", profile.achievements),
        ]
    )

    return (
        "You are an expert career coach writing a compelling, professional cover "
        "letter for a student applying to an internship or entry-level role.\n\n"
        "Write the cover letter in clean Markdown. Rules:\n"
        f"- Company the candidate is applying to: {company.strip() or 'the company'}.\n"
        f"- {greeting_hint}\n"
        "- 3–4 short paragraphs: a strong opening hook, 1–2 body paragraphs that "
        "connect the candidate's REAL projects/skills to the role's needs, and a "
        "confident closing with a call to action.\n"
        "- Be specific and authentic; do NOT fabricate experience, metrics, or "
        "credentials. Use only the information provided.\n"
        "- Keep it under ~350 words. Warm and professional, not robotic.\n"
        "- End with 'Sincerely,' followed by the candidate's name.\n"
        "- Output ONLY the letter in Markdown. No preamble, no commentary.\n"
        f"{job_block}\n"
        "CANDIDATE INFORMATION:\n"
        f"{candidate}"
    )


def generate_cover_letter(
    profile: StudentProfile,
    company: str = "",
    hiring_manager: str = "",
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
) -> str:
    """Generate a Markdown cover letter. Raises GenerationError on failure."""
    if not profile.name.strip():
        raise GenerationError("Please enter at least your name before generating.")
    if not (
        profile.skills.strip()
        or profile.projects.strip()
        or profile.experience.strip()
    ):
        raise GenerationError(
            "Add some skills, projects, or experience so the letter has something "
            "to highlight."
        )

    return complete(
        system="You write warm, specific, truthful cover letters for students.",
        user=_build_prompt(profile, company, hiring_manager),
        api_key=api_key,
        model=model,
        temperature=0.7,
        max_tokens=1200,
    )
