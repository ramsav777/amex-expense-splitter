"""
PDF Processing Module for American Express Statement Parser

This module handles:
- PDF extraction using pdfplumber
- Transaction categorization based on vendor rules
- Rules management (loading/saving from JSON)
"""

import pdfplumber
import json
import re
from typing import List, Dict, Optional
from pathlib import Path


def load_rules(rules_path: str = "rules.json") -> Dict[str, str]:
    """Load vendor categorization rules from JSON file."""
    try:
        with open(rules_path, 'r') as f:
            data = json.load(f)
            return data.get("vendor_rules", {})
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def save_rules(rules: Dict[str, str], rules_path: str = "rules.json") -> None:
    """Save vendor categorization rules to JSON file."""
    with open(rules_path, 'w') as f:
        json.dump({"vendor_rules": rules}, f, indent=2)


def extract_transactions(pdf_path: str) -> List[Dict[str, any]]:
    """
    Extract transactions from American Express PDF statement.
    
    Structure: Brigita's transactions → Brigita header → Ravinder's transactions → Ravinder header
    Headers mark the END of each person's section.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of transaction dictionaries with keys: date, description, amount, cardholder
    """
    # PASS 1: Collect all lines with their indices
    all_lines = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            lines = text.split('\n')
            all_lines.extend(lines)
    
    # PASS 2: Find section headers (mark the END of each section)
    brigita_header_idx = None
    ravinder_header_idx = None
    
    for idx, line in enumerate(all_lines):
        if 'Total new spend' in line or 'total new spend' in line.lower():
            if 'BRIGITA' in line.upper() or 'ALMONAITYTE' in line.upper():
                brigita_header_idx = idx
            elif 'RAVINDER' in line.upper() or 'VIRIK' in line.upper() or 'SINGH' in line.upper():
                ravinder_header_idx = idx
    
    # PASS 3: Extract transactions and assign cardholders
    # Structure: [0 to brigita_header] = Brigita, [brigita_header to ravinder_header] = Ravinder
    transactions = []
    
    for idx, line in enumerate(all_lines):
        # Skip section header lines
        if idx == brigita_header_idx or idx == ravinder_header_idx:
            continue
        
        # Skip payments
        if 'PAYMENT RECEIVED' in line.upper() or 'PAYMENT REC' in line.upper():
            continue
        
        # Try UK Amex format: MonDD MonDD DESCRIPTION AMOUNT [CR]
        # CR can appear on the same line OR on the next line
        uk_pattern = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(\d{1,2})\s+(.+?)\s+([\d,]+\.\d{2})'
        uk_match = re.search(uk_pattern, line)
        
        if uk_match:
            month = uk_match.group(1)
            day = uk_match.group(2)
            date = f"{month}{day}"
            description = uk_match.group(5).strip()
            amount_str = uk_match.group(6).replace(',', '')
            
            # Enhanced CR detection: check current line AND next line
            line_upper = line.upper()
            is_credit = bool(re.search(r'\sCR\s|\sCR$|^CR\s', line_upper))
            
            # If not found on current line, check next line
            if not is_credit and idx + 1 < len(all_lines):
                next_line = all_lines[idx + 1].strip().upper()
                # Check if next line is just "CR" or contains "CR" as standalone word
                is_credit = (next_line == 'CR' or bool(re.search(r'\sCR\s|\sCR$|^CR\s', next_line)))
            
            try:
                amount = float(amount_str)
                if is_credit:
                    amount = -amount
                
                # Assign cardholder based on position
                cardholder = ""
                if brigita_header_idx and idx < brigita_header_idx:
                    cardholder = "Brigita"
                elif ravinder_header_idx and brigita_header_idx and \
                     idx > brigita_header_idx and idx < ravinder_header_idx:
                    cardholder = "Ravinder"
                
                transactions.append({
                    'date': date,
                    'description': description,
                    'amount': amount,
                    'cardholder': cardholder,
                    'category': 'Needs Review'
                })
                continue
            except ValueError:
                pass
        
        # Try US Amex format
        # Try US Amex format: MM/DD[/YYYY] DESCRIPTION AMOUNT [CR]
        us_pattern = r'(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\s+(.+?)\s+\$?([\d,]+\.\d{2})'
        us_match = re.search(us_pattern, line)
        
        if us_match:
            date = us_match.group(1)
            description = us_match.group(2).strip()
            amount_str = us_match.group(3).replace(',', '')
            
            # Enhanced CR detection: check current line AND next line
            line_upper = line.upper()
            is_credit = bool(re.search(r'\sCR\s|\sCR$|^CR\s', line_upper))
            
            # If not found on current line, check next line
            if not is_credit and idx + 1 < len(all_lines):
                next_line = all_lines[idx + 1].strip().upper()
                # Check if next line is just "CR" or contains "CR" as standalone word
                is_credit = (next_line == 'CR' or bool(re.search(r'\sCR\s|\sCR$|^CR\s', next_line)))
            
            try:
                amount = float(amount_str)
                if is_credit:
                    amount = -amount
                
                # Assign cardholder
                cardholder = ""
                if brigita_header_idx and idx < brigita_header_idx:
                    cardholder = "Brigita"
                elif ravinder_header_idx and brigita_header_idx and \
                     idx > brigita_header_idx and idx < ravinder_header_idx:
                    cardholder = "Ravinder"
                
                transactions.append({
                    'date': date,
                    'description': description,
                    'amount': amount,
                    'cardholder': cardholder,
                    'category': 'Needs Review'
                })
            except ValueError:
                continue
    
    return transactions


def categorize_transaction(description: str, rules: Dict[str, str]) -> Optional[str]:
    """
    Categorize a transaction based on vendor rules.
    
    Args:
        description: Transaction description from statement
        rules: Dictionary of vendor patterns to categories
        
    Returns:
        Category name if matched, otherwise None
    """
    # Normalize description to uppercase for matching
    desc_upper = description.upper()
    
    # Check each rule - look for vendor name anywhere in description
    for vendor, category in rules.items():
        vendor_upper = vendor.upper()
        if vendor_upper in desc_upper:
            return category
    
    return None


def apply_rules_to_transactions(transactions: List[Dict], rules: Dict[str, str]) -> List[Dict]:
    """
    Apply categorization rules to a list of transactions.
    
    Args:
        transactions: List of transaction dictionaries
        rules: Vendor categorization rules
        
    Returns:
        Updated transactions with categories applied
    """
    for transaction in transactions:
        category = categorize_transaction(transaction['description'], rules)
        if category:
            transaction['category'] = category
        else:
            transaction['category'] = 'Needs Review'
    
    return transactions
