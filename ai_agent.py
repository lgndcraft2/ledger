from groq import Groq
from models import Transaction
import os
from dotenv import load_dotenv
import json


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Groq with your key
# Best practice: Store this in an environment variable or config file
client = Groq()

def transcribe_audio(audio_file_path):
    """
    Takes a local audio file path, sends it to Groq (Whisper),
    and returns the transcribed text.
    """
    try:
        with open(audio_file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(audio_file_path, file.read()),
                model="whisper-large-v3", # The best model for mixed accents
                response_format="text",   # Just give us the string
                temperature=0.0           # Keep it accurate
            )
        return transcription
    except Exception as e:
        print(f"Transcription Error: {e}")
        return None

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
    

def parse_sales_instruction(user_text):
    """
    Takes natural text: "Sold 2 Rice to Rose for 5k"
    Returns JSON: {"action": "SALE", "item": "Rice", "qty": 2, "price": 5000, "paid": 5000}
    """
    
    system_prompt = """
    You are a Data Extraction Agent. Convert the user's message into a JSON Object.
    
    Rules:
    1. Identify the ACTION: "SALE", "PURCHASE", "DEBT_PAYMENT", or "UNKNOWN".
    2. Extract: item_name, quantity, total_amount, amount_paid, party_name (customer/supplier).
    3. If 'amount_paid' is not mentioned, assume it equals 'total_amount' (Full payment).
    4. If 'quantity' is missing, assume 1.
    5. Return ONLY JSON. No explanation.
    
    Example Input: "Sold 3 yams to Paul for 3000 but he paid 1000"
    Example JSON: {"action": "SALE", "item": "yams", "qty": 3, "total_amount": 3000, "amount_paid": 1000, "party_name": "Paul"}
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            temperature=0, # Keep it strict
            response_format={"type": "json_object"} # Force JSON output
        )
        print(completion.choices[0].message.content)
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"AI Parse Error: {e}")
        return None