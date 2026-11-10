"""Central configuration. Change values here instead of hunting through the code."""
import os

from dotenv import load_dotenv

load_dotenv()

APP_NAME = "AI Resume Review Agent"

# --- LLM ---------------------------------------------------------------
# Verified as an available Groq model. Override with GROQ_MODEL in .env if needed.
DEFAULT_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
LLM_TEMPERATURE = 0.2
LLM_MAX_TOKENS = 6000
AGENT_MAX_ITER = 4  # allowed range 3-5

# --- Upload limits -----------------------------------------------------
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE_MB = 5
MAX_FILE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_PDF_PAGES = 10
MIN_RESUME_CHARS = 150

# Free-tier friendly input limits (characters sent to the model)
MAX_RESUME_CHARS = 12000
MAX_JD_CHARS = 5000

# --- Scoring rubric (must total 100) ----------------------------------
# key -> (display label, max points)
SCORE_RUBRIC = {
    "skills_relevance": ("Skills relevance", 20),
    "work_experience": ("Work experience", 20),
    "education": ("Education", 15),
    "ats_formatting": ("ATS formatting", 15),
    "professional_summary": ("Professional summary", 10),
    "achievements": ("Achievements", 10),
    "grammar_clarity": ("Grammar and clarity", 10),
}
assert sum(v[1] for v in SCORE_RUBRIC.values()) == 100

DISCLAIMER = (
    "This is an AI-generated, estimated ATS-style evaluation. It is NOT an official "
    "score from any real Applicant Tracking System (ATS) and does not guarantee "
    "interview or hiring outcomes. Use it as guidance only."
)
