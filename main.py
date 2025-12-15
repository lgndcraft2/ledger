from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import os
from dotenv import load_dotenv
from urllib.parse import urlencode

from ai_agent import generate_llama_report, parse_sales_instruction
from models import db, Transaction

load_dotenv()

# --- APP CONFIGURATION ---
app = Flask(__name__)

# Use SQLite for testing, switch to Neon for production
#uri = "sqlite:///marketcrm.db"
uri = "postgresql://neondb_owner:npg_oIrB8fM3zSCR@ep-red-dawn-agws209r-pooler.c-2.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'myverysecretkey'

# Initialize DB
db.init_app(app)

# Arkesel Config
ARKESEL_API_KEY = os.getenv("ARKESEL_API_KEY")
SMS_SENDER_ID = "ArkeTest"

WHATSAPP_TOKEN = "EAAMC7iBSd84BQFTG2VKC09CyuE6tr9a17qoxtfOoqYMpdPTuzakqBxf0GcGdIwLKEurIHN7P4VBNfscPMRl9roBgSLe3GjnGwoK3maW657VaJhtnxXpbKMnJygzZBlVTw5XoaD8r8VpyF4pdjSdheQpsYmbzen4CUjHdJBUiMegxrBOywQ3uZBzdOYvCT7O8r0XENLJUFaLVPl5G51yHGIblPKLefoZCyR2hIAMNa1Nw5oXmz8ZCWZAGdcB7VuAJCiFPhLS3GDZAolCDSJQiNfQgVT"
PHONE_NUMBER_ID = "889842650881143" 
VERIFY_TOKEN = "marketcrm_secret"

# --- DATABASE MODELS ---
# Transaction model imported from models.py

# with app.app_context():
#     db.create_all()
#     print("Database tables created.")

# --- HELPER CLASS (Refactored Style) ---
class USSDResponse:
    def __init__(self, session_id=None, user_id=None, msisdn=None, message=None, continue_session=True):
        self.sessionID = session_id
        self.userID = user_id
        self.msisdn = msisdn
        self.message = message
        self.continueSession = continue_session

# --- GLOBAL SESSION STATE ---
# Required because Arkesel sends single inputs, so we must remember the step.
session_state = {}

# --- HELPER FUNCTIONS ---
def save_transaction_sql(phone, t_type, party, item, qty, total, paid):
    try:
        new_txn = Transaction(
            user_phone=phone, transaction_type=t_type, party_name=party,
            item_name=item, quantity=int(qty), total_amount=float(total),
            amount_paid=float(paid)
        )
        db.session.add(new_txn)
        db.session.commit()
        return True
    except Exception as e:
        print(f"DB Error: {e}")
        return False

def send_sms(api_key, message, sender_id, phone_number):
    params = {
        "action": "send-sms",
        "api_key": api_key,
        "from": sender_id,
        "to": phone_number,
        "sms": message,
        "use_case": "transactional"  # REQUIRED for Nigeria
    }

    url = "https://sms.arkesel.com/sms/api?" + urlencode(params)

    response = requests.get(url, timeout=10)

    print("Status:", response.status_code)
    print("Raw response:", response.text)

    return response.text

# --- PASTE THIS ABOVE YOUR @app.route CODE ---

def send_whatsapp_message(to_number, message_body):
    # 1. Check if keys are loaded
    if not PHONE_NUMBER_ID or not WHATSAPP_TOKEN:
        print("❌ ERROR: API Keys are missing! Check your .env or variables.")
        return None

    # 2. Prepare the URL and Headers
    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # 3. Clean the phone number (remove '+' if present)
    clean_phone = str(to_number).replace('+', '')
    
    data = {
        "messaging_product": "whatsapp",
        "to": clean_phone,
        "type": "text",
        "text": {"body": message_body}
    }
    
    print(f"📤 Sending reply to {clean_phone}...")
    
    try:
        response = requests.post(url, headers=headers, json=data)

        print(response)
        # 4. Check for success
        if response.status_code == 200:
            print("✅ Message sent successfully!")
            return 200
        else:
            print(f"❌ FAILED to send. Code: {response.status_code}")
            print(f"❌ META ERROR: {response.text}")
            return response.status_code
            
    except Exception as e:
        print(f"❌ CRITICAL CONNECTION ERROR: {e}")
        return None


# --- MAIN ROUTE ---
@app.route('/ussd', methods=['POST'])
def ussd_handler():
    # 1. GET DATA (Safe Handling like your sample)
    ussd_request = request.get_json(silent=True) or request.values
    
    session_id = ussd_request.get('sessionID')
    user_id = ussd_request.get('userID')
    msisdn = ussd_request.get('msisdn') or ussd_request.get('mobile_number')
    user_data = str(ussd_request.get('userData', '')).strip()
    
    # Arkesel often sends 'userInput' instead of 'userData' in some versions
    if not user_data:
        user_data = str(ussd_request.get('user_input', '')).strip()

    # Initialize Response Object
    ussd_response = USSDResponse(
        session_id=session_id,
        user_id=user_id,
        msisdn=msisdn
    )

    # 2. DETECT NEW SESSION
    is_new_session = ussd_request.get('newSession')
    # If Arkesel doesn't send explicit 'newSession' flag, check if state exists
    if is_new_session is None:
        is_new_session = (session_id not in session_state)

    if is_new_session:
        # Initialize State
        session_state[session_id] = {"step": 0, "data": {}}
        ussd_response.message = "Welcome to Ledger Mi\n1. Record Sale\n2. Record Purchase\n3. Manage Debts\n4. Recent Transactions\n5. Quick Summary"
        ussd_response.continueSession = True
        return jsonify(vars(ussd_response))

    # 3. RETRIEVE STATE
    state = session_state.get(session_id)
    step = state["step"]
    data = state["data"]

    # --- LOGIC TREE ---
    
    # MAIN MENU
    if step == 0:
        if user_data == '1':
            ussd_response.message = "Enter Customer Name:"
            state["step"] = 11 # Sale Flow
        elif user_data == '2':
            ussd_response.message = "Enter Supplier Name:"
            state["step"] = 21 # Purchase Flow
        elif user_data == '3':
            ussd_response.message = "1. Customer Debts (In)\n2. My Debts (Out)"
            state["step"] = 30 # Debt Flow
        elif user_data == '4':
            txns = Transaction.query.filter_by(
                user_phone=msisdn
            ).order_by(Transaction.id.desc()).limit(3).all()

            if not txns:
                ussd_response.message = "No transactions yet."
            else:
                msg = "Recent Transactions:\n"
                for t in txns:
                    bal = t.total_amount - t.amount_paid
                    msg += f"{t.transaction_type}: {t.item_name}\nN{t.total_amount} | Bal N{bal}\n"

                ussd_response.message = msg

            ussd_response.continueSession = False
        elif user_data == '5':
            # Generate AI Summary
            summary = generate_llama_report(msisdn)
            ussd_response.message = f"Quick Summary:\n{summary}"
            ussd_response.continueSession = False
        else:
            ussd_response.message = "Invalid Option.\n1. Sale\n2. Purchase"
            ussd_response.continueSession = True

    # --- RECORD SALE FLOW (11 -> 15) ---
    elif step == 11:
        data["customer"] = user_data
        ussd_response.message = "Enter Item Name:"
        state["step"] = 12
    elif step == 12:
        data["item"] = user_data
        ussd_response.message = "Enter Quantity:"
        state["step"] = 13
    elif step == 13:
        data["qty"] = user_data
        ussd_response.message = "Enter Total Price:"
        state["step"] = 14
    elif step == 14:
        data["price"] = user_data
        ussd_response.message = "Enter Amount Collected:"
        state["step"] = 15
    elif step == 15:
        paid = user_data
        save_transaction_sql(msisdn, "SALE", data["customer"], data["item"], data["qty"], data["price"], paid)
        bal = float(data["price"]) - float(paid)
        
        ussd_response.message = f"Sale Saved!\n{data['qty']}x {data['item']}\nBal: N{bal}"
        ussd_response.continueSession = False # End Session
        del session_state[session_id] # Cleanup

    # --- RECORD PURCHASE FLOW (21 -> 25) ---
    elif step == 21:
        data["supplier"] = user_data
        ussd_response.message = "Enter Item Bought:"
        state["step"] = 22
    elif step == 22:
        data["item"] = user_data
        ussd_response.message = "Enter Quantity:"
        state["step"] = 23
    elif step == 23:
        data["qty"] = user_data
        ussd_response.message = "Enter Total Cost:"
        state["step"] = 24
    elif step == 24:
        data["cost"] = user_data
        ussd_response.message = "Enter Amount Paid:"
        state["step"] = 25
    elif step == 25:
        paid = user_data
        save_transaction_sql(msisdn, "PURCHASE", data["supplier"], data["item"], data["qty"], data["cost"], paid)
        bal = float(data["cost"]) - float(paid)
        
        ussd_response.message = f"Purchase Saved!\nFrom: {data['supplier']}\nYou Owe: N{bal}"
        ussd_response.continueSession = False
        del session_state[session_id]

    # --- DEBT FLOW (30 -> 32) ---
    # ... [Previous code for Sales/Purchases remains the same] ...

    # --- DEBT FLOW (Smart List Version) ---
    elif step == 30:
        if user_data == '1': # Customer Debts (In)
            # 1. Fetch all transactions to calculate balances
            txns = Transaction.query.filter_by(user_phone=msisdn).all()
            
            # 2. Aggregate Balances in Python
            balances = {}
            for t in txns:
                # Filter for Sales-related transactions
                if t.transaction_type in ['SALE', 'DEBT_COLLECTED']:
                    # Math: Price - Paid. 
                    # If Sale: 50k - 30k = +20k (Debt)
                    # If Pay: 0 - 10k = -10k (Reduces Debt)
                    net = t.total_amount - t.amount_paid
                    balances[t.party_name] = balances.get(t.party_name, 0) + net

            # 3. Filter for those who actually owe money (>0)
            debtors = [(name, bal) for name, bal in balances.items() if bal > 0]
            
            if not debtors:
                ussd_response.message = "Good news! No customers owe you money."
                ussd_response.continueSession = False
            else:
                # 4. Generate the List
                msg = "Select Debtor:\n"
                mapping = {}
                for idx, (name, bal) in enumerate(debtors, 1):
                    msg += f"{idx}. {name} (N{bal:,.0f})\n" # Format with commas
                    mapping[str(idx)] = name
                
                # 5. Save the mapping to session so we know '1' is 'Mama T'
                state["debtor_map"] = mapping
                state["step"] = 31 # Next step: Handle selection
                
                ussd_response.message = msg

        elif user_data == '2': # My Debts (Out)
            # Similar logic for Suppliers
            txns = Transaction.query.filter_by(user_phone=msisdn).all()
            balances = {}
            for t in txns:
                if t.transaction_type in ['PURCHASE', 'SUPPLIER_PAYMENT']:
                    net = t.total_amount - t.amount_paid
                    balances[t.party_name] = balances.get(t.party_name, 0) + net
            
            creditors = [(name, bal) for name, bal in balances.items() if bal > 0]
            
            if not creditors:
                ussd_response.message = "You don't owe anyone money."
                ussd_response.continueSession = False
            else:
                msg = "Select Supplier:\n"
                mapping = {}
                for idx, (name, bal) in enumerate(creditors, 1):
                    msg += f"{idx}. {name} (N{bal:,.0f})\n"
                    mapping[str(idx)] = name
                
                state["creditor_map"] = mapping
                state["step"] = 32
                ussd_response.message = msg
    
    # --- HANDLING CUSTOMER SELECTION (Step 31) ---
    elif step == 31:
        selected_index = user_data
        mapping = state.get("debtor_map", {})
        
        if selected_index in mapping:
            selected_name = mapping[selected_index]
            data["party"] = selected_name
            ussd_response.message = f"Enter Amount {selected_name} is paying:"
            state["step"] = 311
        else:
            ussd_response.message = "Invalid selection. Try again."
            ussd_response.continueSession = False

    # --- SAVING CUSTOMER PAYMENT (Step 311) ---
    elif step == 311:
        amount = user_data
        save_transaction_sql(msisdn, "DEBT_COLLECTED", data["party"], "Debt Pay", 0, 0, amount)
        ussd_response.message = f"Saved! {data['party']} paid N{amount}."
        ussd_response.continueSession = False
        del session_state[session_id]

    # --- HANDLING SUPPLIER SELECTION (Step 32) ---
    elif step == 32:
        selected_index = user_data
        mapping = state.get("creditor_map", {})
        
        if selected_index in mapping:
            selected_name = mapping[selected_index]
            data["party"] = selected_name
            ussd_response.message = f"Enter Amount you are paying {selected_name}:"
            state["step"] = 321
        else:
            ussd_response.message = "Invalid selection."
            ussd_response.continueSession = False

    # --- SAVING SUPPLIER PAYMENT (Step 321) ---
    elif step == 321:
        amount = user_data
        save_transaction_sql(msisdn, "SUPPLIER_PAYMENT", data["party"], "Debt Pay", 0, 0, amount)
        ussd_response.message = f"Saved! You paid {data['party']} N{amount}."
        ussd_response.continueSession = False
        del session_state[session_id]

    # Save state if session continues
    if ussd_response.continueSession and session_id in session_state:
        session_state[session_id] = state

    return jsonify(vars(ussd_response))


@app.route('/whatsapp', methods=['GET', 'POST'])
def whatsapp_webhook():
    # ---------------------------------------------------------
    # 1. VERIFICATION (Connects your Webhook to Meta)
    # ---------------------------------------------------------
    if request.method == 'GET':
        mode = request.values.get('hub.mode')
        token = request.values.get('hub.verify_token')
        challenge = request.values.get('hub.challenge')
        
        # Ensure VERIFY_TOKEN is defined in your .env or config
        if mode == 'subscribe' and token == os.getenv("VERIFY_TOKEN", "marketcrm_secret"):
            return challenge, 200
        else:
            return 'Forbidden', 403

    # ---------------------------------------------------------
    # 2. HANDLING MESSAGES (Receive -> AI -> DB -> Reply)
    # ---------------------------------------------------------
    #print("WhatsApp Webhook Event Received")
    if request.method == 'POST':
        data = request.get_json()
        #print("Webhook Data:", data)
        # Check if the structure is valid
        if data.get('object'):
            #print("Valid object found in webhook data.")
            try:
                entry = data['entry'][0]
                changes = entry['changes'][0]
                value = changes['value']
                print("Processing WhatsApp message...    1/3")
                if 'messages' in value:
                    msg = value['messages'][0]
                    from_number = msg['from'] 
                    #print(f"Message from {from_number}")
                    print("Processing WhatsApp message...    2/3")
                    if msg['type'] == 'text':
                        user_text = msg['text']['body']
                        print(f"User Text: {user_text}")
                        print("Processing WhatsApp message...    3/3")
                        # --- A. CHECK FOR REPORT REQUEST (NEW ADDITION) ---
                        if "report" in user_text.lower() or "summary" in user_text.lower():
                            # Optional: Send a "thinking" message
                            print("Generating report...")
                            try:
                                print("Sending thinking message...")
                                send_whatsapp_message(from_number, "Gathering your business data... 🧠")
                                print("Sent thinking message.")
                            except Exception as e:
                                print(f"Error sending thinking message: {e}")
                            
                            # Generate Report
                            summary = generate_llama_report(from_number)
                            send_whatsapp_message(from_number, summary)
                            print("Report sent.")
                            
                            return 'EVENT_RECEIVED', 200
                        
                        # --- B. AI PROCESSING (TRANSACTIONS) ---
                        extracted = parse_sales_instruction(user_text)
                        
                        # Handle cases where AI fails or returns None
                        if not extracted:
                            send_whatsapp_message(from_number, "I didn't understand that. Try: 'Sold 2 rice to Rose for 5k'")
                            return 'EVENT_RECEIVED', 200

                        action = extracted.get('action')
                        
                        # --- C. ROUTING LOGIC ---
                        if action in ["SALE", "PURCHASE"]:
                            
                            # 1. Save to Database
                            save_transaction_sql(
                                phone=from_number,
                                t_type=action,
                                party=extracted.get('party_name', 'Unknown'),
                                item=extracted.get('item', 'Item'),
                                qty=extracted.get('qty', 1),
                                total=extracted.get('total_amount', 0),
                                paid=extracted.get('amount_paid', 0)
                            )
                            
                            # 2. Calculate Balance/Debt
                            total_amt = float(extracted.get('total_amount', 0))
                            paid_amt = float(extracted.get('amount_paid', 0))
                            balance = total_amt - paid_amt
                            
                            # 3. Format the Reply
                            if action == "SALE":
                                reply = (f"✅ *Sale Recorded!*\n"
                                         f"Customer: {extracted.get('party_name', 'Customer')}\n"
                                         f"Item: {extracted.get('item')}\n"
                                         f"Amount: N{total_amt:,.2f}\n"
                                         f"Balance Due: N{balance:,.2f}")
                            else:
                                reply = (f"✅ *Purchase Recorded!*\n"
                                         f"Supplier: {extracted.get('party_name', 'Supplier')}\n"
                                         f"Item: {extracted.get('item')}\n"
                                         f"Cost: N{total_amt:,.2f}")
                            
                            # 4. Send Reply
                            send_whatsapp_message(from_number, reply)
                        
                        elif action == "DEBT_PAYMENT":
                            # Future functionality
                            send_whatsapp_message(from_number, "💰 Debt payment recorded (functionality coming soon).")

                        else:
                            # AI returned "UNKNOWN"
                            send_whatsapp_message(from_number, "I didn't quite catch that. Try saying:\n'Sold 2 rice to Tola for 5000'")

            except Exception as e:
                print(f"Error processing webhook: {e}")

        return 'EVENT_RECEIVED', 200
    


if __name__ == '__main__':
    app.run(port=5000, debug=True)