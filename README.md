# CalCUElator

A simple web-based tool built to reduce the manual overhead of logistical organization for stage managers. 

This project was created to move beyond static paper cue sheets, providing a digital workspace to dynamically manage cue sequences, track show progress, and organize production data.

Currently in active development.

## Current Functionality

* **Cue Management:** Easily create, edit, and execute cues for your show.
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
    * Use the **Spacebar** to advance through the sequence or trigger the end-of-show reset after the final cue.
    * The **Reset** button will clear all active states without deleting the cue data.
* **Modifications:** Use the inline edit (✏️) to modify existing cues or the delete (🗑️) button to remove them.

## Changelog

### v0.1.0
* **Initial Release:** 
    * Established the core sequencing engine with support for multi-show relational data.
    * Implemented interactive show execution and drag-and-drop reordering.