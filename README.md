# FinSight — Personal Finance & Expense Analyzer

A beginner-friendly Streamlit frontend based on the uploaded `Personal_Finance_Expense_Analyzer_Debugged_Private_PDF_Converter` notebook.

## Features

- Dark navy and purple dashboard with income, expenses, net cash flow and savings rate.
- Monthly cash-flow charts, category breakdown, and spending insights.
- Transaction search and filters, with filtered CSV export.
- Data-quality checks and cleaning summaries.
- PDF statement table extraction using `pdfplumber`, column mapping, redacted preview, standardized transactions, review flags, validation report, and opt-in sanitized CSV export.
- The demo generator mirrors the notebook's seeded 3,000-row synthetic transaction data and intentional quality issues.

## Run on Windows

1. Install Python 3.10 or newer from https://www.python.org/downloads/ if needed. During installation, select **Add Python to PATH**.
2. Extract this project folder to a location you can find, such as Desktop.
3. Open Command Prompt or the VS Code terminal in this folder.
4. Create and activate a virtual environment:

   ```bat
   py -m venv .venv
   .venv\Scripts\activate
   ```

5. Install packages:

   ```bat
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

6. Start the app:

   ```bat
   streamlit run app.py
   ```

7. Your browser should open automatically. If not, visit `http://localhost:8501`.

## Use your own transaction CSV

Choose **Upload transaction CSV** in the sidebar. At minimum, the file must have these columns:

- `Date`
- `Amount`
- `Type` (values `Income` or `Expense`)

Recommended extra columns: `Transaction_ID`, `Description`, `Category`, `Payment_Mode`, `Account`, `City`. Missing optional columns are filled with neutral defaults. Rows with missing dates, missing amounts, negative amounts, or unsupported transaction types are excluded from dashboard calculations. Duplicate transaction IDs are deduplicated.

## Use the PDF analyzer

1. Open **PDF Statement Analyzer**.
2. Upload a table-based PDF statement. The app extracts tables but does not run OCR on scanned PDFs.
3. Select a detected table and the header row.
4. Inspect the masked preview and map the date, description, and debit/credit (or amount) columns.
5. Click **Analyze mapped transactions** and review the validation report and any `Review` rows.
6. Tick the review confirmation checkbox before downloading the sanitized CSV.

**Privacy reminder:** use a local copy of your statement. Sensitive-text redaction is a safeguard, not a guarantee. Carefully inspect the sanitized output before sharing it. The app does not intentionally save the uploaded PDF to disk, but the hosting environment and its logs are outside this app's control. Avoid deploying with real statements to a public server.

## Project files

- `app.py` — Streamlit interface and data/PDF processing functions.
- `requirements.txt` — required Python packages.

## Notes

- Demo data is synthetic and should not be described as real customer financial data.
- The PDF workflow intentionally excludes account/customer metadata from the sanitized export.
- Refunds/reversals, ambiguous amounts, zero amounts, and invalid dates are flagged for review rather than confidently classified.
- This is an educational analytics tool, not financial advice or a bank-certified statement parser.
