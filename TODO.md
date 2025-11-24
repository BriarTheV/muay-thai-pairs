# Muay Thai Matchmaker - Master Project Plan 🥊

## ✅ COMPLETED FEATURES (Current Implementation)
- [x] **Basic File Upload & Validation**: Excel upload with column checking, type conversion, gender standardization
- [x] **Core Pairing Algorithm**: Greedy matching with hard filters (gender, club), soft scoring (weight/age/experience)
- [x] **Manual Match Editing**: `st.data_editor` for adjusting generated pairs
- [x] **Export Functionality**: PDF bout sheets and Excel match lists
- [x] **UI/UX**: Tabbed interface, statistics display, warnings for high diffs
- [x] **Internationalization**: Full Russian translation support
- [x] **Docker Deployment**: Containerized app with health checks
- [x] **Testing**: Unit tests for pairing logic
- [x] **Git Management**: Proper branching and remote setup

## 🚧 MISSING FEATURES (Advanced Platform)

## Phase 1: Infrastructure & Security (The Foundation) ✅ *COMPLETED*
- [x] **Repo & Environment**
    - [x] Initialize Git repo (`.gitignore` for Python/Secrets).
    - [x] Create `requirements.txt` (Add `supabase`, `st-gsheets-connection`).
    - [x] Create `.streamlit/secrets.toml` template.
- [x] **Supabase Setup (Database & Auth)**
    - [ ] Create Supabase Project.
    - [ ] **Auth**: Enable "Email/Password" provider.
    - [ ] **Database**: Get Connection String (URI) and API Keys.
    - [ ] Add credentials to `secrets.toml`.
- [x] **Google Cloud Setup**
    - [ ] Enable Google Sheets API.
    - [ ] Create Service Account & Download JSON key.
    - [ ] Add JSON content to `secrets.toml`.
- [x] **App Authentication Layer**
    - [x] Create `utils/auth.py`.
    - [x] Build Login Screen (Email/Pass) using `supabase.auth`.
    - [x] Implement Session State check (`if not st.session_state.user: show_login()`).

## Phase 2: Database Schema & Roster Management ✅ *COMPLETED*
- [x] **Schema Design (PostgreSQL/Supabase)**
    - [x] Table: `clubs` (id, name, contact_info).
    - [x] Table: `fighters` (id, name, gender, dob, weight_class, club_id, record_w, record_l, active_status).
    - [x] Table: `events` (id, name, date, location).
    - [x] Table: `matches` (id, event_id, fighter_red_id, fighter_blue_id, result).
- [x] **Database Utilities**
    - [x] Create `utils/database.py` with CRUD operations for clubs, fighters, events, matches.
- [x] **Roster Management UI (CRUD)**
    - [x] Create **"Manage Fighters"** Page.
    - [x] Form: `Add New Fighter` (Direct to DB).
    - [x] Table: `Edit Existing Fighters` (Bulk update weights/records via `st.data_editor`).
    - [x] Feature: Archive/Deactivate retired fighters.

## ✅ Phase 3: Data Ingestion Modes (COMPLETED)
- [x] **Mode A: File Upload (Legacy)**
    - [x] `st.file_uploader` for Excel/CSV.
    - [x] Validation: Check for required columns (Name, Weight, Gym, Age).
- [x] **Mode B: Google Sheets Import**
    - [x] Input: Text field for "Sheet URL".
    - [x] Logic: Connect via `st.connection("gsheets")`.
    - [x] Mapper: Dropdowns to map Sheet Headers -> App Columns (e.g., "Sheet: 'Mass'" -> "App: 'Weight'").
- [x] **Mode C: "One-Click" Tournament (Database)**
    - [x] UI: Select `Event Date` / `Tournament Name`.
    - [x] UI: Filter Fighters by Club.
    - [x] **Selection**: Checkbox list to select "Who is present today?".
    - [x] Action: "Send to Staging" (Creates a temporary dataframe for pairing).

## Phase 4: Enhanced Pairing Engine (Core Logic)
*This logic runs on the dataframe created in Phase 3, regardless of source.*
- [ ] **Pre-Processing**
    - [ ] Calculate Age from DOB.
    - [ ] Normalize Gender (M/F).
    - [ ] Assign Weight Brackets (IFMA Standards).
- [x] **Algorithm Implementation**
    - [x] **Strict Rules**: Filter out Same-Club & Mixed-Gender.
    - [x] **Scoring System**: Calculate penalty score for Weight Diff + Age Diff + Experience Diff.
    - [x] **Optimization**: Greedy algorithm to minimize total penalty score across all pairs.
    - [x] **Leftovers**: Handle odd numbers/unmatchable fighters gracefully.

## Phase 5: Advanced Matchmaking Dashboard (The UI)
- [x] **Interactive Redaction**
    - [x] Display `Auto-Generated Pairs` in `st.data_editor`.
    - [ ] **Manual Override**: Allow dragging/swapping opponents.
    - [ ] **Warnings**: Highlight rows red if constraints are broken (e.g., Age Gap > 2 years).
- [ ] **Unmatched Pool**
    - [ ] Sidebar/Bottom section showing fighters with no match.
    - [ ] "Force Match" button (Override safety warnings).

## Phase 6: Exports & History
- [x] **PDF Generator**
    - [x] Layout: Header (Event Name), List of Bouts (Red vs Blue), Footer (Officials).
    - [x] Library: `fpdf`.
- [x] **Excel Export**
    - [x] Simple dump of final bout list.
- [x] **Save to History (DB Only)**
    - [x] Button: "Finalize Event".
    - [x] Action: Write the final bouts to the `matches` table in Supabase.

## Phase 7: Deployment & Production
- [x] **Dockerization**
    - [x] Create `Dockerfile` (Python 3.11-slim).
- [ ] **Cloud Config**
    - [ ] Setup Streamlit Cloud project.
    - [ ] Copy local secrets to Streamlit Cloud Secrets Management.
- [ ] **User Testing**
    - [ ] Test "Google Sheet" flow with a real gym roster.
    - [ ] Test "One Click" flow with 50+ fighters in DB.

## 📋 Implementation Roadmap

### **Immediate Next Steps (Priority: High)**
1. **Add Supabase Dependencies**: Update `requirements.txt` with `supabase`, `st-gsheets-connection`
2. **Create Secrets Template**: `.streamlit/secrets.toml.template` with placeholders
3. **Authentication Layer**: Implement login screen and session management
4. **Database Schema**: Design and create Supabase tables

### **Medium-term Goals (Priority: Medium)**
5. **Roster Management**: CRUD interface for fighters and clubs
6. **Google Sheets Integration**: URL input and column mapping
7. **Database Tournament Mode**: Event selection and fighter filtering
8. **Enhanced Dashboard**: Constraint warnings and force matching

### **Future Enhancements (Priority: Low)**
9. **History & Finalization**: Save completed events to database
10. **Streamlit Cloud Deployment**: Production hosting setup
11. **Advanced Testing**: Real-world data testing

## 🎯 Current Status Summary
- **Core Functionality**: ✅ Complete (File upload → Pairing → Manual edit → Export)
- **Advanced Features**: 🚧 Planned (Auth, Database, Multiple data sources)
- **Production Ready**: ⚠️ Basic version ready, needs enterprise features for full deployment

## 📈 Migration Strategy
1. **Phase 1-2**: Add auth and database foundation
2. **Phase 3**: Introduce new data ingestion modes alongside existing file upload
3. **Phase 4-5**: Enhance pairing and UI with database integration
4. **Phase 6-7**: Add history tracking and production deployment

*Estimated timeline: 4-6 weeks for full implementation*
