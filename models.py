from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship

class Show(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    # NEW: Tracks "pre", "running", or "post"
    status: str = Field(default="pre") 
    cues: List["Cue"] = Relationship(back_populates="show")

class Cue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sequence: int = Field(default=0, index=True)
    number: str
    trigger: Optional[str] = Field(default=None)   
    page_num: Optional[str] = Field(default=None)
    description: str
    department: str
    is_active: bool = Field(default=False)
    show_id: Optional[int] = Field(default=None, foreign_key="show.id")
    show: Optional[Show] = Relationship(back_populates="cues")