from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class Lead(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str
    phone_number: str = Field(index=True, unique=True)
    email: Optional[str] = None
    area: Optional[str] = None
    previous_interest: Optional[str] = None
    label: Optional[str] = None
    consent_status: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    messages: List["Message"] = Relationship(back_populates="lead")

class Campaign(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    status: str = Field(default="scheduled") # scheduled, active, paused, completed
    template: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    scheduled_at: Optional[datetime] = None
    
    messages: List["Message"] = Relationship(back_populates="campaign")

class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lead_id: int = Field(foreign_key="lead.id")
    campaign_id: Optional[int] = Field(default=None, foreign_key="campaign.id")
    content: str
    direction: str # inbound, outbound
    status: str = Field(default="sent") # sent, delivered, failed, received
    intent: Optional[str] = None # location, financing, price, interested, not_interested
    created_at: datetime = Field(default_factory=datetime.utcnow)
    twilio_sid: Optional[str] = None
    
    lead: Lead = Relationship(back_populates="messages")
    campaign: Optional[Campaign] = Relationship(back_populates="messages")

class Setting(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(unique=True)
    value: str

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sku: str = Field(index=True, unique=True)
    category: str = Field(index=True)
    name: str
    price: float
    color: Optional[str] = None
    detail: Optional[str] = None
    link: Optional[str] = None
    stock: Optional[str] = None
