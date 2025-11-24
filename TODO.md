# Muay Thai Competition Pairing Service - Project Plan

## ✅ Phase 1: Project Initialization & Structure (COMPLETED)
- [x] **Repo Setup**
    - [x] Initialize git repository.
    - [x] Create `.gitignore` (Python, Streamlit, Excel/PDF artifacts).
    - [x] Create `requirements.txt` (Key libs: `streamlit`, `pandas`, `openpyxl`, `fpdf` or `reportlab`, `altair` for stats).
- [x] **Environment**
    - [x] Set up virtual environment (`venv` or `poetry`).
    - [x] Configure Streamlit secrets (if auth/passwords are needed later).

## ✅ Phase 2: Data Ingestion & Validation (COMPLETED)
- [x] **Excel Template Definition**
    - [x] Define strict column headers for input file:
        - `Name` (used instead of Full Name)
        - `Gender` (M/F)
        - `Age` (numeric)
        - `Weight` (kg)
        - `Club`
        - `Trainer`
        - `Record` (Experience/Record as numeric)
- [x] **Streamlit Uploader**
    - [x] Implement `st.file_uploader` restricted to `.xlsx`.
    - [x] **Validation Logic**:
        - [x] Check for missing columns.
        - [x] Convert `Weight` and `Age` to numeric types (handle typos).
        - [x] Standardize `Gender` values (e.g., "Male", "m", "M" -> "M").
        - [x] Display specific error messages if data is malformed.

## ✅ Phase 3: Core Pairing Logic (The Brain) (COMPLETED)
*Goal: Automate 90% of the work, leave 10% for manual review.*
- [x] **Pre-Processing**
    - [x] Calculate specific Age (handled in validation).
    - [x] Assign **Weight Class** bucket (simplified IFMA-like classes).
- [x] **Matching Algorithm**
    - [x] **Hard Filters** (Cannot be violated):
        - [x] `Gender` must match.
        - [x] `Club` must be different (avoid teammate matchups).
        - [x] `Trainer` must be different (implemented).
    - [x] **Soft Filters** (Scoring System):
        - [x] **Weight Delta**: Penalty increases as difference grows (implemented with scoring).
        - [x] **Age Delta**: Penalty for gaps > 2 years (critical for Juniors).
        - [x] **Experience**: Penalty for mismatch (based on Record).
    - [x] **Greedy Matching Loop**:
        1.  Group fighters by Gender & Weight Class.
        2.  Sort by Experience/Record.
        3.  Attempt to pair top 2 available; if constraints fail, try next.
        4.  Move unmatched fighters to "Unmatched/Leftovers" pool.
- [x] **Conflict Resolution**
    - [x] Flag matches with high safety risks (warnings for age/weight diffs).

## ✅ Phase 4: UI/UX & Manual Redaction (COMPLETED)
- [x] **Dashboard Layout**
    - [x] Sidebar: Language selector, configuration options.
    - [x] Main Area: Tabs ("Data Upload", "Generate Pairs", "Manual Adjustments", "Export").
- [x] **Manual Redaction (Streamlit `data_editor`)**
    - [x] Display generated pairs in an editable dataframe (`st.data_editor`).
    - [x] Editable table for manual changes.
    - [x] Unmatched fighters displayed separately.
    - [x] **Session State Management**:
        - [x] Ensure pairs persist when user interacts with other widgets.
        - [x] Save `st.session_state['matches']` after every edit.

## ✅ Phase 5: Reporting & Export (COMPLETED)
- [x] **Statistics Panel**
    - [x] Show total fighters, total matches, gender distribution.
    - [x] Show number of clubs represented.
- [x] **Export Modules**
    - [x] **Excel Export**:
        - [x] Generate `.xlsx` with match details and summary sheet.
    - [x] **PDF Export (Bout Sheet)**:
        - [x] Create professional layout using `fpdf`.
        - [x] Header: Competition Name.
        - [x] Bout details with Red/Blue corners.
        - [x] Signatures section.

## ✅ Phase 6: Testing & Deployment (COMPLETED)
- [x] **Unit Tests**
    - [x] Test: Does the algorithm separate Genders correctly?
    - [x] Test: Does the algorithm prevent Same-Gym matchups?
    - [x] Test: Does the algorithm handle odd numbers of fighters (leave one out)?
- [x] **Deployment (Docker)**
    - [x] Create `Dockerfile` (Python 3.11-slim).
    - [x] Expose port 8501.
    - [x] Add `HEALTHCHECK`.

## ✅ Additional Features Implemented
- [x] **Internationalization**: Full Russian translation support with language selector.
- [x] **Weight Variance Warning**: Warnings for high weight/age differences.
- [x] **Git Branch Management**: Default branch set to 'main', pushed to remote.
- [x] **Modular Code Structure**: Separate files for pairing, data loading, PDF generation.

## Status: 🎉 PROJECT COMPLETED
All core features implemented and tested. The Muay Thai Matchmaker is ready for production use!
