import os
from contextlib import asynccontextmanager
from typing import List, Optional, Any
from datetime import datetime
import pandas as pd
from io import StringIO

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Session, select, create_engine
from starlette.responses import JSONResponse

import time
from models import Lead, Campaign, Message, Setting, Product
import logic

# Configuration
sqlite_file_name = "campaign.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def get_session():
    with Session(engine) as session:
        yield session

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB
    SQLModel.metadata.create_all(engine)
    yield

app = FastAPI(title="Cozhaven Campaign Manager", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- PRODUCT SYNC ---

@app.post("/sync/products")
async def sync_products(session: Session = Depends(get_session)):
    """Reads the Excel file and updates the Product database."""
    file_path = "/home/cognitbotz/campaign/Cozhaven Retail Price list for Imported furniture 1.xlsx"
    try:
        # Load Excel with pandas
        df = pd.read_excel(file_path)
        
        # Mapping Excel to Product Model
        # Columns: SKU, Detail, Sale Price, Color, Website link..., STOCK
        sync_count = 0
        for _, row in df.iterrows():
            sku_val = row.get('SKU')
            if pd.isna(sku_val): continue
            
            sku = str(sku_val).strip()
            detail = str(row.get('Detail', ''))
            price_val = row.get('Sale Price')
            try:
                price = float(price_val) if not pd.isna(price_val) else 0.0
            except:
                price = 0.0
                
            color = str(row.get('Color', ''))
            link = str(row.get('Website link for photos and config and description', ''))
            stock = str(row.get('Stock available', 'In Stock'))
            
            # Use SKU as name if detail is nan or too short
            name = detail[:50] if len(detail) > 2 and detail.lower() != 'nan' else sku
            
            # Clean up 'nan' strings that come from str() conversion
            color = "" if color.lower() == 'nan' else color
            detail = "" if detail.lower() == 'nan' else detail
            link = "" if link.lower() == 'nan' else link
            stock = "Available" if stock.lower() == 'nan' else stock

            # Simple category logic from SKU or Detail
            category = "Living Room"
            if any(k in detail.lower() for k in ["bed", "nightstand", "slumber"]): category = "Bedroom"
            elif any(k in detail.lower() for k in ["dining", "table", "chair"]): category = "Dining Room"

            existing = session.exec(select(Product).where(Product.sku == sku)).first()
            if existing:
                existing.price = price
                existing.detail = detail
                existing.color = color
                existing.link = link
                existing.stock = stock
                existing.name = name
            else:
                product = Product(
                    sku=sku,
                    name=name,
                    category=category,
                    price=price,
                    color=color,
                    detail=detail,
                    link=link,
                    stock=stock
                )
                session.add(product)
            sync_count += 1
            
        session.commit()
        return {"message": f"Synced {sync_count} products from Cozhaven pricing list"}
    except Exception as e:
        print(f"Sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products", response_model=List[Product])
def get_products(session: Session = Depends(get_session)):
    return session.exec(select(Product)).all()

# --- LEAD SYNC (DATA SCIENTIST APPROACH) ---

def clean_phone(val: Any) -> Optional[str]:
    """Helper to clean phone numbers from floats/strings to E.164."""
    if pd.isna(val): return None
    # Convert to string, remove .0 if it's from float
    s = str(val).split('.')[0]
    # Remove all non-numeric characters
    cleaned = "".join(filter(str.isdigit, s))
    if not cleaned: return None
    # If 10 digits, assume North America and add +1
    if len(cleaned) == 10: return f"+1{cleaned}"
    # If starts with 1, just add +
    if cleaned.startswith('1') and len(cleaned) == 11: return f"+{cleaned}"
    # If longer and doesn't have +, add +
    return f"+{cleaned}"

@app.post("/sync/leads")
async def sync_leads(session: Session = Depends(get_session)):
    """Consolidates leads from multiple CSV sources with a high-recall strategy."""
    sources = [
        {"path": "/home/cognitbotz/campaign/Cozhaven Leads.csv", "name": "CozaLeads", "header": 0},
        {"path": "/home/cognitbotz/campaign/Customer list CZ.csv", "name": "CustomerCZ", "header": None}
    ]
    
    # Optional: Clear leads to prevent confusion during testing
    # session.exec(delete(Lead)) 
    
    total_added = 0
    total_processed = 0
    
    for src in sources:
        try:
            df = pd.read_csv(src["path"], header=src["header"])
            for _, row in df.iterrows():
                total_processed += 1
                name = "Visitor"
                phone_raw = None
                email = None
                label = None
                
                if src["name"] == "CozaLeads":
                    name = str(row.get('Name', row.get('First Name', 'Visitor'))).strip()
                    phone_raw = row.get('Phone', row.get('Mobile Phone', row.get('Other Phone')))
                    email = str(row.get('Email address', '')).strip()
                    label = str(row.get('Labels', ''))
                else: # CustomerCZ - headerless search
                    # column 0 is usually name
                    name = str(row[0]).strip() if pd.notna(row[0]) else "Visitor"
                    # Search all columns for something that looks like a phone
                    for col_idx in range(len(row)):
                        val = str(row[col_idx])
                        # If contains at least 7 digits, treat as phone candidate
                        if sum(c.isdigit() for c in val) >= 7:
                            phone_raw = val
                            break
                    # label/notes might be in other columns
                    label = str(row[1]) if len(row) > 1 and pd.notna(row[1]) else None

                phone = clean_phone(phone_raw)
                if not phone or name.lower() == 'nan': continue
                
                # Check for duplicates
                existing = session.exec(select(Lead).where(Lead.phone_number == phone)).first()
                if not existing:
                    lead = Lead(
                        first_name=name[:100], # Allow longer names for messy CSVs
                        phone_number=phone,
                        email=email if email and '@' in email else None,
                        label=label if label and label.lower() != 'nan' else None,
                        area="Ontario"
                    )
                    session.add(lead)
                    total_added += 1
            session.commit()
        except Exception as e:
            print(f"Error processing {src['name']}: {e}")
            import traceback
            traceback.print_exc()
            
    return {
        "metadata": {
            "processed": total_processed,
            "added": total_added,
            "sources": [s["name"] for s in sources]
        },
        "message": f"Data Science Sync Complete: Added {total_added} new leads."
    }

# --- LEAD MANAGEMENT ---

@app.post("/leads/import")
async def import_leads(file: UploadFile = File(...), session: Session = Depends(get_session)):
    content = await file.read()
    df = pd.read_csv(StringIO(content.decode('utf-8')), dtype=str)
    
    # Required columns: first_name, phone_number
    required_cols = ['first_name', 'phone_number']
    if not all(col in df.columns for col in required_cols):
        raise HTTPException(status_code=400, detail="CSV must contain first_name and phone_number")
    
    new_leads_count = 0
    for _, row in df.iterrows():
        # Basic validation: ensure phone starts with +
        phone = str(row['phone_number']).strip()
        if not phone.startswith('+'):
            # Assume local and add +1 for Canada
            phone = f"+1{phone}"
        else:
            # It already has a +, so leave it as is (e.g., +91)
            pass
            
        # Check if lead exists
        existing = session.exec(select(Lead).where(Lead.phone_number == phone)).first()
        if not existing:
            lead = Lead(
                first_name=row['first_name'],
                phone_number=phone,
                area=row.get('area'),
                previous_interest=row.get('previous_interest')
            )
            session.add(lead)
            new_leads_count += 1
            
    session.commit()
    return {"message": f"Successfully imported {new_leads_count} new leads"}

@app.get("/leads", response_model=List[Lead])
def get_leads(session: Session = Depends(get_session)):
    return session.exec(select(Lead)).all()

# --- MESSAGING & WEBHOOKS ---

@app.post("/webhook/twilio")
async def twilio_webhook(request: Request, session: Session = Depends(get_session)):
    """Receives incoming SMS from Twilio and auto-responds."""
    form_data = await request.form()
    from_number = form_data.get("From")
    body = form_data.get("Body")
    
    # 1. Store incoming message
    lead = session.exec(select(Lead).where(Lead.phone_number == from_number)).first()
    if not lead:
        # Create mystery lead if missing
        lead = Lead(first_name="Visitor", phone_number=from_number)
        session.add(lead)
        session.commit()
        session.refresh(lead)
        
    # 2. Search for relevant products if they ask about items
    # Simple search: find products that may match keywords in the body
    matching_products = []
    keywords = body.lower().split()
    if len(keywords) > 1:
        for k in keywords:
            if len(k) < 4: continue
            prods = session.exec(select(Product).where(Product.detail.contains(k))).all()
            matching_products.extend(prods[:2])
            
    products_context = "\n".join([f"- {p.sku}: {p.name} (${p.price})" for p in matching_products[:5]])
    
    # 3. Classify Intent
    intent = logic.classify_intent(body, products_context)
    
    incoming_msg = Message(
        lead_id=lead.id,
        content=body,
        direction="inbound",
        status="received",
        intent=intent
    )
    session.add(incoming_msg)
    
    # 4. Generate response
    response_text = logic.get_response_for_intent(intent, products_context)
    
    # 5. Send via Twilio
    sid = logic.send_sms(from_number, response_text)
    
    outbound_msg = Message(
        lead_id=lead.id,
        content=response_text,
        direction="outbound",
        status="sent" if sid else "failed",
        twilio_sid=sid
    )
    session.add(outbound_msg)
    
    session.commit()
    return {"status": "ok"}

def process_campaign_sending(campaign_id: int):
    """Background task to send messages with rate limiting."""
    with Session(engine) as session:
        campaign = session.get(Campaign, campaign_id)
        if not campaign:
            return
            
        leads = session.exec(select(Lead)).all()
        for lead in leads:
            # Personalization
            msg_text = campaign.template.replace("{{FirstName}}", lead.first_name)
            
            # Send
            sid = logic.send_sms(lead.phone_number, msg_text)
            
            # Log
            message = Message(
                lead_id=lead.id,
                campaign_id=campaign.id,
                content=msg_text,
                direction="outbound",
                status="sent" if sid else "failed",
                twilio_sid=sid
            )
            session.add(message)
            session.commit() # Commit each to show progress in dashboard
            
            # Batching/Throttling: PRD says 50-70/hour (~1 message per minute)
            # For testing purposes, we'll use a shorter 2-second delay
            time.sleep(2) 
            
        campaign.status = "completed"
        session.add(campaign)
        session.commit()

@app.post("/campaigns/{campaign_id}/send")
def send_campaign(campaign_id: int, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    """Triggers the actual SMS sending for all leads in system."""
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    campaign.status = "active"
    session.add(campaign)
    session.commit()
    
    background_tasks.add_task(process_campaign_sending, campaign_id)
    return {"message": f"Campaign {campaign_id} started in background"}

@app.post("/leads/{lead_id}/send_test")
def send_test_message(lead_id: int, template: str = Form(...), session: Session = Depends(get_session)):
    """Sends a one-off test message to a specific lead."""
    lead = session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    msg_text = template.replace("{{FirstName}}", lead.first_name)
    sid = logic.send_sms(lead.phone_number, msg_text)
    
    message = Message(
        lead_id=lead.id,
        content=msg_text,
        direction="outbound",
        status="sent" if sid else "failed",
        twilio_sid=sid
    )
    session.add(message)
    session.commit()
    return {"message": f"Test message sent to {lead.phone_number}", "sid": sid}

# --- CAMPAIGN MANAGEMENT ---

@app.post("/campaigns")
def create_campaign(campaign: Campaign, session: Session = Depends(get_session)):
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign

@app.get("/campaigns", response_model=List[Campaign])
def list_campaigns(session: Session = Depends(get_session)):
    return session.exec(select(Campaign)).all()

# --- ANALYTICS ---

@app.get("/stats")
def get_stats(session: Session = Depends(get_session)):
    total_leads = len(session.exec(select(Lead)).all())
    messages_sent = len(session.exec(select(Message).where(Message.direction == "outbound")).all())
    replies = len(session.exec(select(Message).where(Message.direction == "inbound")).all())
    total_products = len(session.exec(select(Product)).all())
    
    # Intent breakdown
    intents = session.exec(select(Message.intent)).all()
    intent_counts = {}
    for intent in intents:
        if intent:
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
            
    return {
        "total_leads": total_leads,
        "total_products": total_products,
        "messages_sent": messages_sent,
        "reply_rate": (replies / messages_sent if messages_sent > 0 else 0) * 100,
        "intents": intent_counts
    }

@app.get("/messages", response_model=List[Message])
def get_messages(session: Session = Depends(get_session)):
    return session.exec(select(Message).order_by(Message.created_at.desc())).all()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
