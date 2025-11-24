# Muay Thai Competition Pairing Service - Project Plan

## Phase 1: Project Initialization & Structure
- [ ] **Repo Setup**
    - [ ] Initialize git repository.
    - [ ] Create `.gitignore` (Python, Streamlit, Excel/PDF artifacts).
    - [ ] Create `requirements.txt` (Key libs: `streamlit`, `pandas`, `openpyxl`, `fpdf` or `reportlab`, `altair` for stats).
- [ ] **Environment**
    - [ ] Set up virtual environment (`venv` or `poetry`).
    - [ ] Configure Streamlit secrets (if auth/passwords are needed later).

## Phase 2: Data Ingestion & Validation
- [ ] **Excel Template Definition**
    - [ ] Define strict column headers for input file:
        - `Full Name`
        - `Gender` (M/F)
        - `Age` (or DOB for auto-calc)
        - `Weight` (kg)
        - `Club/Gym`
        - `Trainer`
        - `Experience/Record` (Number of fights or Class A/B/C)
- [ ] **Streamlit Uploader**
    - [ ] Implement `st.file_uploader` restricted to `.xlsx`.
    - [ ] **Validation Logic**:
        - [ ] Check for missing columns.
        - [ ] Convert `Weight` and `Age` to numeric types (handle typos).
        - [ ] Standardize `Gender` values (e.g., "Male", "m", "M" -> "M").
        - [ ] Display specific error messages if data is malformed.

## Phase 3: Core Pairing Logic (The Brain)
*Goal: Automate 90% of the work, leave 10% for manual review.*
- [ ] **Pre-Processing**
    - [ ] Calculate specific Age (if DOB provided).
    - [ ] Assign **Weight Class** bucket (e.g., IFMA standard: <57kg, <60kg, etc.) based on input weight.
- [ ] **Matching Algorithm**
    - [ ] **Hard Filters** (Cannot be violated):
        - [ ] `Gender` must match.
        - [ ] `Club` must be different (avoid teammate matchups).
        - [ ] `Trainer` must be different (optional, strict mode).
    - [ ] **Soft Filters** (Scoring System):
        - [ ] **Weight Delta**: Penalty increases as difference grows (e.g., >2kg difference = High Penalty).
        - [ ] **Age Delta**: Penalty for gaps > 2 years (critical for Juniors).
        - [ ] **Experience**: Penalty for mismatch (e.g., 0 fights vs 10 fights).
    - [ ] **Greedy Matching Loop**:
        1.  Group fighters by Gender & Weight Class.
        2.  Sort by Experience/Record.
        3.  Attempt to pair top 2 available; if constraints (Same Gym) fail, try next available.
        4.  Move unmatched fighters to a "Unmatched/Leftovers" pool.
- [ ] **Conflict Resolution**
    - [ ] Flag matches with high safety risks (e.g., Age gap > 3 years) with a warning icon ⚠️.

## Phase 4: UI/UX & Manual Redaction
- [ ] **Dashboard Layout**
    - [ ] Sidebar: File Upload, Configuration (Max weight diff allowed, Max age gap allowed).
    - [ ] Main Area: Tabs ("Data View", "Auto-Generated Pairs", "Manual Adjustments", "Export").
- [ ] **Manual Redaction (Streamlit `data_editor`)**
    - [ ] Display generated pairs in an editable dataframe (`st.data_editor`).
    - [ ] **Drag-and-Drop / ID Swap**:
        - [ ] Allow user to change `Opponent_ID` manually.
        - [ ] **Or better**: Two-column layout with "Red Corner" and "Blue Corner" dropdowns for manual fights.
    - [ ] **"Leftovers" Section**:
        - [ ] Clearly display fighters who were NOT paired.
        - [ ] Allow manual addition of these fighters into new bouts.
    - [ ] **Session State Management**:
        - [ ] Ensure pairs persist when user interacts with other widgets (crucial in Streamlit).
        - [ ] Save `st.session_state['pairs']` after every edit.

## Phase 5: Reporting & Export
- [ ] **Statistics Panel**
    - [ ] Show total fighters, total matches, gender distribution.
    - [ ] Show number of clubs represented.
- [ ] **Export Modules**
    - [ ] **Excel Export**:
        - [ ] Generate `.xlsx` with columns: `Match #`, `Red Corner`, `Red Club`, `Red Weight`, `Blue Corner`, `Blue Club`, `Blue Weight`.
    - [ ] **PDF Export (Bout Sheet)**:
        - [ ] Create professional layout using `fpdf`.
        - [ ] Header: Competition Name, Date.
        - [ ] Table: List of bouts (Red vs Blue).
        - [ ] Footer: Signatures for Officials.
        - [ ] *Bonus*: Individual "Bout Cards" (1 page per fight for judges).

## Phase 6: Testing & Deployment
- [ ] **Unit Tests**
    - [ ] Test: Does the algorithm separate Genders correctly?
    - [ ] Test: Does the algorithm prevent Same-Gym matchups?
    - [ ] Test: Does the algorithm handle odd numbers of fighters (leave one out)?
- [ ] **Deployment (Docker)**
    - [ ] Create `Dockerfile` (Python 3.11-slim).
    - [ ] Expose port 8501.
    - [ ] Add `HEALTHCHECK`.

## Missing/Bonus Features (Added for completeness)
- [ ] **Weight Variance Warning**: Highlight rows where the weight difference is > X kg in Red.
- [ ] **Round Robin Support**: Toggle for "Tournament Mode" (Bracket) vs "Gala Mode" (Single Match).
- [ ] **Corner Randomization**: Randomly assign Red/Blue corner so one gym isn't always Red.
- [ ] **Medical Suspensions**: Column in input for "Medical Clearance" (boolean) - filter out `False` immediately.
