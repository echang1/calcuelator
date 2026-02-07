from typing import Optional
from sqlmodel import Field, SQLModel

class Cue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sequence: int = Field(default=0, index=True)    # For Cue Ordering
    number: str           # e.g., "1", "1.5", "A"
    description: str      # e.g., "House to Half", "Blackout"
    department: str       # "Lights", "Sound", "Deck"
    is_active: bool = Field(default=False)
    
    # We will add status later, keeping it simple for now!