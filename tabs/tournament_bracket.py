import streamlit as st
import pandas as pd
from utils.translations import translations
import random


def t(key, default=None):
    """Translation function with optional fallback"""
    lang = st.session_state.get("language", "ru")
    if default is None:
        default = key
    return translations[lang].get(key, default)


def generate_seeded_bracket(
    participants: list, seeding_method: str = "standard"
) -> list:
    """Generate seeded single-elimination bracket."""
    n = len(participants)

    # Sort participants based on seeding method
    if seeding_method == "experience":
        # Assume participants have experience info, but for now, keep as is
        pass  # Could sort by total_fights if available
    elif seeding_method == "random":
        import random

        random.shuffle(participants)
    # Standard: keep order

    # Find next power of 2
    bracket_size = 1
    while bracket_size < n:
        bracket_size *= 2

    # Add byes
    seeded = participants + ["BYE"] * (bracket_size - n)

    # Seeding: alternate high-low
    bracket = []
    for i in range(bracket_size // 2):
        bracket.append((seeded[i], seeded[bracket_size - 1 - i]))

    return bracket


def display_bracket_round(bracket: "TournamentBracket", round_num: int):
    """Display a specific round of the tournament bracket with enhanced visualization."""
    if round_num >= len(bracket.rounds):
        st.error("Round does not exist")
        return

    round_matches = bracket.rounds[round_num]

    # Enhanced header with progress indicator
    total_rounds = len(bracket.rounds)
    progress = (round_num + 1) / total_rounds

    st.markdown(
        f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <h2 style="color: var(--text-primary);">🏆 Round {round_num + 1} of {total_rounds}</h2>
        <div style="background: var(--tertiary-bg); border-radius: 10px; height: 8px; width: 100%; max-width: 300px; margin: 10px auto;">
            <div style="background: linear-gradient(90deg, var(--accent-success) {progress * 100}%, var(--accent-secondary) {progress * 100}%); height: 100%; border-radius: 10px;"></div>
        </div>
        <p style="color: var(--text-secondary); margin: 5px 0;">{round_num + 1}/{total_rounds} rounds completed</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if not round_matches:
        st.info(t("no_matches_round"))
        return

    # Display matches with enhanced styling
    cols = st.columns(min(3, max(1, len(round_matches))))
    for i, (fighter1, fighter2) in enumerate(round_matches):
        with cols[i % len(cols)]:
            # Check if this match has a winner
            winner_key = f"r{round_num}m{i}"
            current_winner = bracket.winners.get(winner_key)

            # Determine match status styling
            if current_winner:
                border_color = "var(--accent-success)"  # Green for completed
                bg_color = "var(--secondary-bg)"  # Theme background
                status_icon = "✅"
            elif fighter1 == "BYE" or fighter2 == "BYE":
                border_color = "var(--accent-warning)"  # Yellow for bye
                bg_color = "var(--secondary-bg)"  # Theme background
                status_icon = "🚫"
            else:
                border_color = "var(--accent-primary)"  # Blue for pending
                bg_color = "var(--primary-bg)"  # Theme background
                status_icon = "⏳"

            st.markdown(
                f"""
            <div style="border: 3px solid {border_color}; border-radius: var(--radius-large); padding: 20px; margin: 15px 0; background: {bg_color}; box-shadow: var(--shadow-medium); color: var(--text-primary);">
                <div style="text-align: center; margin-bottom: 15px;">
                    <h4 style="margin: 0; color: {border_color};">{status_icon} Match {i + 1}</h4>
                </div>
            """,
                unsafe_allow_html=True,
            )

            if fighter1 == "BYE":
                st.markdown(
                    f"""
                <div style="text-align: center; padding: 10px; background: var(--secondary-bg); border-radius: var(--radius-medium); margin: 10px 0; border: 1px solid var(--border-color);">
                    <strong style="color: var(--accent-success);">{fighter2}</strong><br>
                    <small style="color: var(--text-secondary);">BYE (Automatic Advance)</small>
                </div>
                """,
                    unsafe_allow_html=True,
                )
                if round_num < len(bracket.rounds) - 1:
                    bracket.advance_winner(round_num, i, fighter2)
            elif fighter2 == "BYE":
                st.markdown(
                    f"""
                <div style="text-align: center; padding: 10px; background: var(--secondary-bg); border-radius: var(--radius-medium); margin: 10px 0; border: 1px solid var(--border-color);">
                    <strong style="color: var(--accent-success);">{fighter1}</strong><br>
                    <small style="color: var(--text-secondary);">BYE (Automatic Advance)</small>
                </div>
                """,
                    unsafe_allow_html=True,
                )
                if round_num < len(bracket.rounds) - 1:
                    bracket.advance_winner(round_num, i, fighter1)
            else:
                # Fighter display with enhanced styling
                col1, col2 = st.columns(2)
                with col1:
                    fighter_style = (
                        f"color: var(--accent-danger); font-weight: bold;"
                        if current_winner == fighter1
                        else f"color: var(--text-secondary);"
                    )
                    border_color = (
                        "var(--accent-success)"
                        if current_winner == fighter1
                        else "var(--border-color)"
                    )
                    winner_badge = (
                        f'<div style="color: var(--accent-success); font-weight: bold; margin-top: 5px;">🏆 WINNER</div>'
                        if current_winner == fighter1
                        else ""
                    )
                    st.markdown(
                        f"""
                    <div style="text-align: center; padding: 10px; background: var(--primary-bg); border-radius: var(--radius-medium); margin: 5px; border: 2px solid {border_color}; color: var(--text-primary);">
                        <div style="font-size: 1.2em; {fighter_style}">🔴 {fighter1}</div>
                        {winner_badge}
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                with col2:
                    fighter_style = (
                        f"color: var(--accent-primary); font-weight: bold;"
                        if current_winner == fighter2
                        else f"color: var(--text-secondary);"
                    )
                    border_color = (
                        "var(--accent-success)"
                        if current_winner == fighter2
                        else "var(--border-color)"
                    )
                    winner_badge = (
                        f'<div style="color: var(--accent-success); font-weight: bold; margin-top: 5px;">🏆 WINNER</div>'
                        if current_winner == fighter2
                        else ""
                    )
                    st.markdown(
                        f"""
                    <div style="text-align: center; padding: 10px; background: var(--primary-bg); border-radius: var(--radius-medium); margin: 5px; border: 2px solid {border_color}; color: var(--text-primary);">
                        <div style="font-size: 1.2em; {fighter_style}">🔵 {fighter2}</div>
                        {winner_badge}
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                # Winner selection (only if not yet decided)
                if not current_winner:
                    st.markdown(
                        "<div style='text-align: center; margin: 15px 0;'><strong>Select Winner:</strong></div>",
                        unsafe_allow_html=True,
                    )

                    winner = st.radio(
                        f"Winner for Match {i + 1}:",
                        [fighter1, fighter2],
                        key=winner_key,
                        horizontal=True,
                        label_visibility="collapsed",
                    )

                    if st.button(
                        f"Confirm Winner",
                        key=f"confirm_{round_num}_{i}",
                        type="primary",
                    ):
                        bracket.advance_winner(round_num, i, winner)
                        st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)


def display_interactive_bracket(matches_df: pd.DataFrame):
    """Display interactive Olympic-style tournament bracket with improved readability."""
    winners = st.session_state.get("bracket_winners", {})
    current_round = st.session_state.get("current_round", 1)

    # Inject CSS for interactive bracket
    st.markdown(
        """
    <style>
    .tournament-header {
        text-align: center;
        margin-bottom: 20px;
    }
    .tournament-header h2 {
        color: var(--text-primary);
        margin-bottom: 5px;
    }
    .tournament-header p {
        color: var(--text-secondary);
        margin: 0;
    }
    .match-card {
        border: 2px solid var(--border-color);
        border-radius: var(--radius-large);
        padding: 15px;
        margin: 10px 0;
        background: var(--primary-bg);
        box-shadow: var(--shadow-light);
        color: var(--text-primary);
    }
    .fighter-name {
        font-weight: bold;
        margin: 5px 0;
        color: var(--text-primary);
    }
    .winner-badge {
        background: var(--accent-success);
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        margin-left: 10px;
    }
    .bye-badge {
        background: var(--accent-warning);
        color: var(--text-primary);
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        margin-left: 10px;
    }
    .round-section {
        margin-bottom: 30px;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Group by weight class
    if "Weight_Class" in matches_df.columns:
        grouped = matches_df.groupby("Weight_Class")
    else:
        grouped = [(t("all_classes"), matches_df)]

    for class_name, class_matches in grouped:
        st.markdown(
            f"""
        <div class="tournament-header">
            <h2>{t("weight_class")}: {class_name}</h2>
            <p>🏆 Olympic Single-Elimination Tournament</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Get participants for this weight class
        participants = []
        for _, match in class_matches.iterrows():
            participants.extend(
                [
                    f"{match['Red_Corner']} ({match['Red_Club']})",
                    f"{match['Blue_Corner']} ({match['Blue_Club']})",
                ]
            )

        # Generate bracket
        bracket = generate_seeded_bracket(participants)

        # Display rounds
        round_matches = bracket
        round_num = 1

        while round_matches:
            with st.expander(
                f"📅 {t('round')} {round_num}", expanded=(round_num == current_round)
            ):
                if round_num == current_round:
                    # Interactive round
                    st.markdown('<div class="round-section">', unsafe_allow_html=True)
                    num_cols = min(4, max(1, len(round_matches) // 2))
                    cols = st.columns(num_cols)
                    for i, (fighter1, fighter2) in enumerate(round_matches):
                        with cols[i % len(cols)]:
                            if fighter1 == "BYE":
                                st.markdown(
                                    f"""
                                <div class="match-card">
                                    <div class="fighter-name">{fighter2}</div>
                                    <span class="bye-badge">BYE</span>
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )
                                winners[f"round{round_num}_match{i}"] = fighter2
                            elif fighter2 == "BYE":
                                st.markdown(
                                    f"""
                                <div class="match-card">
                                    <div class="fighter-name">{fighter1}</div>
                                    <span class="bye-badge">BYE</span>
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )
                                winners[f"round{round_num}_match{i}"] = fighter1
                            else:
                                st.markdown(
                                    f"""
                                <div class="match-card">
                                    <h4>{t("pair")} {i + 1}</h4>
                                    <div class="fighter-name">🔴 {fighter1}</div>
                                    <div style="text-align: center; margin: 10px 0;">VS</div>
                                    <div class="fighter-name">🔵 {fighter2}</div>
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )

                                winner = st.radio(
                                    "🏆 Select Winner:",
                                    [fighter1, fighter2],
                                    key=f"round{round_num}_match{i}",
                                    horizontal=True,
                                    label_visibility="collapsed",
                                )
                                winners[f"round{round_num}_match{i}"] = winner
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    # Show results
                    st.markdown('<div class="round-section">', unsafe_allow_html=True)
                    num_cols = min(4, max(1, len(round_matches) // 2))
                    cols = st.columns(num_cols)
                    for i, (fighter1, fighter2) in enumerate(round_matches):
                        with cols[i % len(cols)]:
                            winner = winners.get(f"round{round_num}_match{i}")
                            if winner:
                                st.markdown(
                                    f"""
                                <div class="match-card">
                                    <h4>{t("pair")} {i + 1}</h4>
                                    <div class="fighter-name">{winner}</div>
                                    <span class="winner-badge">WINNER</span>
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.markdown(
                                    f"""
                                <div class="match-card">
                                    <h4>{t("pair")} {i + 1}</h4>
                                    <div style="color: #6c757d;">Pending Result</div>
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )
                    st.markdown("</div>", unsafe_allow_html=True)

            # Prepare next round
            next_round_matches = []
            for i in range(0, len(round_matches), 2):
                w1 = winners.get(f"round{round_num}_match{i}")
                w2 = winners.get(f"round{round_num}_match{i + 1}")
                if w1 and w2:
                    next_round_matches.append((w1, w2))

            round_matches = next_round_matches
            round_num += 1

        # Update session state
        st.session_state["bracket_winners"] = winners
        st.session_state["current_round"] = current_round

        # Controls
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(
                "⏭️ Next Round",
                type="primary",
                key=f"bracket_next_round_{current_round}",
            ):
                st.session_state["current_round"] = min(current_round + 1, round_num)
                st.rerun()
        with col2:
            st.metric("Current Round", current_round)
        with col3:
            if st.button("🔄 Reset Tournament", key=f"bracket_reset_{current_round}"):
                st.session_state["bracket_winners"] = {}
                st.session_state["current_round"] = 1
                st.rerun()
        with col2:
            if st.button("Reset Tournament"):
                st.session_state["bracket_winners"] = {}
                st.session_state["current_round"] = 1
                st.rerun()


class RoundRobinTournament:
    """Manages a round-robin tournament where each fighter plays every other fighter."""

    def __init__(self, fighters_df: pd.DataFrame):
        self.fighters_df = fighters_df
        self.matches = []
        self.results = {}  # match_id -> winner
        self.statistics = {}  # fighter_name -> {'wins': 0, 'losses': 0, 'points': 0}
        self.completed = False

        # Initialize statistics for all fighters
        for _, fighter in fighters_df.iterrows():
            name = f"{fighter['Name']} ({fighter.get('Club', 'Unknown')})"
            self.statistics[name] = {"wins": 0, "losses": 0, "points": 0}

        # Generate round-robin matches
        self._generate_round_robin_matches()

    def _generate_round_robin_matches(self):
        """Generate all possible matches between fighters."""
        participants = []
        for _, fighter in self.fighters_df.iterrows():
            participants.append(f"{fighter['Name']} ({fighter.get('Club', 'Unknown')})")

        # Generate all unique pairs
        self.matches = []
        for i in range(len(participants)):
            for j in range(i + 1, len(participants)):
                self.matches.append((participants[i], participants[j]))

    def record_result(self, match_idx: int, winner: str):
        """Record the result of a match."""
        if match_idx < len(self.matches):
            self.results[match_idx] = winner

            # Update statistics
            fighter1, fighter2 = self.matches[match_idx]
            loser = fighter1 if winner == fighter2 else fighter2

            self.statistics[winner]["wins"] += 1
            self.statistics[winner]["points"] += 3  # 3 points for win
            self.statistics[loser]["losses"] += 1
            self.statistics[loser]["points"] += 0  # 0 points for loss

            # Check if tournament is complete
            self.completed = len(self.results) == len(self.matches)

    def get_standings(self):
        """Get current standings sorted by points."""
        standings = []
        for fighter, stats in self.statistics.items():
            win_rate = (
                stats["wins"] / (stats["wins"] + stats["losses"])
                if (stats["wins"] + stats["losses"]) > 0
                else 0
            )
            standings.append(
                {
                    "fighter": fighter,
                    "wins": stats["wins"],
                    "losses": stats["losses"],
                    "points": stats["points"],
                    "win_rate": win_rate,
                }
            )

        return sorted(standings, key=lambda x: (-x["points"], -x["win_rate"]))


class TournamentBracket:
    """Manages a single-elimination tournament bracket."""

    def __init__(self, fighters_df: pd.DataFrame, seeding_method: str = "standard"):
        self.fighters_df = fighters_df
        self.seeding_method = seeding_method
        self.rounds = []
        self.current_round = 0
        self.winners = {}
        self.completed = False

        # Generate initial bracket
        self._generate_bracket()

    def _generate_bracket(self):
        """Generate the tournament bracket structure."""
        # Get fighter names for bracket
        participants = []
        for _, fighter in self.fighters_df.iterrows():
            name = f"{fighter['Name']} ({fighter.get('Club', 'Unknown')})"
            participants.append(name)

        # Generate seeded bracket
        bracket = generate_seeded_bracket(participants, self.seeding_method)

        # Initialize rounds
        self.rounds = [bracket]

        # Generate subsequent rounds (placeholders)
        current_matches = bracket
        round_num = 1
        while len(current_matches) > 1:
            next_matches = []
            for i in range(0, len(current_matches), 2):
                if i + 1 < len(current_matches):
                    next_matches.append(("TBD", "TBD"))
            if next_matches:
                self.rounds.append(next_matches)
            current_matches = next_matches
            round_num += 1

    def advance_winner(self, round_num: int, match_idx: int, winner: str):
        """Advance a winner to the next round."""
        if round_num < len(self.rounds) - 1:
            next_round = round_num + 1
            next_match_idx = match_idx // 2

            if match_idx % 2 == 0:
                # First slot in next match
                self.rounds[next_round][next_match_idx] = (
                    winner,
                    self.rounds[next_round][next_match_idx][1],
                )
            else:
                # Second slot in next match
                self.rounds[next_round][next_match_idx] = (
                    self.rounds[next_round][next_match_idx][0],
                    winner,
                )

        self.winners[f"r{round_num}m{match_idx}"] = winner

        # Check if round is complete
        current_round_matches = self.rounds[round_num]
        if all(
            match[0] != "TBD" and match[1] != "TBD" for match in current_round_matches
        ):
            self.current_round = min(self.current_round + 1, len(self.rounds) - 1)

        # Check tournament completion
        if self.current_round == len(self.rounds) - 1 and len(self.rounds[-1]) == 1:
            final_match = self.rounds[-1][0]
            if final_match[0] != "TBD" and final_match[1] != "TBD":
                self.completed = True


def generate_tournament_bracket(matches_df: pd.DataFrame) -> str:
    """Generate HTML for tournament bracket display with weight class organization."""
    html = f"""
    <style>
        .bracket {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 20px;
            color: var(--text-primary);
        }}
        .weight-class-section {{
            margin-bottom: 40px;
            border: 1px solid var(--border-color);
            border-radius: var(--radius-large);
            padding: 20px;
            background: var(--secondary-bg);
        }}
        .weight-class-title {{
            background-color: var(--weight-header-bg, var(--tertiary-bg));
            padding: 10px;
            border-radius: var(--radius-medium);
            margin-bottom: 20px;
            font-size: 1.2em;
            font-weight: bold;
            color: var(--text-primary);
        }}
        .round {{
            display: inline-block;
            vertical-align: top;
            margin-right: 40px;
        }}
        .round h4 {{
            text-align: center;
            margin-bottom: 10px;
            color: var(--text-primary);
        }}
        .match {{
            border: 2px solid var(--border-color);
            border-radius: var(--radius-large);
            padding: 10px;
            margin: 10px 0;
            background: var(--primary-bg);
            min-width: 200px;
            min-height: 60px;
            color: var(--text-primary);
            box-shadow: var(--shadow-light);
        }}
        .fighter {{
            padding: 5px;
            border-bottom: 1px solid var(--border-light);
            color: var(--text-primary);
        }}
        .fighter:last-child {{
            border-bottom: none;
        }}
        .placeholder {{
            color: var(--text-muted);
            font-style: italic;
        }}
    </style>
    <div class="bracket">
        <h2>{t("tournament_brackets")}</h2>
    """

    # Group by weight class
    if "Weight_Class" in matches_df.columns:
        grouped = matches_df.groupby("Weight_Class")
    else:
        grouped = [(t("all_classes"), matches_df)]

    for class_name, class_matches in grouped:
        # Sort by average age
        class_matches = class_matches.copy()
        class_matches["Avg_Age"] = (
            class_matches["Red_Age"] + class_matches["Blue_Age"]
        ) / 2
        class_matches = class_matches.sort_values("Avg_Age")

        html += f"""
        <div class="weight-class-section">
            <div class="weight-class-title">{t("weight_class")}: {class_name}</div>
            <div class="round">
                <h4>{t("round")} 1</h4>
        """

        for idx, match in class_matches.iterrows():
            html += f"""
                <div class="match">
                    <div class="fighter">{match["Red_Corner"]} ({match["Red_Club"]})</div>
                    <div class="fighter">vs</div>
                    <div class="fighter">{match["Blue_Corner"]} ({match["Blue_Club"]})</div>
                </div>
            """

        # Add subsequent rounds with placeholders
        num_matches = len(class_matches)
        round_num = 2
        while num_matches > 1:
            num_matches = (num_matches + 1) // 2  # Ceiling division
            html += f"""
            </div>
            <div class="round">
                <h4>{t("round")} {round_num}</h4>
            """
            for i in range(num_matches):
                html += """
                <div class="match">
                    <div class="fighter placeholder">Winner Match {i*2+1}</div>
                    <div class="fighter">vs</div>
                    <div class="fighter placeholder">Winner Match {i*2+2}</div>
                </div>
                """

            round_num += 1

        html += """
            </div>
        </div>
        """

    html += "</div>"
    return html


def render_tournament_bracket_tab():
    st.header(t("tournament_brackets"))

    if (
        st.session_state.get("fighters_df") is None
        or st.session_state["fighters_df"].empty
    ):
        st.warning(t("no_fighter_data"))
    else:
        fighters_df = st.session_state["fighters_df"]

        # Tournament format selection
        tournament_format = st.selectbox(
            "Tournament Format",
            ["Single-Elimination", "Round-Robin"],
            index=0,
            help="Choose the tournament format: Single-Elimination (knockout) or Round-Robin (everyone plays everyone)",
        )

        if tournament_format == "Single-Elimination":
            # Create or get tournament bracket
            if (
                "tournament_bracket" not in st.session_state
                or st.session_state.get("tournament_format") != "single"
            ):
                st.session_state["tournament_bracket"] = TournamentBracket(fighters_df)
                st.session_state["tournament_format"] = "single"

            bracket = st.session_state["tournament_bracket"]

            # Tournament controls
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Fighters", len(fighters_df))
            with col2:
                st.metric("Current Round", bracket.current_round + 1)
            with col3:
                status = "🏆 Completed" if bracket.completed else "⏳ In Progress"
                st.metric("Status", status)

            # Display current round
            display_bracket_round(bracket, bracket.current_round)

            # Navigation
            st.markdown("---")
            nav_col1, nav_col2, nav_col3 = st.columns(3)
            with nav_col1:
                if st.button("⬅️ Previous Round", disabled=bracket.current_round == 0):
                    bracket.current_round = max(0, bracket.current_round - 1)
                    st.rerun()
            with nav_col2:
                if st.button(
                    "➡️ Next Round",
                    disabled=bracket.current_round >= len(bracket.rounds) - 1,
                ):
                    bracket.current_round = min(
                        len(bracket.rounds) - 1, bracket.current_round + 1
                    )
                    st.rerun()
            with nav_col3:
                if st.button("🔄 New Tournament"):
                    st.session_state["tournament_bracket"] = TournamentBracket(
                        fighters_df
                    )
                    st.rerun()

        elif tournament_format == "Round-Robin":
            # Create or get round-robin tournament
            if (
                "round_robin_tournament" not in st.session_state
                or st.session_state.get("tournament_format") != "round_robin"
            ):
                st.session_state["round_robin_tournament"] = RoundRobinTournament(
                    fighters_df
                )
                st.session_state["tournament_format"] = "round_robin"

            tournament = st.session_state["round_robin_tournament"]

            # Tournament controls
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Fighters", len(fighters_df))
            with col2:
                completed_matches = len(tournament.results)
                total_matches = len(tournament.matches)
                st.metric("Matches Completed", f"{completed_matches}/{total_matches}")
            with col3:
                status = "🏆 Completed" if tournament.completed else "⏳ In Progress"
                st.metric("Status", status)

            # Display current matches and allow result entry
            st.subheader(t("round_robin_matches"))

            if not tournament.completed:
                # Show pending matches
                pending_matches = [
                    i
                    for i in range(len(tournament.matches))
                    if i not in tournament.results
                ]

                if pending_matches:
                    st.write(t("select_match_result"))

                    # Display matches in a grid
                    cols = st.columns(min(3, len(pending_matches)))
                    for idx, match_idx in enumerate(
                        pending_matches[:9]
                    ):  # Show first 9 pending matches
                        with cols[idx % len(cols)]:
                            fighter1, fighter2 = tournament.matches[match_idx]
                            st.markdown(
                                f"""
                            <div style="border: 2px solid #ddd; border-radius: 8px; padding: 10px; margin: 5px; background: #f8f9fa;">
                                <strong>Match {match_idx + 1}</strong><br>
                                🔴 {fighter1}<br>
                                🔵 {fighter2}
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                            winner = st.radio(
                                f"Winner for Match {match_idx + 1}:",
                                [fighter1, fighter2],
                                key=f"rr_match_{match_idx}",
                                horizontal=True,
                                label_visibility="collapsed",
                            )

                            if st.button(f"Record Result", key=f"record_{match_idx}"):
                                tournament.record_result(match_idx, winner)
                                st.rerun()
                else:
                    st.success(t("all_matches_completed"))
            else:
                st.success(t("tournament_completed"))

            # Display standings
            st.subheader(t("current_standings"))
            standings = tournament.get_standings()

            standings_df = pd.DataFrame(standings)
            standings_df["Position"] = range(1, len(standings_df) + 1)
            standings_df = standings_df[
                ["Position", "fighter", "wins", "losses", "points", "win_rate"]
            ]

            st.dataframe(
                standings_df,
                column_config={
                    "Position": st.column_config.NumberColumn("Pos", width="small"),
                    "fighter": st.column_config.TextColumn("Fighter", width="large"),
                    "wins": st.column_config.NumberColumn("W", width="small"),
                    "losses": st.column_config.NumberColumn("L", width="small"),
                    "points": st.column_config.NumberColumn("Pts", width="small"),
                    "win_rate": st.column_config.NumberColumn(
                        "Win %", format="%.1%", width="small"
                    ),
                },
                use_container_width=True,
            )

            # Reset tournament
            st.markdown("---")
            if st.button("🔄 New Round-Robin Tournament"):
                st.session_state["round_robin_tournament"] = RoundRobinTournament(
                    fighters_df
                )
                st.rerun()

        # Tournament History Section
        st.markdown("---")
        st.subheader(t("tournament_history"))

        # Initialize tournament history if not exists
        if "tournament_history" not in st.session_state:
            st.session_state["tournament_history"] = []

        # Save current tournament
        if st.button("💾 Save Tournament to History"):
            if (
                tournament_format == "Single-Elimination"
                and hasattr(st.session_state.get("tournament_bracket"), "completed")
                and st.session_state["tournament_bracket"].completed
            ):
                tournament_data = {
                    "format": "Single-Elimination",
                    "date": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                    "fighters_count": len(fighters_df),
                    "bracket": st.session_state["tournament_bracket"],
                    "winners": st.session_state["tournament_bracket"].winners.copy(),
                }
                st.session_state["tournament_history"].append(tournament_data)
                st.success("Tournament saved to history!")
            elif (
                tournament_format == "Round-Robin"
                and st.session_state["round_robin_tournament"].completed
            ):
                tournament_data = {
                    "format": "Round-Robin",
                    "date": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                    "fighters_count": len(fighters_df),
                    "standings": st.session_state[
                        "round_robin_tournament"
                    ].get_standings(),
                    "results": st.session_state[
                        "round_robin_tournament"
                    ].results.copy(),
                }
                st.session_state["tournament_history"].append(tournament_data)
                st.success(t("tournament_saved"))
            elif (
                tournament_format == "Round-Robin"
                and st.session_state["round_robin_tournament"].completed
            ):
                tournament_data = {
                    "format": "Round-Robin",
                    "date": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                    "fighters_count": len(fighters_df),
                    "standings": st.session_state[
                        "round_robin_tournament"
                    ].get_standings(),
                    "results": st.session_state[
                        "round_robin_tournament"
                    ].results.copy(),
                }
                st.session_state["tournament_history"].append(tournament_data)
                st.success(t("tournament_saved"))
            else:
                st.warning(t("complete_tournament_first"))

        # Display tournament history
        if st.session_state["tournament_history"]:
            st.write(t("previous_tournaments"))
            for i, hist_tournament in enumerate(
                reversed(st.session_state["tournament_history"][-5:])
            ):  # Show last 5
                with st.expander(
                    f"{hist_tournament['format']} - {hist_tournament['date']} ({hist_tournament['fighters_count']} fighters)"
                ):
                    if hist_tournament["format"] == "Round-Robin":
                        standings_df = pd.DataFrame(hist_tournament["standings"])
                        standings_df["Position"] = range(1, len(standings_df) + 1)
                        st.dataframe(
                            standings_df[
                                ["Position", "fighter", "wins", "losses", "points"]
                            ]
                        )
                    else:
                        st.write(t("single_elim_completed"))
                        if hist_tournament.get("winners"):
                            final_winner = (
                                list(hist_tournament["winners"].values())[-1]
                                if hist_tournament["winners"]
                                else "Unknown"
                            )
                            st.write(f"{t('champion')} {final_winner}")
        else:
            st.info(t("no_tournament_history"))

        # Tournament Statistics Section
        st.markdown("---")
        st.subheader(t("tournament_statistics"))

        if st.session_state["tournament_history"]:
            total_tournaments = len(st.session_state["tournament_history"])
            single_elim_tournaments = sum(
                1
                for t in st.session_state["tournament_history"]
                if t["format"] == "Single-Elimination"
            )
            round_robin_tournaments = sum(
                1
                for t in st.session_state["tournament_history"]
                if t["format"] == "Round-Robin"
            )

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Tournaments", total_tournaments)
            with col2:
                st.metric("Single-Elimination", single_elim_tournaments)
            with col3:
                st.metric("Round-Robin", round_robin_tournaments)

            # Fighter performance across all tournaments
            if st.session_state["tournament_history"]:
                st.subheader(t("all_time_performance"))

                fighter_stats = {}

                for tournament in st.session_state["tournament_history"]:
                    if tournament["format"] == "Round-Robin":
                        for standing in tournament["standings"]:
                            fighter = standing["fighter"]
                            if fighter not in fighter_stats:
                                fighter_stats[fighter] = {
                                    "tournaments": 0,
                                    "total_wins": 0,
                                    "total_points": 0,
                                    "best_position": float("inf"),
                                }
                            fighter_stats[fighter]["tournaments"] += 1
                            fighter_stats[fighter]["total_wins"] += standing["wins"]
                            fighter_stats[fighter]["total_points"] += standing["points"]
                            fighter_stats[fighter]["best_position"] = min(
                                fighter_stats[fighter]["best_position"],
                                standing.get("position", len(tournament["standings"])),
                            )

                if fighter_stats:
                    # Calculate averages and rankings
                    performance_data = []
                    for fighter, stats in fighter_stats.items():
                        avg_wins = stats["total_wins"] / stats["tournaments"]
                        avg_points = stats["total_points"] / stats["tournaments"]
                        performance_data.append(
                            {
                                "Fighter": fighter,
                                "Tournaments": stats["tournaments"],
                                "Avg Wins": round(avg_wins, 1),
                                "Avg Points": round(avg_points, 1),
                                "Best Position": stats["best_position"],
                            }
                        )

                    # Sort by average points descending
                    performance_data.sort(
                        key=lambda x: (-x["Avg Points"], x["Best Position"])
                    )

                    performance_df = pd.DataFrame(performance_data)
                    st.dataframe(
                        performance_df,
                        column_config={
                            "Fighter": st.column_config.TextColumn(
                                "Fighter", width="large"
                            ),
                            "Tournaments": st.column_config.NumberColumn(
                                "Tournaments", width="small"
                            ),
                            "Avg Wins": st.column_config.NumberColumn(
                                "Avg Wins", width="small"
                            ),
                            "Avg Points": st.column_config.NumberColumn(
                                "Avg Points", width="small"
                            ),
                            "Best Position": st.column_config.NumberColumn(
                                "Best Pos", width="small"
                            ),
                        },
                        use_container_width=True,
                    )
                else:
                    st.info(t("no_fighter_stats"))
        else:
            st.info(t("complete_save_tournaments"))
