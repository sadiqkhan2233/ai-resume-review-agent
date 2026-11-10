# 📄 AI Resume Review Agent

A beginner-friendly **single-agent** AI app that reviews resumes, gives an **estimated ATS-style score**,
matches the resume to a job description, and suggests concrete improvements.

> ⚠️ The score is an AI-generated estimate. It is **not** an official score from any real ATS.

## Tech stack
Python • CrewAI (one agent) • Groq (`openai/gpt-oss-20b`) via LiteLLM • Streamlit • PyMuPDF • python-docx • Pydantic • ReportLab • python-dotenv

## Features
- Upload PDF / DOCX (type, size and corruption checks; nothing is stored on disk)
- Optional job title + job description → explainable job-match score
- Scoring out of 100: Skills 20, Experience 20, Education 15, ATS formatting 15, Summary 10, Achievements 10, Grammar 10
- Strengths, weaknesses, missing info, skill gaps, certification ideas, bullet rewrites, improved summary, action plan
- Downloadable PDF report (and raw JSON)

## Project structure
```
ai-resume-review-agent/
├── app.py                  # Streamlit UI
├── requirements.txt
├── .env.example            # copy to .env locally
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
└── resume_agent/
    ├── config.py           # settings & scoring rubric
    ├── extractors.py       # PDF / DOCX text extraction + validation
    ├── schemas.py          # Pydantic models
    ├── scoring.py          # totals, grade, job-match formula
    ├── agent.py            # the ONE CrewAI agent + task
    └── report.py           # PDF report (ReportLab)
```

## Run locally
```bash
git clone https://github.com/<your-username>/ai-resume-review-agent.git
cd ai-resume-review-agent
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # Windows: copy .env.example .env
# edit .env and paste your free Groq key from https://console.groq.com/keys
streamlit run app.py
```
Use Python 3.10 – 3.13.

## Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit: AI Resume Review Agent"
git branch -M main
git remote add origin https://github.com/<your-username>/ai-resume-review-agent.git
git push -u origin main
```
`.env` is in `.gitignore`, so your API key will not be uploaded.

## Deploy free on Streamlit Community Cloud
1. Go to https://share.streamlit.io and sign in with GitHub.
2. Click **Create app** → choose your repo, branch `main`, main file `app.py`.
3. Open **Advanced settings → Secrets** and paste:
   ```toml
   GROQ_API_KEY = "your_groq_api_key_here"
   ```
4. Click **Deploy**.

(Alternatively, leave the secret empty and let each visitor paste their own free Groq key in the sidebar.)

## Architecture (single agent)
`Streamlit UI → extract text → one CrewAI Agent ("Professional Resume Reviewer") → one Task → Pydantic validation → Python scoring → UI + PDF`.
Delegation is off, memory is off, and `max_iter` is 4. Totals and the job-match score are calculated in Python so they are always consistent and explainable.

## Troubleshooting
| Problem | Fix |
|---|---|
| `401` / invalid key | Re-copy the key from the Groq console |
| `429` / rate limit | Free tier limit - wait a minute, shorten the resume, or switch model in the sidebar |
| Model not found | Check https://console.groq.com/docs/models and change the model name in the sidebar or `GROQ_MODEL` |
| "Very little text could be read" | Your PDF is a scanned image. Export a text-based PDF or use DOCX |
| `sqlite3` version error on Streamlit Cloud | Add `pysqlite3-binary` to `requirements.txt` and put `__import__("pysqlite3"); import sys; sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")` at the very top of `app.py` |
| Dependency conflicts | After a successful local run, run `pip freeze` and pin the working versions |

## License
MIT - free to use and modify.
