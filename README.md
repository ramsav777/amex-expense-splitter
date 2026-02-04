# American Express Expense Splitter

A mobile-friendly web application for processing American Express PDF statements and splitting expenses between two people.

## Features

- 📄 **PDF Processing** - Automatically extracts transactions from Amex PDF statements
- 🤖 **Smart Categorization** - Rule-based auto-categorization of vendors
- 📱 **Mobile-Friendly** - Responsive UI accessible from iPhone/mobile browsers
- ✏️ **Easy Review** - Simple interface to categorize unknown transactions
- ⚙️ **Flexible Rules** - Add/edit/delete vendor categorization rules
- 💰 **Settlement Calculation** - Automatic calculation based on assigned spending

## Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation

```bash
pip install -r requirements.txt
```

### Run the Application

```bash
streamlit run app.py --server.address=0.0.0.0
```

The app will be available at `http://localhost:8501`

## Usage

### 1. Review Tab
- Upload your Amex PDF statement
- Review transactions flagged as "Needs Review"
- Click **Person A**, **Person B**, or **Joint** to categorize each transaction
- Check **"Remember this choice"** to save the categorization rule for future statements

### 2. Settings Tab
- View all current vendor categorization rules
- Add new rules manually
- Delete existing rules

### 3. Summary Tab
- View spending breakdown by person and joint expenses
- See settlement calculation (who owes whom)
- Use debug view to verify all extracted transactions

## Settlement Logic

Settlement is calculated based on **assigned spending**, not whose card was used:
- Person A owes: Personal A expenses + 50% of Joint expenses
- Person B owes: Personal B expenses + 50% of Joint expenses
- The person who spent more pays the difference to balance the total

## Deployment

This app can be deployed to Streamlit Community Cloud for free:

1. Push this repository to GitHub
2. Sign in to [Streamlit Cloud](https://streamlit.io/cloud)
3. Deploy from your GitHub repository
4. Access from anywhere on your phone!

## Privacy

- The app runs locally and doesn't upload data anywhere (when self-hosted)
- Transaction data is stored in session state only (not persisted)
- Only vendor rules are saved in `rules.json`
- Uploaded PDFs are processed and immediately deleted

## Technical Stack

- **Framework**: Streamlit
- **PDF Parsing**: pdfplumber
- **Data Processing**: pandas

## License

Personal use project
