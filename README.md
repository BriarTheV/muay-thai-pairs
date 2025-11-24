# Muay Thai Matchmaker 🥊

A Streamlit-based web application designed to automate and manage the creation of fight pairs for Muay Thai competitions. This tool streamlines the matchmaking process by processing athlete data from Excel, applying rule-based pairing logic (IFMA standard compliant), and allowing manual adjustments before exporting official bout sheets.

## 🚀 Features

- **Excel Ingestion**: Upload athlete rosters with automatic cleaning and validation.
- **Smart Pairing Algorithm**:
  - Automatically matches fighters by **Gender**, **Weight Class**, **Age**, and **Experience**.
  - **Conflict Avoidance**: Hard constraints prevent fighters from the same gym or trainer from facing each other.
  - **Safety Checks**: Flags matches with unsafe weight or age discrepancies.
- **Interactive Redaction**: Drag-and-drop style interface to manually adjust bouts or handle unmatched fighters.
- **Export**: Generate professional PDF bout sheets and Excel summaries for officials.

## 🛠 Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Core** | Python 3.11+ | Main programming language |
| **UI Framework** | Streamlit | Interactive web interface and state management |
| **Data Processing** | Pandas | Dataframe manipulation and filtering logic |
| **I/O** | OpenPyXL | Reading/Writing Excel files |
| **Reporting** | FPDF / ReportLab | Generating PDF bout sheets |
| **Deployment** | Docker | Containerization for easy hosting |
| **Database**  | PostgreSQL (Supabase) | Persistent data storage    |
| **Auth**      | Supabase Auth         | User management & Security |
| **UI**        | Streamlit             | Frontend interface         |

The app expects an Excel file with at least: `Name`, `Gender`, `Age`, `Weight`, `Club`, `Trainer`, `Record`.

## ⚖️ Logic & Rules

The pairing engine prioritizes safety first, then fairness:
1. **Strict Filter**: Gender must match.
2. **Strict Filter**: Club must differ (unless "Sparring Mode" is enabled).
3. **Optimization**: Minimizes variance in Weight and Experience.
4. **Safety**: Warns if Age gap > 2 years (for Juniors) or Weight gap > 5%.
