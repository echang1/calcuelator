# CalCUElator

A simple web-based tool built to reduce the manual overhead of logistical organization for stage managers. 

This project was created to move beyond static paper cue sheets, providing a digital workspace to dynamically manage cue sequences, track show progress, and organize production data.

Currently in active development.

## Current Functionality

* **Cue Management:** Easily create, edit, and execute cues for your show.
* **Stage Elements:** Track the positions and movements of set pieces, props, drops, and curtains.
* **Multi-Show Support:** Store and manage cues for multiple shows at the same time.

## Quickstart

This project is a FastAPI application. To run it locally, ensure you have a Python 3.10+ environment ready.

1. **Clone the repository:**
    ```bash
    git clone https://github.com/echang1/calcuelator.git
    cd calcuelator
    ```

2. **Setup Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3. **Run the Developoment Server:**
    ```bash
    uvicorn main:app --reload
    ```
    The interface will be accessible at `http://localhost:8000`.

## Usage Guide

Once the server is running, the workflow is centered around show-specific cue lists:

* **Show Setup:** From the main "Lobby" view, create a new show to initialize a dedicated cue sequence.
* **Cue Entry:** Within a show, use the entry form to add cues. Cues can be reordered by dragging rows; the sequence is updated automatically in the database.
* **Live Operation:** * Click **GO** on a row to set it as the active cue.
    * Use the **Spacebar** or **RightArrow** to advance (**LeftArrow** to go back) through the sequence or trigger the end-of-show reset after the final cue.
    * Press **H** to activate the HUD _(Defaults to view level 0: Command Mode)_.
    * Use **UpArrow** and **DownArrow** to cycle between view levels _(Currently available: 0 = Command, 1 = Spatial)_.
    * The **Reset** button will clear all active states without deleting the cue data _(Press **CTRL+R** to reset from any screen)_.
* **Stage Elements:** Open the "Stage Inventory" to create new Stage Elements.
* **Modifications:** Use the inline edit (✏️) to modify existing cues, the delete (🗑️) button to remove them, or the movement (📦) button to add Stage Element transitions.


## Changelog

### v0.2.1
**Spatial View**
* Added Stage Elements to track the position and movement of set pieces, props, drops, and curtains.
* Added Spatial View to HUD Mode: Use `UpArrow` and `DownArrow` to switch between HUD view levels: `0 = Command, 1 = Spatial`. 

### v0.2.0
**Command Console**
* Implemented HUD Mode: Press `H` to toggle a full-screen, high-contrast overlay designed for keyboard navigation during live performances.
* Added Cue columns for _Trigger_, the specific action/line that initiates the cue, and _Page Num_, the associated script page.

### v0.1.0
**Initial Release** 
* Established the core sequencing engine with support for multi-show relational data.
* Implemented interactive show execution and drag-and-drop reordering.