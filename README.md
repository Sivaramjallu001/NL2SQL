# 🧠 Natural Language to SQL

This Streamlit app allows you to **ask questions in plain English** and automatically generates the correct SQL query for your uploaded SQLite database. It uses **Google Gemini 1.5 Flash** for natural language understanding and includes advanced **country/region matching** using fuzzy logic and semantic search.

---

## 📌 Features

- 📁 Upload any `.db` (SQLite) file
- 💬 Ask natural language questions like:
  - `Show orders from Bharat in 2025`
  - `List customers from USA`
  - `Get sales from deutschland`
- 🧠 Uses Google Gemini to generate SQL queries from your question
- 🌍 Fuzzy matching of country names via:
  - `country_converter` for ISO name normalization
  - `rapidfuzz` for typo handling
  - `sentence-transformers` for semantic similarity
- 📊 Executes and displays SQL results directly

---


