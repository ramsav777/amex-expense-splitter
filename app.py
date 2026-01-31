"""
American Express Expense Splitter - Streamlit Application

A mobile-friendly web app to process Amex PDF statements and split expenses
between Person A, Person B, and Joint categories.
"""

import streamlit as st
import pandas as pd
import socket
from pathlib import Path
from processor import (
    load_rules,
    save_rules,
    extract_transactions,
    apply_rules_to_transactions,
    categorize_transaction
)


def get_local_ip():
    """Get the local IP address for network access."""
    try:
        # Create a socket to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "localhost"


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'transactions' not in st.session_state:
        st.session_state.transactions = []
    if 'rules' not in st.session_state:
        st.session_state.rules = load_rules()
    if 'uploaded_file_name' not in st.session_state:
        st.session_state.uploaded_file_name = None


def review_tab():
    """Review tab for categorizing transactions."""
    st.header("📋 Review Transactions")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload American Express PDF Statement",
        type=['pdf'],
        help="Select your Amex PDF statement to process"
    )
    
    if uploaded_file is not None:
        # Check if this is a new file
        if st.session_state.uploaded_file_name != uploaded_file.name:
            with st.spinner("Processing PDF..."):
                # Save temporarily to process
                temp_path = Path("temp_statement.pdf")
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Extract and categorize transactions
                transactions = extract_transactions(str(temp_path))
                st.session_state.transactions = apply_rules_to_transactions(
                    transactions, 
                    st.session_state.rules
                )
                st.session_state.uploaded_file_name = uploaded_file.name
                
                # Clean up temp file
                temp_path.unlink()
                
            st.success(f"✅ Processed {len(st.session_state.transactions)} transactions")
    
    # Display transactions that need review
    if st.session_state.transactions:
        needs_review = [t for t in st.session_state.transactions if t['category'] == 'Needs Review']
        categorized = [t for t in st.session_state.transactions if t['category'] != 'Needs Review']
        
        # Show stats with custom styling for dark mode
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div style="background-color: #262730; padding: 15px; border-radius: 10px; text-align: center; border: 2px solid #4A4A5E;">
                <p style="margin: 0; color: #FAFAFA; font-size: 14px;">Total Transactions</p>
                <p style="font-size: 28px; font-weight: bold; margin: 5px 0; color: #29B5E8;">{len(st.session_state.transactions)}</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style="background-color: #262730; padding: 15px; border-radius: 10px; text-align: center; border: 2px solid #4A4A5E;">
                <p style="margin: 0; color: #FAFAFA; font-size: 14px;">Needs Review</p>
                <p style="font-size: 28px; font-weight: bold; margin: 5px 0; color: #FF6B6B;">{len(needs_review)}</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div style="background-color: #262730; padding: 15px; border-radius: 10px; text-align: center; border: 2px solid #4A4A5E;">
                <p style="margin: 0; color: #FAFAFA; font-size: 14px;">Categorized</p>
                <p style="font-size: 28px; font-weight: bold; margin: 5px 0; color: #51CF66;">{len(categorized)}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # Reset button
        if st.button("🔄 Reset All Categorizations", type="secondary", help="Clear all categorizations and start fresh"):
            for t in st.session_state.transactions:
                t['category'] = 'Needs Review'
            st.success("✅ All categorizations reset!")
            st.rerun()
        
        if needs_review:
            st.subheader("🔍 Needs Review")
            
            for idx, transaction in enumerate(needs_review):
                with st.container():
                    col1, col2 = st.columns([3, 2])
                    
                    with col1:
                        # Show refund indicator for negative amounts
                        is_refund = transaction['amount'] < 0
                        refund_indicator = " 🔁 REFUND" if is_refund else ""
                        st.write(f"**{transaction['description']}**{refund_indicator}")
                        cardholder_info = f" • {transaction.get('cardholder', '')}" if transaction.get('cardholder') else ""
                        
                        # Format amount: put minus sign before currency symbol
                        amt = transaction['amount']
                        amount_display = f"£{amt:.2f}" if amt >= 0 else f"-£{abs(amt):.2f}"
                        
                        if is_refund:
                            amount_display = f":green[{amount_display}]"
                        st.caption(f"{transaction['date']} • {amount_display}{cardholder_info}")
                    
                    with col2:
                        # Create buttons in a row
                        btn_col1, btn_col2, btn_col3 = st.columns(3)
                        
                        # Get vendor name for checkbox label
                        vendor_name = transaction['description'].split()[0]
                        
                        # Checkbox to enable bulk apply
                        bulk_apply = st.checkbox(
                            f"💾 Remember this choice for future **{vendor_name}** transactions",
                            key=f"bulk_{idx}"
                        )
                        
                        with btn_col1:
                            if st.button("👤 BA", key=f"a_{idx}", use_container_width=True):
                                if bulk_apply:
                                    # Categorize ALL matching transactions and save rule
                                    vendor_upper = vendor_name.upper()
                                    for t in st.session_state.transactions:
                                        if vendor_upper in t['description'].upper():
                                            t['category'] = 'Person A'
                                    st.session_state.rules[vendor_upper] = 'Person A'
                                    save_rules(st.session_state.rules)
                                else:
                                    # Categorize only this transaction
                                    transaction['category'] = 'Person A'
                                st.rerun()
                        
                        with btn_col2:
                            if st.button("👥 RV", key=f"b_{idx}", use_container_width=True):
                                if bulk_apply:
                                    # Categorize ALL matching transactions and save rule
                                    vendor_upper = vendor_name.upper()
                                    for t in st.session_state.transactions:
                                        if vendor_upper in t['description'].upper():
                                            t['category'] = 'Person B'
                                    st.session_state.rules[vendor_upper] = 'Person B'
                                    save_rules(st.session_state.rules)
                                else:
                                    # Categorize only this transaction
                                    transaction['category'] = 'Person B'
                                st.rerun()
                        
                        with btn_col3:
                            if st.button("🏠 Joint", key=f"j_{idx}", use_container_width=True):
                                if bulk_apply:
                                    # Categorize ALL matching transactions and save rule
                                    vendor_upper = vendor_name.upper()
                                    for t in st.session_state.transactions:
                                        if vendor_upper in t['description'].upper():
                                            t['category'] = 'Joint'
                                    st.session_state.rules[vendor_upper] = 'Joint'
                                    save_rules(st.session_state.rules)
                                else:
                                    # Categorize only this transaction
                                    transaction['category'] = 'Joint'
                                st.rerun()
                    
                    st.divider()
        else:
            st.success("🎉 All transactions have been categorized!")
        
        # Edit Categorized Transactions
        if categorized:
            st.subheader("✏️ Edit Categorized Transactions")
            st.caption("Click a button to recategorize any transaction")
            
            for idx, transaction in enumerate(categorized):
                with st.container():
                    col1, col2 = st.columns([3, 2])
                    
                    with col1:
                        current_cat = transaction['category']
                        icon = "👤 BA" if current_cat == "Person A" else ("👥 RV" if current_cat == "Person B" else "🏠 Joint")
                        is_refund = transaction['amount'] < 0
                        refund_indicator = " 🔁 REFUND" if is_refund else ""
                        st.write(f"**{transaction['description']}** • {icon}{refund_indicator}")
                        cardholder_info =f" • {transaction.get('cardholder', '')}" if transaction.get('cardholder') else ""
                        
                        # Format amount
                        amt = transaction['amount']
                        amount_display = f"£{amt:.2f}" if amt >= 0 else f"-£{abs(amt):.2f}"
                        
                        if is_refund:
                            amount_display = f":green[{amount_display}]"
                        st.caption(f"{transaction['date']} • {amount_display}{cardholder_info}")
                    
                    with col2:
                        btn_col1, btn_col2, btn_col3 = st.columns(3)
                        
                        with btn_col1:
                            if st.button("👤", key=f"edit_a_{idx}", use_container_width=True):
                                transaction['category'] = 'Person A'
                                st.rerun()
                        
                        with btn_col2:
                            if st.button("👥", key=f"edit_b_{idx}", use_container_width=True):
                                transaction['category'] = 'Person B'
                                st.rerun()
                        
                        with btn_col3:
                            if st.button("🏠", key=f"edit_j_{idx}", use_container_width=True):
                                transaction['category'] = 'Joint'
                                st.rerun()
                    
                    st.divider()
        
        # Show categorized transactions summary
        if categorized:
            with st.expander(f"📊 View Summary ({len(categorized)} transactions)"):
                df = pd.DataFrame(categorized)
                # Select columns, include cardholder if it exists
                columns = ['date', 'description', 'amount']
                if 'cardholder' in df.columns:
                    columns.append('cardholder')
                columns.append('category')
                df = df[columns]
                df['amount'] = df['amount'].apply(lambda x: f"£{x:.2f}")
                st.dataframe(df, use_container_width=True, hide_index=True)


def settings_tab():
    """Settings tab for managing vendor rules."""
    st.header("⚙️ Settings")
    
    st.subheader("Vendor Categorization Rules")
    st.caption("Manage automatic categorization rules for vendors")
    
    # Display current rules
    if st.session_state.rules:
        st.write("### Current Rules")
        
        # Convert to DataFrame for easy editing
        rules_data = [
            {"Vendor": vendor, "Category": category}
            for vendor, category in st.session_state.rules.items()
        ]
        df = pd.DataFrame(rules_data)
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Delete rule
        st.write("### Remove Rule")
        vendor_to_delete = st.selectbox(
            "Select vendor to remove",
            options=list(st.session_state.rules.keys()),
            key="delete_vendor"
        )
        
        if st.button("🗑️ Delete Rule"):
            del st.session_state.rules[vendor_to_delete]
            save_rules(st.session_state.rules)
            st.success(f"Deleted rule for {vendor_to_delete}")
            st.rerun()
    else:
        st.info("No rules defined yet. Add your first rule below!")
    
    st.divider()
    
    # Add new rule
    st.write("### Add New Rule")
    col1, col2 = st.columns(2)
    
    with col1:
        new_vendor = st.text_input(
            "Vendor Name",
            placeholder="e.g., WALMART",
            help="Enter the vendor name as it appears in statements"
        )
    
    with col2:
        new_category = st.selectbox(
            "Category",
            options=["Person A", "Person B", "Joint"]
        )
    
    if st.button("➕ Add Rule"):
        if new_vendor:
            vendor_upper = new_vendor.upper().strip()
            st.session_state.rules[vendor_upper] = new_category
            save_rules(st.session_state.rules)
            st.success(f"✅ Added rule: {vendor_upper} → {new_category}")
            st.rerun()
        else:
            st.error("Please enter a vendor name")


def summary_tab():
    """Summary tab showing spending breakdown and settlement."""
    st.header("📊 Summary")
    
    if not st.session_state.transactions:
        st.info("Upload a statement in the Review tab to see your summary")
        return
    
    # Calculate "Paid" totals (based on cardholder)
    paid_by_a = sum(
        t['amount'] for t in st.session_state.transactions 
        if t.get('cardholder') == 'Brigita'
    )
    paid_by_b = sum(
        t['amount'] for t in st.session_state.transactions 
        if t.get('cardholder') == 'Ravinder'
    )
    
    # Calculate "Consumed" totals (based on category)
    personal_a = sum(
        t['amount'] for t in st.session_state.transactions 
        if t['category'] == 'Person A'
    )
    personal_b = sum(
        t['amount'] for t in st.session_state.transactions 
        if t['category'] == 'Person B'
    )
    joint_total = sum(
        t['amount'] for t in st.session_state.transactions 
        if t['category'] == 'Joint'
    )
    
    # Display totals with custom styling for better visibility
    st.subheader("Spending Breakdown")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style="background-color: #262730; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #4A4A5E;">
            <h3 style="margin: 0; color: #FAFAFA;">👤 Brigita Paid</h3>
            <p style="font-size: 32px; font-weight: bold; margin: 10px 0; color: #29B5E8;">£{paid_by_a:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background-color: #262730; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #4A4A5E;">
            <h3 style="margin: 0; color: #FAFAFA;">👥 Ravinder Paid</h3>
            <p style="font-size: 32px; font-weight: bold; margin: 10px 0; color: #29B5E8;">£{paid_by_b:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background-color: #262730; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #4A4A5E;">
            <h3 style="margin: 0; color: #FAFAFA;">🏠 Joint Total</h3>
            <p style="font-size: 32px; font-weight: bold; margin: 10px 0; color: #51CF66;">£{joint_total:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Settlement calculation
    st.subheader("💰 Settlement")
    st.caption("Settlement = Total Paid - (Personal Spending + 50% Joint)")
    
    # Responsibility breakdown
    brigita_responsibility = personal_a + (joint_total / 2)
    ravinder_responsibility = personal_b + (joint_total / 2)
    
    # Settlement is based on the delta between what was paid and what should have been paid
    # If Brigita paid more than she is responsible for, Ravinder owes her.
    # brigita_delta = paid_by_a - brigita_responsibility
    # If positive, Brigita overpaid. If negative, she underpaid.
    settlement = paid_by_a - brigita_responsibility
    
    if abs(settlement) < 0.01:
        st.success("✅ You're all squared up! No settlement needed.")
    elif settlement > 0:
        # Brigita paid more than her share, Ravinder owes her
        st.warning(f"**Ravinder owes Brigita: £{abs(settlement):,.2f}**")
    else:
        # Brigita paid less than her share, she owes Ravinder
        st.warning(f"**Brigita owes Ravinder: £{abs(settlement):,.2f}**")
    
    # Detailed breakdown
    with st.expander("📝 Settlement Calculation Details"):
        st.write(f"""
        **Brigita's Math:**
        - Total Paid on Card: £{paid_by_a:,.2f}
        - Personal Expenses: £{personal_a:,.2f}
        - Joint share (50%): £{joint_total/2:,.2f}
        - Responsibility: £{brigita_responsibility:,.2f}
        - Net Delta: {'+' if settlement > 0 else ''}£{settlement:,.2f}
        
        **Ravinder's Math:**
        - Total Paid on Card: £{paid_by_b:,.2f}
        - Personal Expenses: £{personal_b:,.2f}
        - Joint share (50%): £{joint_total/2:,.2f}
        - Responsibility: £{ravinder_responsibility:,.2f}
        - Net Delta: {'+' if -settlement > 0 else ''}£{-settlement:,.2f}
        
        *Note: Negative spending (refunds) correctly reduces both the paid amount and responsibility.*
        """)


def main():
    """Main application entry point."""
    # Page config
    st.set_page_config(
        page_title="Expense Splitter",
        page_icon="💳",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS for mobile-friendly design
    st.markdown("""
        <style>
        .stButton button {
            height: 50px;
            font-weight: bold;
        }
        .stMetric {
            background-color: #f0f2f6;
            padding: 15px;
            border-radius: 10px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.title("💳 American Express Expense Splitter")
    
    # Display network info
    local_ip = get_local_ip()
    st.info(f"📱 **Mobile Access:** Open `http://{local_ip}:8501` on your iPhone")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📋 Review", "⚙️ Settings", "📊 Summary"])
    
    with tab1:
        review_tab()
    
    with tab2:
        settings_tab()
    
    with tab3:
        summary_tab()


if __name__ == "__main__":
    # Print connection info to console
    local_ip = get_local_ip()
    print(f"\n{'='*60}")
    print(f"🚀 Expense Splitter is running!")
    print(f"{'='*60}")
    print(f"Local access: http://localhost:8501")
    print(f"Network access: http://{local_ip}:8501")
    print(f"\n📱 To access from your iPhone:")
    print(f"   Open Safari and navigate to: http://{local_ip}:8501")
    print(f"{'='*60}\n")
    
    main()
