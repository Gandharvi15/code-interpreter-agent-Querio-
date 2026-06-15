import os
import pandas as pd
from dotenv import load_dotenv
from langchain_experimental.tools import PythonREPLTool
from safety import is_safe
from eda_engine import is_eda_question, run_eda
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ── Safe code executor ───────────────────────────────────────────
def run_code(code: str) -> str:
    """Safety-check then execute Python code, return stdout."""
    safe, reason = is_safe(code)
    if not safe:
        return f"⛔ Blocked: {reason}"
    try:
        tool = PythonREPLTool()
        output = tool.run(code)
        return str(output).strip() if output else "Done."
    except Exception as e:
        return f"⚠ Execution error: {e}"


# ── Ask Groq to write pandas code ───────────────────────────────
def generate_code(question: str, column_info: str) -> str:
    """
    Single LLM call — returns only executable Python code, no explanation.
    Uses llama-3.3-70b-versatile for best tool-use reliability.
    """
    system = """You are a Python data analyst. 
When given a question and column info, respond with ONLY executable Python code.
No explanation, no markdown fences, no comments — just raw Python.
Rules:
- Always start with: import pandas as pd
- Always read data with: df = pd.read_csv('temp_data.csv')
- Always end with a print() that shows the answer clearly
- Keep code short and direct"""

    prompt = f"""Columns: {column_info}

Question: {question}

Write Python + pandas code to answer this. Raw code only."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",   # fast + reliable tool use
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
        temperature=0,
        max_tokens=400,
    )

    code = response.choices[0].message.content.strip()

    # Strip markdown fences if model adds them despite instructions
    if code.startswith("```"):
        lines = code.splitlines()
        code = "\n".join(
            l for l in lines
            if not l.strip().startswith("```")
        ).strip()

    return code


# ── Format raw output into a clean answer ───────────────────────
def format_answer(raw_output: str, question: str) -> str:
    """One quick LLM call to make the printed output readable."""
    if not raw_output or raw_output.startswith("⛔") or raw_output.startswith("⚠"):
        return raw_output

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",   # cheap model fine for formatting
            messages=[
                {"role": "system", "content": "You are a concise data analyst. Format the raw output as a clean, readable answer in 1-4 sentences or a short list. No code, no preamble."},
                {"role": "user",   "content": f"Question: {question}\nRaw output:\n{raw_output}"},
            ],
            temperature=0,
            max_tokens=200,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return raw_output  # fallback to raw if formatting fails


# ── Generate smart example questions from df ────────────────────
def generate_examples(df: pd.DataFrame) -> list[str]:
    """
    Looks at the actual columns + dtypes + sample values and asks
    the LLM for 4 relevant example questions (2 text, 2 chart).
    Falls back to generic questions if the call fails.
    """
    try:
        column_info = ", ".join(
            f"{col} ({str(dtype).replace('object','str').replace('int64','int').replace('float64','float')})"
            for col, dtype in zip(df.columns, df.dtypes)
        )
        # Give the model a peek at real values so questions are meaningful
        sample = df.head(3).to_dict(orient="records")

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You generate example data questions for a data analysis app. "
                        'Output MUST be a raw JSON array of exactly 4 strings: ["Q1?","Q2?","Q3?","Q4?"] '
                        "Do NOT use objects, dicts, keys, or wrappers of any kind. "
                        "Do NOT write {query:...} or {question:...} — only plain quoted strings inside the array. "
                        "No markdown, no explanation. Just the array. "
                        "Mix: 2 text/aggregation questions and 2 chart/visualization questions. "
                        "Use actual column names. Max 8 words per question."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Columns: {column_info}\nSample rows: {sample}\n\nReturn 4 example questions as a JSON array.",
                },
            ],
            temperature=0.4,
            max_tokens=200,
        )

        raw = response.choices[0].message.content.strip()

        # Strip markdown fences
        if raw.startswith("```"):
            raw = "\n".join(
                l for l in raw.splitlines() if not l.strip().startswith("```")
            ).strip()

        import json, re

        # Strip any markdown fences that slipped through
        raw = re.sub(r"```[\w]*", "", raw).strip()

        questions = json.loads(raw)

        # Unwrap nested {"questions": [...]} wrapper the model sometimes adds
        if isinstance(questions, dict):
            for v in questions.values():
                if isinstance(v, list):
                    questions = v
                    break

        if isinstance(questions, list) and len(questions) > 0:
            cleaned = []
            for q in questions[:4]:
                if isinstance(q, dict):
                    # Extract string value regardless of key name
                    # handles "question", "query", "Question", "Query", etc.
                    val = next(
                        (v for v in q.values() if isinstance(v, str)),
                        str(next(iter(q.values())))
                    )
                    cleaned.append(val.strip())
                else:
                    cleaned.append(str(q).strip())
            if cleaned:
                return cleaned

    except Exception:
        pass  # fall through to generic fallback

    # ── Fallback: build generic questions from column names ──────
    cols = list(df.columns)
    num_cols  = df.select_dtypes(include="number").columns.tolist()
    cat_cols  = df.select_dtypes(include="object").columns.tolist()

    fallback = []
    if num_cols:
        fallback.append(f"Top 3 highest {num_cols[0]}?")
        fallback.append(f"Average {num_cols[0]} overall?")
    if cat_cols and num_cols:
        fallback.append(f"Show {num_cols[0]} by {cat_cols[0]} bar chart")
        fallback.append(f"Distribution of {num_cols[0]}")
    else:
        fallback = [
            "Show data distribution",
            "What are the top values?",
            "Compare values by category",
            "Show trends in the data",
        ]

    return fallback[:4]


# ── Main router ──────────────────────────────────────────────────
def run_agent(df: pd.DataFrame, question: str) -> dict:
    """
    Routes to EDA engine or direct code-gen pipeline.
    Always returns a dict — never raises.
    """
    try:
        # ── EDA route ────────────────────────────────────────────
        if is_eda_question(question):
            fig, insight = run_eda(question, df)
            return {
                "type":    "eda",
                "fig":     fig,
                "insight": insight,
                "answer":  None,
            }

        # ── Direct code-gen route (fast, no agent loop) ──────────
        column_info = ", ".join(
            f"{col} ({dtype})" for col, dtype in zip(df.columns, df.dtypes)
        )
        df.to_csv("temp_data.csv", index=False)

        # Step 1 — generate code
        code = generate_code(question, column_info)

        # Step 2 — execute code
        raw_output = run_code(code)

        # Step 3 — format output
        answer = format_answer(raw_output, question)

        return {
            "type":    "text",
            "answer":  answer,
            "fig":     None,
            "insight": None,
        }

    except Exception as e:
        return {
            "type":    "text",
            "answer":  f"⚠ Error: {str(e)}",
            "fig":     None,
            "insight": None,
        }