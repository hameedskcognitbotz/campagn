import os
from typing import Dict, Any, Optional
from groq import Groq
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

# Initialize Groq client
api_key = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=api_key) if api_key else None

# Initialize Twilio client
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_client = Client(account_sid, auth_token) if account_sid and auth_token else None
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
TWILIO_SENDER_ID = os.getenv("TWILIO_SENDER_ID") # e.g. "BudgetStr"

# Business Details from Excel
STORE_HOURS = "Saturday and Sunday: 12pm to 9pm, Monday to Friday: 12pm to 8pm"
STORE_SPECIALTY = "Imported premium furniture: Sectional sofas, Dining sets, Bedroom furniture."

# Business Context from PRD
INTENT_MAPPING = {
    "location": os.getenv("MAPS_URL", "https://goo.gl/maps/mississauga"),
    "financing": os.getenv("FINANCING_URL", "https://example.com/financing"),
    "price": "We offer sectionals from $499, sofas from $299. Visit us to see our full Spring range!",
    "interested": f"Great! Visit us at {os.getenv('STORE_ADDRESS', 'Mississauga Store')}. Show this SMS for an extra 5% off! 🗺️ {os.getenv('MAPS_URL', '')}",
    "not_interested": "No problem! We've updated your preferences. Have a great day."
}

def classify_intent(message_text: str, products_context: str = "") -> str:
    """Classify the user intent using Groq with product context."""
    if not groq_client:
        return "interested"
        
    prompt = f"""
    You are a concierge for Cozhaven, a premium furniture store in Mississauga.
    Store hours: {STORE_HOURS}.
    Store Specialty: {STORE_SPECIALTY}.
    
    Current available products and samples:
    {products_context}

    Classify this customer SMS into ONE: 
    'location', 'financing', 'price', 'interested', 'not_interested'.
    
    Message: "{message_text}"
    
    Return ONLY the string of the intent category.
    """
    
    try:
        completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
            temperature=0,
        )
        intent = completion.choices[0].message.content.strip().lower()
        if intent in INTENT_MAPPING:
            return intent
        return "interested" # Default
    except Exception as e:
        print(f"Groq API Error: {e}")
        return "interested"

def get_response_for_intent(intent: str, products_match: str = "") -> str:
    """Return the response based on intent and optional product matches."""
    if intent == 'price' and products_match:
        return f"We have several options matching your request:\n{products_match}\nVisit us to see them in person!"
    return INTENT_MAPPING.get(intent, INTENT_MAPPING["interested"])

def send_sms(to_number: str, message_text: str) -> Optional[str]:
    """Send an SMS via Twilio and return the SID."""
    if not twilio_client:
        print(f"Twilio not configured. Would have sent: {message_text}")
        return "mock_sid"
    try:
        # Use Sender ID if target is NOT India (+91), as India requires strict registration
        # Otherwise use the validated Twilio Phone Number
        from_val = TWILIO_PHONE_NUMBER
        if TWILIO_SENDER_ID and not to_number.startswith("+91"):
            from_val = TWILIO_SENDER_ID
            
        message = twilio_client.messages.create(
            body=message_text,
            from_=from_val,
            to=to_number
        )
        return message.sid
    except Exception as e:
        print(f"Twilio Error sending to {to_number}: {e}")
        return None
