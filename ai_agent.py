from groq import Groq
from models import Transaction
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Groq with your key
# Best practice: Store this in an environment variable or config file
client = Groq()

def generate_llama_report(user_phone):
    """
    1. Fetches today's transactions for the user.
    2. Sends them to Llama 3.
    3. Returns a short, smart summary.
    """
    
    # 1. Fetch Data (e.g., last 10 transactions or today's sales)
    # You might want to filter by date in a real app
    txns = Transaction.query.filter_by(user_phone=user_phone)\
        .order_by(Transaction.id.desc())\
        .limit(10).all()
    
    if not txns:
        return "You have no transactions to analyze yet."

    # 2. Format Data for the AI
    # Llama needs text, so we convert the database rows into a readable string
    data_str = "Transaction List:\n"
    for t in txns:
        data_str += f"- {t.transaction_type}: {t.item_name} (Qty: {t.quantity}) for N{t.total_amount}. Paid: N{t.amount_paid}.\n"

    # 3. The Prompt (Instructions for Llama)
    system_instruction = """
    You are a helpful business assistant for a Nigerian market trader.
    Analyze the provided transaction list.
    Write a SHORT summary (under 50 words).
    1. Total Sales Amount.
    2. Who owes money (Debtors).
    3. Give one piece of business advice based on the items sold.
    4. Anything else useful.
    Use simple English and mix pidgin english.
    """

    # 4. Call Llama 3
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", # The Meta Llama 3 model
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": data_str}
            ],
            temperature=0.5,
            max_tokens=200,
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Llama Error: {e}")
        return "Sorry, my brain is tired. I couldn't generate the report."