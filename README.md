# 💸 Personal Finance & Expense Analyzer

<p align="center">
  <strong>A Streamlit-based application to analyze personal finances, explore spending patterns, and convert bank statements into structured transaction data.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/Pandas-Data%20Analysis-150458?logo=pandas" alt="Pandas">
  <img src="https://img.shields.io/badge/Status-Portfolio%20Project-purple" alt="Project Status">
</p>

---

## 📌 Project Overview

The **Personal Finance & Expense Analyzer** is a Python-based data analytics project designed to help users understand their income, expenses, and cash flow through an interactive web application.

Built with Streamlit, the application provides a financial dashboard where users can upload transaction data, filter records, explore monthly trends, and analyze spending by category and payment method.

It also includes a **PDF bank statement converter** to support the extraction and conversion of statement data into a structured format for further analysis.

## ✨ Key Features

### 📊 Interactive Expense Dashboard
- Upload transaction data using a CSV file.
- View total income, total expenses, and net cash flow.
- Calculate the expense-to-income percentage.
- Analyze monthly income and expenses.
- Track monthly net cash flow.
- Explore expenses by category and payment method.
- View a category-wise spending summary, including transaction count, total, and average expenses.
- Filter transactions by date range, category, transaction type, payment method, and city.

### 📄 PDF Bank Statement Converter
- Includes a separate tool for bank statement conversion.
- Supports a workflow for extracting and standardizing transaction data from PDF statements.
- Helps prepare transaction records for analysis and CSV export.

<details>
<summary><strong>🔍 More about data handling</strong></summary>

- Automatically recognizes several common transaction column names.
- Allows users to map columns from differently formatted bank statement CSV files.
- Handles common currency symbols and comma-separated amounts.
- Parses transaction dates and validates transaction records.
- Identifies and skips invalid records where applicable.
- Allows filtered transactions to be downloaded as a CSV file.

</details>

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Streamlit | Interactive web application |
| Pandas | Data cleaning, transformation, and analysis |
| NumPy | Numerical and statistical operations |
| Plotly | Interactive visualization support where used |
| Matplotlib | Data visualization in the original analysis workflow |
| Seaborn | Statistical visualization in the original analysis workflow |

## ⚙️ Installation and Setup

Follow these steps to run the project locally.

### 1. Clone the repository

```bash
git clone https://github.com/adityarm1704/personal finance expense analyzer.git
```


### 2. Navigate to the project folder

```bash
cd YOUR-REPOSITORY
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

### 4. Activate the virtual environment

**Windows:**

```bash
.venv\Scripts\activate
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

### 5. Install the dependencies

If your project contains a `requirements.txt` file:

```bash
python -m pip install -r requirements.txt
```

If you do not have a requirements file yet, install the main dashboard dependencies:

```bash
python -m pip install streamlit pandas numpy plotly
```

Install any additional libraries required by the PDF converter according to your project's imports.

### 6. Run the application

```bash
streamlit run app.py
```

The application should open in your default browser. If it does not, open the local URL displayed in your terminal.

## 🚀 How to Use

1. Launch the application using Streamlit.
2. Select **Expense dashboard** or **PDF statement converter** from the sidebar.
3. For the dashboard, upload a CSV file containing your transactions.
4. If your CSV uses different column names, map the relevant columns using the sidebar controls.
5. Adjust the date range and other filters to explore specific transactions.
6. Review financial metrics, monthly trends, and spending summaries.
7. Open the Transactions tab to inspect records and download filtered transactions as a CSV file.

## 📁 Project Structure

```text
Personal_finance_streamlit/
│
├── app.py                  # Main Streamlit application
├── bank_pdf_converter.py   # PDF statement conversion functionality
├── requirements.txt        # Project dependencies
├── README.md               # Project documentation
└── transactions.csv        # Optional default transaction dataset
```

*The file names above describe the intended structure. Adjust this section to match the files actually included in your repository. The default CSV dataset is optional if users upload their own data.*

## 📈 Expected Outcomes

The application helps users:

- Understand income and expenses over a selected period.
- Identify categories that account for a larger share of spending.
- Compare monthly income with expenses.
- Monitor net cash flow.
- Review transaction records in a structured format.
- Prepare supported bank statement data for analysis.

## 🔒 Data Privacy

- Use synthetic or anonymized transaction data when demonstrating the project publicly.
- Do not upload real bank statements, account numbers, or other sensitive financial information to a public GitHub repository.
- Review any data before sharing or uploading it.
- This project is intended for educational and analytical purposes and does not provide professional financial advice.

## 🎯 Learning Objectives

This project demonstrates practical experience with:

- Python programming and data analysis.
- Data cleaning and validation.
- Pandas data manipulation and aggregation.
- Interactive dashboard development with Streamlit.
- Financial KPI calculation.
- Time-series analysis and data visualization.
- File upload, transaction processing, and CSV export workflows.

## 🔮 Future Improvements

- Add customizable expense budgets and savings goals.
- Introduce more detailed financial insights and alerts.
- Add additional statement formats and improve PDF extraction reliability.
- Include exportable financial reports.
- Deploy the application online for easier access.

## 👨‍💻 Author

**Aditya Masure**

<p>
  <a href="https://github.com/adityarm1704">GitHub Profile</a>
</p>

---

<p align="center">
  <em>Built with Python and Streamlit to make personal finance analysis more accessible.</em>
</p>
