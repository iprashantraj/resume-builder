"""Portfolio-page generation.

The model turns the student's data into structured JSON (headline, about,
skills, projects, links); we render that into a polished, self-contained HTML
page the student can host anywhere or open straight in a browser.
"""

from __future__ import annotations

import html
import json
import re
from typing import List, Optional

from resume_generator import (
    DEFAULT_MODEL,
    GenerationError,
    StudentProfile,
    complete,
)


def _build_prompt(profile: StudentProfile) -> str:
    def section(label: str, value: str) -> str:
        value = value.strip()
        return f"{label}: {value}\n" if value else ""

    candidate = "".join(
        [
            section("Name", profile.name),
            section("Target role", profile.target_role),
            section("Location", profile.location),
            section("Links", profile.links),
            section("Summary", profile.summary),
            section("Education", profile.education),
            section("Skills", profile.skills),
            section("Projects", profile.projects),
            section("Experience", profile.experience),
            section("Achievements", profile.achievements),
        ]
    )

    return (
        "You are building the content for a student's personal portfolio website. "
        "Using ONLY the information provided (never fabricate), return STRICT JSON "
        "with exactly these keys and no others:\n"
        "{\n"
        '  "name": string,\n'
        '  "tagline": string,            // short headline, e.g. role + focus\n'
        '  "about": string,              // 2-3 sentence first-person bio\n'
        '  "skills": [string],           // individual skills/technologies\n'
        '  "projects": [                 // most impressive first\n'
        '    {"name": string, "description": string, "tech": [string]}\n'
        "  ],\n"
        '  "education": [string],        // each entry one line\n'
        '  "experience": [string],       // each entry one line, may be empty\n'
        '  "achievements": [string],     // may be empty\n'
        '  "links": [{"label": string, "url": string}]  // may be empty\n'
        "}\n\n"
        "Write polished, confident, recruiter-friendly copy. For links, infer the "
        "label (GitHub, LinkedIn, Portfolio, Email) from the value and keep the "
        "raw URL/handle in url. Output ONLY the JSON object, nothing else.\n\n"
        "STUDENT INFORMATION:\n"
        f"{candidate}"
    )


def _parse_json(raw: str) -> dict:
    """Parse the model's JSON, tolerating code fences or surrounding prose."""
    text = raw.strip()
    # Strip ```json ... ``` fences if present.
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError as exc:
                raise GenerationError(
                    f"Could not parse the portfolio content from the model: {exc}"
                ) from exc
        raise GenerationError(
            "The model did not return valid portfolio data. Try generating again."
        )


def _esc(value: str) -> str:
    return html.escape(str(value), quote=True)


def _normalize_link(url: str) -> str:
    url = url.strip()
    if url.startswith(("http://", "https://", "mailto:")):
        return url
    if "@" in url and "/" not in url:
        return f"mailto:{url}"
    return f"https://{url}"


def _render_html(data: dict) -> str:
    name = _esc(data.get("name", "Your Name"))
    tagline = _esc(data.get("tagline", ""))
    about = _esc(data.get("about", ""))

    def chip_list(items: List[str]) -> str:
        return "".join(f'<span class="chip">{_esc(s)}</span>' for s in items if s)

    def li_list(items: List[str]) -> str:
        return "".join(f"<li>{_esc(s)}</li>" for s in items if s)

    skills_html = chip_list(data.get("skills", []) or [])

    projects_html = ""
    for proj in data.get("projects", []) or []:
        if not isinstance(proj, dict):
            continue
        tech = chip_list(proj.get("tech", []) or [])
        projects_html += f"""
        <article class="card">
          <h3>{_esc(proj.get('name', ''))}</h3>
          <p>{_esc(proj.get('description', ''))}</p>
          <div class="chips">{tech}</div>
        </article>"""

    links_html = ""
    for link in data.get("links", []) or []:
        if not isinstance(link, dict) or not link.get("url"):
            continue
        href = _esc(_normalize_link(link.get("url", "")))
        label = _esc(link.get("label", "Link"))
        links_html += f'<a class="link" href="{href}" target="_blank" rel="noopener">{label}</a>'

    def section_block(title: str, body: str) -> str:
        return (
            f'<section><h2>{title}</h2>{body}</section>' if body.strip() else ""
        )

    education_html = section_block(
        "Education", f'<ul>{li_list(data.get("education", []) or [])}</ul>'
        if data.get("education") else ""
    )
    experience_html = section_block(
        "Experience", f'<ul>{li_list(data.get("experience", []) or [])}</ul>'
        if data.get("experience") else ""
    )
    achievements_html = section_block(
        "Achievements", f'<ul>{li_list(data.get("achievements", []) or [])}</ul>'
        if data.get("achievements") else ""
    )
    skills_section = section_block(
        "Skills", f'<div class="chips">{skills_html}</div>' if skills_html else ""
    )
    projects_section = section_block(
        "Projects", f'<div class="grid">{projects_html}</div>' if projects_html else ""
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name} — Portfolio</title>
<style>
  :root {{
    --bg:#0f172a; --bg2:#1e293b; --card:#ffffff; --ink:#1e293b;
    --muted:#64748b; --accent:#6366f1; --chip:#eef2ff; --chip-ink:#4338ca;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
         color:var(--ink); background:#f1f5f9; line-height:1.6; }}
  header {{ background:linear-gradient(135deg,var(--bg),var(--bg2)); color:#fff;
            padding:72px 24px 60px; text-align:center; }}
  header h1 {{ margin:0; font-size:2.6rem; letter-spacing:-0.02em; }}
  header .tagline {{ margin:10px 0 22px; font-size:1.15rem; color:#cbd5e1; }}
  .links {{ display:flex; gap:12px; justify-content:center; flex-wrap:wrap; }}
  .link {{ color:#fff; text-decoration:none; border:1px solid rgba(255,255,255,.35);
           padding:8px 16px; border-radius:999px; font-size:.9rem; transition:.2s; }}
  .link:hover {{ background:rgba(255,255,255,.15); }}
  main {{ max-width:860px; margin:-32px auto 60px; padding:0 24px; }}
  section {{ background:var(--card); border-radius:16px; padding:28px 32px; margin-bottom:22px;
             box-shadow:0 10px 30px rgba(15,23,42,.06); }}
  section h2 {{ margin:0 0 16px; font-size:1.15rem; text-transform:uppercase;
                letter-spacing:.08em; color:var(--accent); }}
  section p {{ margin:0; color:var(--ink); }}
  ul {{ margin:0; padding-left:20px; }}
  li {{ margin-bottom:6px; }}
  .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
  .card {{ border:1px solid #e2e8f0; border-radius:12px; padding:18px; }}
  .card h3 {{ margin:0 0 8px; font-size:1.05rem; }}
  .card p {{ color:var(--muted); font-size:.95rem; }}
  .chips {{ display:flex; gap:8px; flex-wrap:wrap; margin-top:12px; }}
  .chip {{ background:var(--chip); color:var(--chip-ink); padding:5px 12px;
           border-radius:999px; font-size:.82rem; font-weight:600; }}
  footer {{ text-align:center; color:var(--muted); padding:24px; font-size:.85rem; }}
  @media (max-width:640px) {{ .grid {{ grid-template-columns:1fr; }} header h1 {{ font-size:2rem; }} }}
</style>
</head>
<body>
  <header>
    <h1>{name}</h1>
    <div class="tagline">{tagline}</div>
    <div class="links">{links_html}</div>
  </header>
  <main>
    {section_block("About", f'<p>{about}</p>' if about else "")}
    {skills_section}
    {projects_section}
    {experience_html}
    {education_html}
    {achievements_html}
  </main>
  <footer>Built with AI Resume &amp; Portfolio Builder</footer>
</body>
</html>"""


def generate_portfolio(
    profile: StudentProfile,
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
) -> str:
    """Generate a self-contained HTML portfolio page. Raises GenerationError."""
    if not profile.is_minimally_complete():
        raise GenerationError(
            "Please provide at least your name plus some education, skills, or "
            "projects before generating."
        )

    raw = complete(
        system="You output only strict, valid JSON for a portfolio website.",
        user=_build_prompt(profile),
        api_key=api_key,
        model=model,
        temperature=0.5,
        max_tokens=2000,
    )
    data = _parse_json(raw)
    if not isinstance(data, dict):
        raise GenerationError("Unexpected portfolio data format from the model.")
    # Ensure the name is always present even if the model omitted it.
    data.setdefault("name", profile.name)
    return _render_html(data)
