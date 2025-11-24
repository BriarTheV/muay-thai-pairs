# Muay Thai Matchmaker

import streamlit as st
import pandas as pd
from utils.data_loader import validate_excel_file, get_weight_class
from utils.pairing import pair_fighters
from utils.pdf_gen import generate_excel_matches, generate_pdf_bout_sheets

st.title("🥊 Muay Thai Matchmaker")

# Initialize session state
if "fighters_df" not in st.session_state:
    st.session_state["fighters_df"] = pd.DataFrame()
if "matches" not in st.session_state:
    st.session_state["matches"] = pd.DataFrame()
if "unmatched" not in st.session_state:
    st.session_state["unmatched"] = pd.DataFrame()

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Data Upload", "🤝 Generate Pairs", "✏️ Manual Adjustments", "📤 Export"]
)

with tab1:
    st.header("Data Upload & Validation")

    # File uploader
    uploaded_file = st.file_uploader(
        "Upload Excel file with fighter data",
        type=["xlsx"],
        help="Excel file must contain columns: Name, Gender, Age, Weight, Club, Trainer, Record",
    )

    if uploaded_file is not None:
        # Validate and load data
        df, error_msg = validate_excel_file(uploaded_file)

        if error_msg:
            st.error(f"Error loading data: {error_msg}")
        else:
            st.success("Data loaded successfully!")

            # Add weight class
            df["Weight Class"] = df["Weight"].apply(get_weight_class)

            # Store in session state
            st.session_state["fighters_df"] = df

            # Display data
            st.subheader("Fighter Data")
            st.dataframe(df)

            st.write(f"Total fighters: {len(df)}")
            st.write(f"Genders: {df['Gender'].value_counts().to_dict()}")
            st.write(f"Clubs: {df['Club'].nunique()} unique clubs")

with tab2:
    st.header("Generate Automatic Pairings")

    if st.session_state["fighters_df"].empty:
        st.warning("Please upload fighter data first in the Data Upload tab.")
    else:
        df = st.session_state["fighters_df"]

        # Configuration
        col1, col2 = st.columns(2)
        with col1:
            weight_tolerance = st.slider("Weight Tolerance (kg)", 0.0, 2.0, 0.5, 0.1)
        with col2:
            allow_same_trainer = st.checkbox("Allow same trainer matches", value=False)

        # Generate pairings button
        if st.button("Generate Pairings", type="primary"):
            with st.spinner("Generating pairings..."):
                matches_df, unmatched_df = pair_fighters(df)

                # Store in session state
                st.session_state["matches"] = matches_df
                st.session_state["unmatched"] = unmatched_df

            st.success("Pairings generated!")

        # Display results
        if not st.session_state["matches"].empty:
            matches_df = st.session_state["matches"]
            st.subheader("Generated Matches")
            st.dataframe(matches_df)

            # Statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Matches", len(matches_df))
            with col2:
                avg_weight_diff = matches_df["Weight_Diff"].mean()
                st.metric("Avg Weight Diff", f"{avg_weight_diff:.2f} kg")
            with col3:
                st.metric("Unmatched Fighters", len(st.session_state["unmatched"]))

            # Warnings
            warnings = []
            high_weight_diff = matches_df[matches_df["Weight_Diff"] > 1.0]
            if not high_weight_diff.empty:
                warnings.append(
                    f"{len(high_weight_diff)} matches with weight diff > 1kg"
                )

            high_age_diff = matches_df[matches_df["Age_Diff"] > 3]
            if not high_age_diff.empty:
                warnings.append(f"{len(high_age_diff)} matches with age diff > 3 years")

            if warnings:
                st.warning(" ⚠️ " + "; ".join(warnings))

        if not st.session_state["unmatched"].empty:
            st.subheader("Unmatched Fighters")
            st.dataframe(st.session_state["unmatched"])

with tab3:
    st.header("Manual Adjustments")

    if st.session_state["matches"].empty:
        st.warning("Please generate pairings first in the Generate Pairs tab.")
    else:
        st.write("Edit the matches table below. Changes are saved automatically.")

        # Editable data editor
        edited_matches = st.data_editor(
            st.session_state["matches"],
            num_rows="dynamic",
            use_container_width=True,
            key="matches_editor",
        )

        # Update session state with edits
        st.session_state["matches"] = edited_matches

        st.success("Matches updated!")

        # Display current matches
        st.subheader("Current Matches")
        st.dataframe(edited_matches)

with tab4:
    st.header("Export Results")

    if st.session_state["matches"].empty:
        st.warning("No matches to export. Generate pairings first.")
    else:
        matches_df = st.session_state["matches"]

        # Event name input
        event_name = st.text_input("Event Name", value="Muay Thai Competition")

        # Export buttons
        col1, col2 = st.columns(2)

        with col1:
            if st.button("📊 Export to Excel"):
                excel_data = generate_excel_matches(matches_df)
                st.download_button(
                    label="Download Excel",
                    data=excel_data,
                    file_name=f"{event_name.replace(' ', '_')}_matches.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

        with col2:
            if st.button("📄 Export to PDF"):
                pdf_data = generate_pdf_bout_sheets(matches_df, event_name)
                st.download_button(
                    label="Download PDF",
                    data=pdf_data,
                    file_name=f"{event_name.replace(' ', '_')}_bout_sheets.pdf",
                    mime="application/pdf",
                )

        # Statistics panel
        st.subheader("Competition Statistics")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Matches", len(matches_df))

        with col2:
            total_fighters = len(st.session_state["fighters_df"])
            st.metric("Total Fighters", total_fighters)

        with col3:
            matched_fighters = len(matches_df) * 2
            st.metric("Matched Fighters", matched_fighters)

        with col4:
            unmatched = len(st.session_state["unmatched"])
            st.metric("Unmatched Fighters", unmatched)

        # Detailed stats
        if not matches_df.empty:
            st.subheader("Match Details")
            st.write(
                f"Average weight difference: {matches_df['Weight_Diff'].mean():.2f} kg"
            )
            st.write(
                f"Average age difference: {matches_df['Age_Diff'].mean():.1f} years"
            )

            # Gender distribution
            gender_dist = matches_df["Gender"].value_counts()
            st.bar_chart(gender_dist)

            # Weight class distribution
            wc_dist = matches_df["Weight_Class"].value_counts()
            st.bar_chart(wc_dist)
