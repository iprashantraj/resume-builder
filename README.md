# 📄 AI Resume & Portfolio Builder

Many students struggle to present their skills and projects in an attractive,
professional format. Generic resume templates don't highlight individual
strengths. This **generative AI solution** automatically creates tailored
**resumes**, **cover letters**, and **portfolio pages** from a student's own
data — improving their job and internship opportunities.

> Fill one form, get three polished outputs — each one uniquely generated from
> your real skills, projects, and experience. No fabrication, no cookie-cutter
> templates.

## 🔗 Demo

🚀 **[Live Demo](https://iprashantraj-resume-builder.streamlit.app/)** — try it now, no setup needed

**Local preview:**

```bash
streamlit run app.py
# → opens at http://localhost:8501
```

## 🖼️ Screenshots

| Resume | Cover Letter | Portfolio |
|--------|-------------|-----------|
| ATS-friendly, one-page PDF with proper fonts | Tailored to a specific company and role | Responsive HTML page with hero, skill chips, and project cards |

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend / UI** | [Streamlit](https://streamlit.io/) — interactive web app with forms, tabs, live preview |
| **AI / LLM** | [Groq](https://groq.com/) — ultra-fast inference on **LLaMA 3.3 70B Versatile** |
| **PDF generation** | [fpdf2](https://py-pdf.github.io/fpdf2/) — embedded TrueType fonts (Arial + Georgia) for professional typography |
| **Portfolio rendering** | Pure HTML/CSS — self-contained, responsive, hostable anywhere |
| **Language** | Python 3.9+ |

## ✨ Features

- **📄 Resume** — AI-generated, one-page, ATS-friendly, optionally tailored to a
  pasted job description. Download as Markdown or styled PDF (Georgia + Arial fonts).
- **✉️ Cover letter** — warm, specific letter tailored to a company / role / job
  description. Download as Markdown or PDF.
- **🌐 Portfolio** — a self-contained, responsive HTML page (gradient hero, skill
  chips, project cards) the student can host anywhere or open in a browser.
- **🎯 Job-description tailoring** — paste a job posting and the resume and cover
  letter mirror its key terminology where the candidate genuinely matches.
- **🎁 5 free generations** (shared across all three) on the app's built-in key;
  after that, visitors use their own Groq key.
- **🔒 API key security** — the owner key is gitignored, never displayed or logged;
  visitor keys are masked and used only in-memory for the session.
- **🚫 No fabrication** — the model is explicitly instructed to never invent
  employers, dates, metrics, or credentials.

## 🚀 Setup

```bash
# 1. Clone the repo
git clone https://github.com/iprashantraj/resume-builder.git
cd resume-builder

# 2. Create a virtual environment (recommended on macOS)
python3 -m venv .venv && source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your Groq API key (get one free at https://console.groq.com/keys)
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Then edit .streamlit/secrets.toml and paste your key

# 5. Run
streamlit run app.py
```

## ☁️ Deploy to Streamlit Cloud

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo.
3. Set `GROQ_API_KEY` in **Secrets** (Settings → Secrets → paste
   `GROQ_API_KEY = "gsk_..."` in TOML format).
4. Deploy — your live URL will look like `https://<your-app>.streamlit.app`.

## ⚙️ Configuration

| Setting          | How to set it                                  | Default                   |
| ---------------- | ---------------------------------------------- | ------------------------- |
| `GROQ_API_KEY`   | `.streamlit/secrets.toml`, env var, or sidebar | — (required)              |
| `GROQ_MODEL`     | environment variable                           | `llama-3.3-70b-versatile` |
| Free trial count | `FREE_TRIAL_LIMIT` in `app.py`                 | `5`                       |

## 📁 Project Structure

```
app.py                     # Streamlit UI (Resume / Cover Letter / Portfolio tabs)
resume_generator.py        # StudentProfile model, shared Groq helper, resume prompt
cover_letter_generator.py  # Cover-letter prompt + generation
portfolio_generator.py     # Portfolio JSON prompt + HTML rendering
pdf_export.py              # Markdown → styled PDF (embedded Arial/Georgia fonts)
requirements.txt           # Python dependencies
.streamlit/
  secrets.toml.example     # Template — copy to secrets.toml and add your key
  secrets.toml             # Your real key (gitignored, never committed)
.gitignore
```

## 📌 Note on the free-trial limit

Trials are counted in Streamlit **session state** (per browser session). A
visitor who clears state can reset their count — that's fine for an MVP/demo.
For a hard limit you'd back the counter with persistent per-user storage.

## 🗺️ Roadmap

- [ ] Multiple resume templates / themes
- [ ] One-click portfolio hosting (GitHub Pages)
- [ ] Save / load profiles across sessions
- [ ] LinkedIn PDF import to pre-fill the form

## 📄 License

MIT
