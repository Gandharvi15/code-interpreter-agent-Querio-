import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

# ── Keyword trigger list ─────────────────────────────────────────
EDA_KEYWORDS = [
    "show", "plot", "chart", "graph", "visualize", "visualise",
    "distribution", "compare", "comparison", "trend", "scatter",
    "histogram", "bar", "correlation", "spread", "breakdown",
    "vs", "versus", "over time", "by department", "by category"
]

def is_eda_question(question: str) -> bool:
    """Returns True if the question should trigger a chart."""
    q = question.lower()
    return any(kw in q for kw in EDA_KEYWORDS)


def pick_chart_type(question: str, df: pd.DataFrame) -> str:
    """
    Rule-based chart type selector based on question keywords and data shape.
    Returns one of: bar, histogram, scatter, box, line, pie
    """
    q = question.lower()
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(include="object").columns.tolist()

    if any(k in q for k in ["distribution", "histogram", "spread"]):
        return "histogram"
    if any(k in q for k in ["scatter", "correlation", "vs", "versus", "relationship"]):
        return "scatter"
    if any(k in q for k in ["box", "range", "outlier", "quartile"]):
        return "box"
    if any(k in q for k in ["trend", "over time", "line"]):
        return "line"
    if any(k in q for k in ["proportion", "share", "percentage", "pie"]):
        return "pie"
    # Default: bar for categorical comparisons
    return "bar"


def pick_columns(question: str, df: pd.DataFrame, chart_type: str):
    """
    Heuristically pick the best x and y columns from the question + df.
    Returns (x_col, y_col) or (col,) for single-axis charts.
    """
    q = question.lower()
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(include="object").columns.tolist()

    # Try to find columns mentioned in the question
    mentioned = [c for c in df.columns if c.lower() in q]

    if chart_type == "histogram":
        col = mentioned[0] if mentioned and mentioned[0] in numeric_cols else (numeric_cols[0] if numeric_cols else None)
        return (col, None)

    if chart_type == "scatter":
        if len(mentioned) >= 2:
            return (mentioned[0], mentioned[1])
        if len(numeric_cols) >= 2:
            return (numeric_cols[0], numeric_cols[1])
        return (numeric_cols[0], numeric_cols[0]) if numeric_cols else (None, None)

    if chart_type == "pie":
        x = mentioned[0] if mentioned and mentioned[0] in categorical_cols else (categorical_cols[0] if categorical_cols else None)
        y = mentioned[1] if len(mentioned) > 1 and mentioned[1] in numeric_cols else (numeric_cols[0] if numeric_cols else None)
        return (x, y)

    if chart_type in ("bar", "box", "line"):
        # x = categorical, y = numeric
        x = next((c for c in mentioned if c in categorical_cols), categorical_cols[0] if categorical_cols else None)
        y = next((c for c in mentioned if c in numeric_cols), numeric_cols[0] if numeric_cols else None)
        return (x, y)

    return (None, None)


def build_chart(question: str, df: pd.DataFrame):
    """
    Builds and returns a Plotly figure based on question + df.
    Returns (fig, chart_type, x_col, y_col)
    """
    chart_type = pick_chart_type(question, df)
    x_col, y_col = pick_columns(question, df, chart_type)

    # Chart theme: white plot area on lavender paper — bold contrasting colors
    PAPER   = "#F5F0FF"
    BG      = "#FFFFFF"
    GRID    = "rgba(100,80,200,0.10)"
    TEXT    = "#2D2350"
    TEXT2   = "#7A6EA0"
    # Vivid palette — no color near the lavender bg, so elements always pop
    PALETTE = ["#5B21B6","#0EA5E9","#F43F5E","#F59E0B","#10B981","#8B5CF6","#EC4899","#06B6D4"]

    base_layout = dict(
        paper_bgcolor=PAPER,
        plot_bgcolor=BG,
        font=dict(family="DM Sans, sans-serif", color=TEXT, size=13),
        margin=dict(l=48, r=24, t=56, b=48),
        xaxis=dict(
            gridcolor=GRID,
            linecolor="rgba(100,80,200,0.20)",
            tickcolor="rgba(100,80,200,0.20)",
            tickfont=dict(color=TEXT2, size=11),
            showgrid=True,
        ),
        yaxis=dict(
            gridcolor=GRID,
            linecolor="rgba(100,80,200,0.20)",
            tickcolor="rgba(100,80,200,0.20)",
            tickfont=dict(color=TEXT2, size=11),
            showgrid=True,
        ),
        colorway=PALETTE,
    )

    fig = None

    try:
        if chart_type == "histogram" and x_col:
            fig = px.histogram(df, x=x_col, nbins=15,
                               color_discrete_sequence=[PALETTE[0]])
            fig.update_traces(marker_line_color=PAPER, marker_line_width=1.5)

        elif chart_type == "scatter" and x_col and y_col:
            color_col = next((c for c in df.select_dtypes("object").columns), None)
            fig = px.scatter(df, x=x_col, y=y_col,
                             color=color_col,
                             hover_data=df.columns.tolist(),
                             color_discrete_sequence=PALETTE)
            fig.update_traces(marker=dict(size=9, opacity=0.8))

        elif chart_type == "box" and x_col and y_col:
            fig = px.box(df, x=x_col, y=y_col,
                         color=x_col,
                         color_discrete_sequence=PALETTE)

        elif chart_type == "line" and x_col and y_col:
            fig = px.line(df, x=x_col, y=y_col,
                          color_discrete_sequence=[PALETTE[0]])
            fig.update_traces(line=dict(width=2.5))

        elif chart_type == "pie" and x_col and y_col:
            agg = df.groupby(x_col)[y_col].sum().reset_index()
            fig = px.pie(agg, names=x_col, values=y_col,
                         color_discrete_sequence=PALETTE)
            fig.update_traces(textposition="inside", textinfo="percent+label",
                              textfont=dict(color="#FFFFFF"))

        else:
            # Default: grouped bar
            if x_col and y_col:
                agg = df.groupby(x_col)[y_col].mean().reset_index().sort_values(y_col, ascending=False)
                fig = px.bar(agg, x=x_col, y=y_col,
                             color=x_col,
                             color_discrete_sequence=PALETTE)
                fig.update_traces(marker_line_color=PAPER, marker_line_width=1.5)

        if fig:
            fig.update_layout(**base_layout)
            title = question.strip().rstrip("?").capitalize()
            fig.update_layout(
                title=dict(text=title, font=dict(size=15, color=TEXT, weight="bold"), x=0),
                showlegend=True,
                legend=dict(bgcolor="rgba(245,240,255,0.8)", bordercolor=GRID,
                            font=dict(color=TEXT)),
            )

    except Exception as e:
        print(f"Chart build error: {e}")
        fig = None

    return fig, chart_type, x_col, y_col


def generate_insight(question: str, df: pd.DataFrame, chart_type: str, x_col: str, y_col: str) -> str:
    """
    Calls Groq to generate a 2-3 sentence storytelling insight about the chart data.
    """
    try:
        # Build a data summary to feed to the LLM
        if x_col and y_col and x_col in df.columns and y_col in df.columns:
            if chart_type in ("bar", "box", "pie"):
                summary = df.groupby(x_col)[y_col].agg(["mean", "min", "max"]).round(2).to_string()
            elif chart_type == "histogram":
                summary = df[x_col].describe().round(2).to_string()
            elif chart_type == "scatter":
                corr = df[[x_col, y_col]].corr().iloc[0, 1]
                summary = f"Correlation between {x_col} and {y_col}: {corr:.2f}\n" + df[[x_col, y_col]].describe().round(2).to_string()
            else:
                summary = df[[x_col, y_col]].describe().round(2).to_string()
        elif x_col and x_col in df.columns:
            summary = df[x_col].describe().round(2).to_string()
        else:
            summary = df.describe().round(2).to_string()

        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        prompt = f"""You are a data storyteller. Given this data summary and the user's question, write exactly 2-3 sentences of insight in a storytelling style — like a data journalist would. Be specific, use actual numbers from the summary, and highlight what's most surprising or meaningful. Do NOT use bullet points. Write in flowing prose only.

User question: {question}
Chart type: {chart_type}
Data summary:
{summary}

Write your insight now:"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=180
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"The data reveals interesting patterns across {x_col or 'the dataset'}. Explore the chart above to uncover trends and outliers in your data."


def run_eda(question: str, df: pd.DataFrame):
    """
    Main EDA entry point.
    Returns (fig, insight_text) — fig may be None if chart couldn't be built.
    """
    fig, chart_type, x_col, y_col = build_chart(question, df)
    insight = generate_insight(question, df, chart_type, x_col, y_col)
    return fig, insight