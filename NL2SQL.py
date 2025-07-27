import streamlit as st
import pandas as pd
import sqlite3
import os
import google.generativeai as genai

# ✅ Configure Gemini API key
GOOGLE_API_KEY = "YOUR-API-KEY"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# ✅ Streamlit setup
st.set_page_config(page_title="AI-Powered SQL Generator", layout="wide")
st.title("🧠 Natural Language to SQL with Table Intelligence")

# ✅ File uploader
uploaded_file = st.file_uploader("📁 Upload a SQLite .db file", type=["db", "sql"])

if uploaded_file:
    # ✅ Save file temporarily
    db_path = f"temp_{uploaded_file.name}"
    with open(db_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # ✅ Connect to SQLite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # ✅ Get tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    if not tables:
        st.warning("No tables found in database.")
        st.stop()

    # ✅ Show tables
    st.subheader("🗂 Database Schema Overview")
    schema_info = []
    for table in tables:
        st.markdown(f"**📌 Table: `{table}`**")
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table} LIMIT 5;", conn)
            st.dataframe(df)
        except Exception as e:
            st.error(f"Could not read table {table}: {e}")
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]
        schema_info.append(f"Table '{table}' has columns: {', '.join(columns)}")

    schema_text = "\n".join(schema_info)

    # ✅ Distinct values for each column
    column_values_info = []
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]
        for col in columns:
            try:
                query = f"SELECT DISTINCT {col} FROM {table} LIMIT 10"
                values = cursor.execute(query).fetchall()
                flat_values = [str(v[0]) for v in values if v[0] is not None]
                if flat_values:
                    column_values_info.append(f"{table}.{col} = {flat_values}")
            except:
                continue
    column_values_text = "\n".join(column_values_info)

    st.markdown("---")
    st.subheader("💬 Ask Your Data Question")

    # ✅ Text input
    nl_query = st.text_input(
        "Question about your data",
        placeholder="e.g., Show customers from US or sales in India"
    )

    if nl_query and st.button("🔍 Generate and Execute Query"):
        # ✅ Sample data
        sample_table = tables[0]
        sample_data = pd.read_sql_query(f"SELECT * FROM {sample_table} LIMIT 3", conn).to_string()

        # ✅ Prompt for Gemini
        prompt = f"""You are an intelligent SQL assistant. Convert the natural language question into a valid SQL query.

                        Database Overview:
                        - Users and sellers are from multiple regions like India, USA, UK, and Germany.
                        - Sellers offer multiple products.
                        - Orders store user ID, product ID, quantity, and date across 2023, 2024, and 2025.

                        Schema:
                        {schema_text}

                        Sample Values:
                        {column_values_text}

                        Sample Data (from a few tables):
                        {sample_data}

                        Natural Language Question:
                        \"\"\"{nl_query}\"\"\"

                        Rules:
                        1. Recognize country/region synonyms (e.g., US, USA, America = United States).
                        2. Handle minor spelling errors in country names.
                        3. Use only table/column names from the schema.
                        4. Return only the SQL query.
                        5. The SQL should be ready to run directly on the uploaded database.
                        6. If a user asks about "India", match all variants like: 'india', 'IND', 'bharat', 'Bharat' like for any other country as well.

                        Important Notes:
                        - Use real column values when appropriate.
                        - Be strict about using only the tables and columns listed.
                        - Assume fuzzy synonyms for country/region terms when needed.

                        SQL Query:
                        """

        with st.spinner("🔄 Analyzing your question and generating SQL..."):
            try:
                response = model.generate_content(prompt)
                sql_query = response.text.strip().replace("```sql", "").replace("```", "").strip()
                st.markdown("### 🧾 Generated SQL")
                st.code(sql_query, language="sql")
            except Exception as e:
                st.error(f"Query generation failed: {str(e)}")
                st.stop()

        # ✅ Execute query if SELECT
        if sql_query.strip().lower().startswith("select"):
            try:
                result_df = pd.read_sql_query(sql_query, conn)
                st.markdown("### 📊 Query Results")
                if result_df.empty:
                    st.info("✅ Query ran but returned no results.")
                    st.warning("⚠️ No data matched. Try rephrasing or making your query more specific.")
                else:
                    st.dataframe(result_df, use_container_width=True)

                    # ✅ Region explanation
                    if any(term in nl_query.lower() for term in ['region', 'country', 'us', 'uk', 'india']):
                        explanation_prompt = f"""Briefly explain how you handled regional terms in this query:
                                                    Original: \"{nl_query}\"
                                                    SQL: \"{sql_query}\"
                                                    """
                        explanation = model.generate_content(explanation_prompt).text.strip()
                        st.info(f"🧠 AI Note: {explanation}")
            except Exception as e:
                st.error(f"Query failed: {str(e)}")
                st.warning("⚠️ This might be due to an unclear question or schema mismatch.")
                st.info("💬 Tip: Reword your question. Example: 'List all orders from sellers in INDIA'")

                fix_prompt = f"""This SQL query failed with error: {str(e)}
                                    Query: {sql_query}
                                    Schema: {schema_text}
                                    Suggest a corrected SQL version (only SQL):
                                    """
                try:
                    fixed_sql = model.generate_content(fix_prompt).text.strip()
                    st.info(f"🛠 Suggested Fix:\n{fixed_sql}")
                except:
                    st.warning("Model couldn't fix the query. Try rephrasing.")
        else:
            st.info("Try a different data query like: 'Show top 5 products in 2024'.")

    # ✅ Cleanup
    conn.close()
    os.remove(db_path) if os.path.exists(db_path) else None

else:
    st.info("👋 Please upload a SQLite database file to begin.")
