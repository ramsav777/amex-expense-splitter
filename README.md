# American Express Expense Splitter

A mobile-friendly Python web application for processing American Express PDF statements and splitting expenses between two people.

## Features

- 📄 **PDF Processing**: Automatically extract transactions from Amex PDF statements
- 🤖 **Smart Categorization**: Rule-based auto-categorization of vendors
- 📱 **Mobile-Friendly**: Responsive UI accessible from iPhone/mobile browsers
- ✏️ **Easy Review**: Simple interface to categorize unknown transactions
- ⚙️ **Flexible Rules**: Add/edit/delete vendor categorization rules
- 💰 **Settlement Calculation**: Automatic calculation of who owes whom

## Quick Start

1. **Install Dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Run the Application**
   ```powershell
   streamlit run app.py --server.address=0.0.0.0
   ```

3. **Access from Mobile**
   - The app will display the local network IP on startup
   - Open that URL (e.g., `http://192.168.1.xxx:8501`) in your iPhone browser

## How to Use

### 1. Review Tab
- Upload your Amex PDF statement
- Review transactions flagged as "Needs Review"
- Click [Person A], [Person B], or [Joint] to categorize each transaction
- Check "Bulk Apply" to save the categorization rule for future statements

### 2. Settings Tab
- View all current vendor categorization rules
- Add new rules manually
- Delete existing rules

### 3. Summary Tab
- View spending breakdown by person and joint expenses
- See settlement calculation (joint expenses split 50/50)
- Check who owes whom and how much

## Project Structure

```
amex-expense-splitter/
├── app.py              # Main Streamlit application
├── processor.py        # PDF parsing and categorization logic
├── rules.json          # Vendor categorization rules
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Technical Details

- **Framework**: Streamlit (Python web framework)
- **PDF Parsing**: pdfplumber
- **Data Processing**: pandas
- **Storage**: JSON file for rules

## Example Workflow

1. Upload Amex PDF statement
2. App automatically categorizes known vendors (e.g., Kroger → Joint)
3. Review unknown vendors (e.g., Amazon → Needs Review)
4. Categorize manually with one click
5. Optionally save as a rule for future statements
6. View summary with settlement amount

## Notes

- Rules are stored in `rules.json` and persist between sessions
- Transaction data is stored in session state (not persisted)
- The app runs locally and doesn't upload data anywhere
- Joint expenses are always split 50/50 in the settlement calculation
