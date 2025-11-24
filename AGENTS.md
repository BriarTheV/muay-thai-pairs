# AI Agent Context & Directives

## 🧠 Project Context
You are assisting in building a **Muay Thai Matchmaking Service** using **Streamlit**. The goal is to pair athletes for combat sports competitions safely and fairly.

## 🏗 Architecture & State Management
*   **Framework**: Streamlit.
*   **Critical Rule**: Streamlit re-runs the entire script on every interaction. **ALL** mutable data (the list of pairs, the current uploaded dataframe) MUST be stored in `st.session_state`.
*   **Data Flow**:
    1.  `Raw Data` (Excel) → `st.session_state['fighters_df']`
    2.  `Pairing Engine` (Function) → `st.session_state['matches']`
    3.  `User Edits` (Data Editor) → Updates `st.session_state['matches']`
    4.  `Export` → Reads from `st.session_state['matches']`

## 🥊 Domain Rules (The "Physics" of this world)
When writing logic or tests, adhere to these constraints:
1.  **Gym Conflict**: `Fighter_A.Club` == `Fighter_B.Club` is INVALID (unless explicitly overridden).
2.  **Gender Separation**: Mixed-gender fights are strictly FORBIDDEN.
3.  **Weight Classes**:
    *   Matches are made within buckets (e.g., 63.5kg - 67kg).
    *   Allow a "Catchweight" tolerance (configurable, default ±0.5kg).
4.  **Unmatched Fighters**: If a fighter has no safe opponent, they remain in the "Unmatched" pool. Do not force a bad match.

## 💻 Coding Standards
*   **Type Hinting**: Use Python type hints for all pairing functions (e.g., `def find_match(fighter: Fighter) -> Optional[Fighter]:`).
*   **Modularity**: Keep the pairing logic in `utils/pairing.py`, separate from the UI code in `app.py`.
*   **Pandas**: Use vectorized operations where possible, but for the greedy matching algorithm, iterating over sorted lists is acceptable for clarity.
*   **Error Handling**: Never crash on bad Excel data. Log the error and skip the row.

## 📝 File Structure
*   `app.py`: Main UI entry point.
*   `utils/pairing.py`: The core algorithm (Greedy matching logic).
*   `utils/data_loader.py`: Excel validation and cleaning.
*   `utils/pdf_gen.py`: FPDF layout generation.

## ⚠️ Common Pitfalls to Avoid
*   **Do not** use global variables; use `st.session_state`.
*   **Do not** lose manual edits when the user changes a filter. Ensure `st.data_editor` writes back to state.
*   **Do not** hallucinate rules. If unsure about a pairing rule (e.g., age gap limits), define it as a `CONSTANT` at the top of the file so it can be easily changed later.
