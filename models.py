from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship

# --- TRANSITIONS (THE MOVEMENTS) ---
class ElementTransition(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships
    # These link the transition to a specific Cue and a specific Element
    cue_id: int = Field(foreign_key="cue.id", nullable=False)
    element_id: int = Field(foreign_key="stageelement.id", nullable=False)
    
    target_state: str # e.g. "In", "Out", "SR Wing", "CS"

    # Back Populates allow us to traverse the relationship in reverse
    cue: "Cue" = Relationship(back_populates="transitions")
    element: "StageElement" = Relationship(back_populates="transitions")
    
# --- INVENTORY (THE OBJECTS) ---
class StageElement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    show_id: int = Field(foreign_key="show.id")
    
    name: str
    category: str # "Deck", "Fly", "Prop", "Actor"
    default_state: str # Default "Home" position

    # Parent Relationship
    show: "Show" = Relationship(back_populates="stage_elements")
    
    # Children Relationship (FIXED WITH CASCADE)
    # If this Element is deleted, delete all associated transitions
    transitions: List[ElementTransition] = Relationship(
        back_populates="element", 
        sa_relationship_kwargs={"cascade": "all, delete-orphan"} 
    )

# --- CUES ---
class Cue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    show_id: int = Field(foreign_key="show.id")
    
    sequence: int # 1, 2, 3... (Auto-calculated ordering)
    number: str   # "1", "1.5", "A", "25"
    description: str
    department: str # "Lights", "Sound", "Deck", "Auto"
    trigger: Optional[str] = None
    page_num: Optional[str] = None
    
    is_active: bool = Field(default=False) 

    # Parent Relationship
    show: "Show" = Relationship(back_populates="cues")

    # Children Relationship (FIXED WITH CASCADE)
    # If this Cue is deleted, delete all associated transitions
    transitions: List[ElementTransition] = Relationship(
        back_populates="cue", 
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    
# --- SHOW ---
class Show(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    status: str = Field(default="pre") # "pre", "running", "post"

    # Children Relationships (FIXED WITH CASCADE)
    # If Show is deleted, delete all Cues and Elements
    cues: List[Cue] = Relationship(
        back_populates="show",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    stage_elements: List[StageElement] = Relationship(
        back_populates="show",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )