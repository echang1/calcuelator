from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship

class Show(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    
    # A Show has many Cues (This is for the code to understand the link)
    cues: List["Cue"] = Relationship(back_populates="show")

class Cue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sequence: int = Field(default=0, index=True)
    number: str
    description: str
    department: str
    is_active: bool = Field(default=False)
    
    # NEW: Link every cue to a specific Show ID
    show_id: Optional[int] = Field(default=None, foreign_key="show.id")
    show: Optional[Show] = Relationship(back_populates="cues")