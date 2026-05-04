import os
import json
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
from anomaly import get_all_anomalies
from database import get_connection


load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def ask_llm(prompt, system_prompt="You are a helpful domain monitoring assistant."):
    """Makes a single call to the Groq LLM and returns the response text.

    Args:
        prompt: The user message to send
        system_prompt: Instructions that define the AI's role and behaviour

    Returns:
        str: The model's response as a plain string
    """
    chat_completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    return chat_completion.choices[0].message.content


def format_anomalies_for_llm(anomalies):
    """Converts a list of anomaly dicts into a plain text string for the LLM.

    Args:
        anomalies: List of dicts with keys severity, domain, issue

    Returns:
        str: Formatted string with one anomaly per line
    """
    lines = []
    for a in anomalies:
        line = f"[{a['severity']}] {a['domain']} — {a['issue']}"
        lines.append(line)
    return "\n".join(lines)


def summarize_anomalies():
    """Fetches all anomalies from the DB and asks the LLM to summarize them.

    Sends the anomaly list to Groq with a structured system prompt.
    Asks for JSON output grouped by severity.

    Returns:
        dict: Parsed JSON with keys critical, warning, info
              Returns empty dict if parsing fails.
    """

    anomalies = get_all_anomalies()

    if not anomalies:
        print("No anomalies found.")
        return {}

    anomalies_text = format_anomalies_for_llm(anomalies)

    system_prompt = """You are a domain monitoring assistant.
    You will be given a list of domain anomalies with severity levels.
    Respond ONLY with a valid JSON object — no explanation, no markdown, no backticks.
    The JSON must have exactly these three keys: critical, warning, info.
    Each key maps to a list of strings summarizing the issues for that severity level.
    Example format:
    {
        "critical": ["domain.com — SSL cert expires in 3 days"],
        "warning": ["example.com — SSL cert expires in 25 days"],
        "info": ["google.com — Multiple A records found (6)"]
    }"""

    response = ask_llm(anomalies_text, system_prompt)

    try:
        result = json.loads(response)
        return result
    except json.JSONDecodeError:
        print("LLM returned malformed JSON. Retrying with stricter prompt...")
        strict_prompt = system_prompt + \
            "\nYou MUST return only raw JSON. No other text whatsoever."
        response = ask_llm(anomalies_text, strict_prompt)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            print("Retry also failed. Check error manually.")
            print(response)
            return {}


def natural_language_query(question):
    """Converts a plain English question into SQL and runs it against the database.

    Sends the question along with the DB schema to the LLM which returns
    a SQL SELECT query. Validates it is SELECT only before executing.

    Args:
        question: Plain English question e.g. 'show me domains expiring this month'

    Returns:
        pandas.DataFrame: Query results, empty DataFrame if query fails
    """

    schema = """
    Table: dns_records
    Columns: id , domain, record_type(A/MX/NS)  , value , fetched_at(YYYY-MM-DD HH:MM:SS)
    Note: Use SELECT DISTINCT domain when querying for unique domains to avoid duplicates.
    
    Table: ssl_certs  
    Columns: id, domain, issuer , exp_date(YYYY-MM-DD), days_until_expiry, fetched_at(YYYY-MM-DD HH:MM:SS)
    """

    system_prompt = """You are a SQL expert working with a SQLite database that monitors domains.
    You will be given a database schema and a plain English question from the user.
    Your job is to convert the question into a valid SQLite SELECT query.
    Respond ONLY with the raw SQL query — no explanation, no markdown, no backticks, no extra text.
    The query must start with SELECT.
    Only use tables and columns that exist in the schema provided.
    Never use DELETE, DROP, INSERT, or UPDATE."""

    # 3 - combine schema and question into one prompt
    prompt = f"{schema}\n\nQuestion: {question}"

    # 4 - call ask_llm and get the SQL back
    sql_query = ask_llm(prompt, system_prompt)

    # 5 - strip whitespace
    sql_query = sql_query.strip()

    # 6 - safety check
    if not sql_query.upper().startswith("SELECT"):
        print(f"Rejected: {sql_query}")
        return pd.DataFrame()

    # 7 - run the query against your DB and return a DataFrame
    try:
        conn = get_connection()
        df = pd.read_sql_query(sql_query, conn)
        return df
    except Exception as e:
        print(f"Failed: {e}")
        return pd.DataFrame()
