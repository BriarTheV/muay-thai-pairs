# utils/pairing.py - Core pairing logic

import pandas as pd
import re
from typing import List, Tuple, Optional
from dataclasses import dataclass

# Constants
WEIGHT_TOLERANCE = 0.5  # kg
AGE_GAP_WARNING = 2  # years for Juniors
WEIGHT_GAP_PERCENT_WARNING = 5  # %

# Official Muay Thai Weight Categories (kg) - Adults and Juniors
WEIGHT_CLASSES_ADULT = [
    {"name": "First Flyweight", "min": 45.0, "max": 48.0},
    {"name": "Flyweight", "min": 48.0, "max": 51.0},
    {"name": "Bantamweight", "min": 51.0, "max": 54.0},
    {"name": "Featherweight", "min": 54.0, "max": 57.0},
    {"name": "Lightweight", "min": 57.0, "max": 60.0},
    {"name": "Light Welterweight", "min": 60.0, "max": 63.5},
    {"name": "Welterweight", "min": 63.5, "max": 67.0},
    {"name": "Light Middleweight", "min": 67.0, "max": 71.0},
    {"name": "Middleweight", "min": 71.0, "max": 75.0},
    {"name": "Light Heavyweight", "min": 75.0, "max": 81.0},
    {"name": "Cruiserweight", "min": 81.0, "max": 86.0},
    {"name": "Heavyweight", "min": 86.0, "max": 91.0},
    {"name": "Super Heavyweight", "min": 91.0, "max": 999.0},  # 91+
]


# Age-based pairing rules for youths
def get_max_diff_12_15(weight):
    """Max weight difference for 12-15 year olds (ages 12-15)."""
    if weight <= 60:
        return 2.0
    if weight <= 70:
        return 3.0
    if weight <= 80:
        return 4.0
    return 5.0  # Over 80kg


def get_max_diff_16_17(weight):
    """Max weight difference for 16-17 year olds."""
    if weight <= 54:
        return 2.0
    if weight <= 66:
        return 3.0
    if weight <= 74:
        return 4.0
    if weight <= 79:
        return 5.0
    if weight <= 85:
        return 6.0
    return 7.0  # Over 85kg (more lenient for 16-17)


# Legacy functions (deprecated but kept for compatibility)
def get_max_diff_12_14(weight):
    """Legacy function - use get_max_diff_12_15 instead."""
    return get_max_diff_12_15(weight)


def get_max_diff_15_16(weight):
    """Legacy function - use get_max_diff_16_17 instead."""
    return get_max_diff_16_17(weight)


# Class level ordering (higher is more experienced)
CLASS_ORDER = {"А": 4, "Б": 3, "В": 2, "С": 2, "Г": 1, "0 боев": 0}


def get_class_rank(class_level):
    """Get numerical rank for class level."""
    if not class_level or pd.isna(class_level):
        return 0
    # Handle both string and numeric class levels
    class_str = str(class_level).strip().upper()
    return CLASS_ORDER.get(class_str, 0)


# Age-based pairing rules for juniors
JUNIOR_PAIRING_RULES = {
    "12-14": {
        (0, 60): 2.0,  # up to 60kg: 2kg difference
        (60, 70): 3.0,  # 60-70kg: 3kg difference
        (70, 80): 4.0,  # 70-80kg: 4kg difference
        (80, float("inf")): 5.0,  # over 80kg: 5kg difference
    },
    "15-16": {
        (0, 54): 2.0,  # up to 54kg: 2kg difference
        (54, 66): 3.0,  # 54-66kg: 3kg difference
        (66, 74): 4.0,  # 66-74kg: 4kg difference
        (74, 79): 5.0,  # 74-79kg: 5kg difference
        (79, 85): 6.0,  # 79-85kg: 6kg difference
        (85, float("inf")): 7.0,  # over 85kg: 7kg difference (assuming)
    },
}


@dataclass
class Fighter:
    index: int
    name: str
    gender: str
    age: int
    weight_min: float
    weight_max: float
    club: str
    trainer: str
    record: int
    total_fights: int
    weight_class: str
    class_level: Optional[str] = None
    dob: Optional[str] = None
    # Parsed club hierarchy
    club_region: Optional[str] = None
    club_name: Optional[str] = None
    club_subgroup: Optional[str] = None


def parse_club_hierarchy(club_str: str) -> dict:
    """
    Robust club parsing with multiple fallback patterns.

    Supported formats:
    - "Region / Club (Subgroup)" -> e.g., "Тутаев / Пламя (ФК)"
    - "Region / Club" -> e.g., "Тутаев / Пламя"
    - "Club (Subgroup)" -> e.g., "Пламя (ФК)"
    - "Region - Club" -> e.g., "Тутаев - Пламя"
    - "Club" -> e.g., "Пламя"
    """
    import re

    if not club_str or not isinstance(club_str, str):
        return {
            "region": None,
            "club": str(club_str) if club_str else None,
            "subgroup": None,
        }

    club_str = club_str.strip()

    # Pattern 1: "Region / Club (Subgroup)" - e.g., "Тутаев / Пламя (ФК)"
    pattern1 = r"^(.+?)\s*/\s*(.+?)\s*\((.+?)\)$"
    match = re.match(pattern1, club_str)
    if match:
        region, club, subgroup = match.groups()
        return {
            "region": region.strip(),
            "club": club.strip(),
            "subgroup": subgroup.strip(),
        }

    # Pattern 2: "Region / Club" - e.g., "Тутаев / Пламя"
    pattern2 = r"^(.+?)\s*/\s*(.+?)$"
    match = re.match(pattern2, club_str)
    if match:
        region, club = match.groups()
        return {"region": region.strip(), "club": club.strip(), "subgroup": None}

    # Pattern 3: "Club (Subgroup)" - e.g., "Пламя (ФК)"
    pattern3 = r"^(.+?)\s*\((.+?)\)$"
    match = re.match(pattern3, club_str)
    if match:
        club, subgroup = match.groups()
        return {"region": None, "club": club.strip(), "subgroup": subgroup.strip()}

    # Pattern 4: Alternative separators
    separators = [" - ", " | ", " @ ", " in ", " at ", " from "]
    for sep in separators:
        if sep in club_str:
            parts = club_str.split(sep, 1)
            if len(parts) == 2:
                return {
                    "region": parts[0].strip(),
                    "club": parts[1].strip(),
                    "subgroup": None,
                }

    # Pattern 5: Check for subgroup in brackets at end
    bracket_match = re.search(r"(.+?)\s*\((.+?)\)\s*$", club_str)
    if bracket_match and "(" not in bracket_match.group(1):
        club, subgroup = bracket_match.groups()
        return {"region": None, "club": club.strip(), "subgroup": subgroup.strip()}

    # Fallback: Entire string as club name
    return {"region": None, "club": club_str, "subgroup": None}


def validate_club_parsing(df: pd.DataFrame) -> dict:
    """Validate club parsing and report issues."""
    issues = []
    parsed_clubs = []

    for idx, row in df.iterrows():
        club_str = row.get("Club", "")
        parsed = parse_club_hierarchy(club_str)

        parsed_clubs.append(
            {
                "original": club_str,
                "region": parsed["region"],
                "club": parsed["club"],
                "subgroup": parsed["subgroup"],
            }
        )

        # Check for parsing issues
        if not parsed["club"]:
            issues.append(f"Row {idx}: Failed to parse club '{club_str}'")
        elif len(club_str) > 0 and parsed["club"] == club_str and not parsed["region"]:
            # Club parsed as-is, might be missing structure
            pass  # This is acceptable fallback

    return {"valid": len(issues) == 0, "issues": issues, "parsed_clubs": parsed_clubs}

    club_str = club_str.strip()

    # Pattern: "Region / Club (Subgroup)"
    import re

    pattern = r"^(.+?)\s*/\s*(.+?)\s*\((.+?)\)$"
    match = re.match(pattern, club_str)

    if match:
        region, club, subgroup = match.groups()
        return {
            "region": region.strip(),
            "club": club.strip(),
            "subgroup": subgroup.strip(),
        }

    # Pattern: "Region / Club"
    pattern = r"^(.+?)\s*/\s*(.+?)$"
    match = re.match(pattern, club_str)

    if match:
        region, club = match.groups()
        return {"region": region.strip(), "club": club.strip(), "subgroup": None}

    # Fallback: treat as club name only
    return {"region": None, "club": club_str, "subgroup": None}


def check_club_conflict(
    fighter1: Fighter, fighter2: Fighter, conflict_level: int = 1
) -> bool:
    """
    Check if two fighters have a club conflict at the specified level.

    Conflict Levels:
    1: Exact match (original behavior)
    2: Same region + club (ignore subgroup) - RECOMMENDED
    3: Same region only
    4: No conflicts
    """
    if conflict_level == 4:
        return False  # No conflicts

    if not fighter1.club or not fighter2.club:
        return False  # No club info = no conflict

    if conflict_level == 1:
        # Exact string match
        return fighter1.club == fighter2.club

    # For levels 2-3, we need parsed club info
    if conflict_level >= 2:
        # Parse clubs if not already parsed
        if fighter1.club_region is None:
            parsed1 = parse_club_hierarchy(fighter1.club)
            fighter1.club_region = parsed1["region"]
            fighter1.club_name = parsed1["club"]
            fighter1.club_subgroup = parsed1["subgroup"]

        if fighter2.club_region is None:
            parsed2 = parse_club_hierarchy(fighter2.club)
            fighter2.club_region = parsed2["region"]
            fighter2.club_name = parsed2["club"]
            fighter2.club_subgroup = parsed2["subgroup"]

        if conflict_level == 2:
            # Same region AND club (ignore subgroup)
            return (
                fighter1.club_region == fighter2.club_region
                and fighter1.club_name == fighter2.club_name
                and fighter1.club_region is not None
                and fighter1.club_name is not None
            )

        if conflict_level == 3:
            # Same region only
            return (
                fighter1.club_region == fighter2.club_region
                and fighter1.club_region is not None
            )

    return False  # Default: no conflict


def get_weight_class(weight: float) -> str:
    """Get official weight class name for given weight."""
    for category in WEIGHT_CATEGORIES["adult"]:
        if category["min"] <= weight < category["max"]:
            return category["name"]
    return "Не определен"


def get_age_division(age: int) -> str:
    """Get strict age division for pairing validation."""
    if 12 <= age <= 13:
        return "12-13"
    elif 14 <= age <= 15:
        return "14-15"
    elif 16 <= age <= 17:
        return "16-17"
    elif age >= 18:
        return "18+"
    else:
        return "underage"  # Invalid for competition


def get_age_group(age: int) -> str:
    """Get age group for pairing rules (legacy function)."""
    if 12 <= age <= 14:
        return "12-14"
    elif 15 <= age <= 16:
        return "15-16"
    elif 17 <= age <= 18:
        return "17-18"
    else:
        return "adult"


def parse_weight_range(weight_str: str) -> Tuple[float, float]:
    """Parse weight range string like '6-7' or 'до 22'."""
    if not weight_str or pd.isna(weight_str):
        return (0, 999)

    weight_str = str(weight_str).strip().lower()

    # Handle ">= X" (greater than or equal to X)
    if ">=" in weight_str:
        try:
            weight = float(re.search(r">=\s*(\d+(?:\.\d+)?)", weight_str).group(1))
            return (weight, weight)  # Treat as exact weight
        except:
            pass

    # Handle "до X" (up to X) - treat as ">= X"
    if "до" in weight_str:
        try:
            weight = float(re.search(r"до\s*(\d+(?:\.\d+)?)", weight_str).group(1))
            return (weight, weight)  # Treat as exact weight (same as >= X)
        except:
            pass

    # Handle range "X-Y"
    range_match = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)", weight_str)
    if range_match:
        try:
            min_w = float(range_match.group(1))
            max_w = float(range_match.group(2))
            return (min_w, max_w)
        except:
            pass

    # Single weight
    try:
        weight = float(weight_str)
        return (weight, weight)
    except:
        return (0, 999)


def get_weight_category(weight: float) -> str:
    """Get weight category name for given weight."""
    for cat in WEIGHT_CLASSES_ADULT:
        if cat["min"] <= weight < cat["max"]:
            return cat["name"]
        if cat["name"] == "Super Heavyweight" and weight >= 91:
            return cat["name"]
    return None


def create_fighters(df: pd.DataFrame) -> List[Fighter]:
    """Convert DataFrame to list of Fighter objects."""
    fighters = []
    for idx, row in df.iterrows():
        weight_str = row.get("Weight", "")
        weight_min, weight_max = parse_weight_range(weight_str)
        weight_class = get_weight_category((weight_min + weight_max) / 2)

        # Record column contains total fights
        total_fights = int(row.get("Record", row.get("Total_Fights", 0)))
        record = int(row.get("Wins", 0))  # Wins from separate column if available

        # Parse club hierarchy
        club_str = row["Club"]
        club_parsed = parse_club_hierarchy(club_str)

        fighter = Fighter(
            index=idx,
            name=row["Name"],
            gender=row["Gender"],
            age=int(row["Age"]),
            weight_min=weight_min,
            weight_max=weight_max,
            club=club_str,
            trainer=row["Trainer"],
            record=record,
            total_fights=total_fights,
            weight_class=weight_class,
            class_level=row.get("Class"),
            dob=str(row.get("DOB")) if pd.notna(row.get("DOB")) else None,
            club_region=club_parsed["region"],
            club_name=club_parsed["club"],
            club_subgroup=club_parsed["subgroup"],
        )
        fighters.append(fighter)
    return fighters


def is_valid_pair(f1: Fighter, f2: Fighter) -> tuple[bool, str]:
    """Check if two fighters can be paired based on official rules."""
    # Basic safety checks
    if f1.gender != f2.gender:
        return False, "Gender mismatch"

    # Age division check (strict division boundaries)
    if get_age_division(f1.age) != get_age_division(f2.age):
        return (
            False,
            f"Different age divisions: {get_age_division(f1.age)} vs {get_age_division(f2.age)}",
        )

    # Different club (handled separately via check_club_conflict)

    # Different trainer (optional, can be disabled)
    if f1.trainer and f2.trainer and f1.trainer == f2.trainer:
        return False, "Same trainer"

    avg_weight = (f1.weight_min + f2.weight_min) / 2
    weight_diff = abs(f1.weight_min - f2.weight_min)

    # Youths 12-15 (ages 12-13 and 14-15 divisions)
    if get_age_division(f1.age) in ["12-13", "14-15"] and get_age_division(f2.age) in [
        "12-13",
        "14-15",
    ]:
        max_allowed = get_max_diff_12_15(avg_weight)
        if weight_diff <= max_allowed:
            return True, f"Valid youth match ({get_age_division(f1.age)})"
        else:
            return (
                False,
                f"Weight diff {weight_diff}kg exceeds youth limit {max_allowed}kg",
            )

    # Older Youths 16-17
    elif get_age_division(f1.age) in ["16-17"] and get_age_division(f2.age) in [
        "16-17"
    ]:
        max_allowed = get_max_diff_16_17(avg_weight)
        if weight_diff <= max_allowed:
            return True, "Valid older youth match (16-17)"
        else:
            return (
                False,
                f"Weight diff {weight_diff}kg exceeds older youth limit {max_allowed}kg",
            )

    # Adults (18+) - OR youth with undefined categories
    else:
        # Check if either fighter has an undefined weight category (likely youth)
        cat1 = get_weight_category(f1.weight_min)
        cat2 = get_weight_category(f2.weight_min)

        # If both have valid categories, require exact match (adult rules)
        if cat1 and cat2:
            if cat1 == cat2:
                return True, f"Match in {cat1}"
            else:
                return False, f"Different categories: {cat1} vs {cat2}"

        # If either has undefined category (youth or light weights), use floating rules
        else:
            # Use youth floating weight rules for undefined categories
            avg_weight = (f1.weight_min + f2.weight_min) / 2
            weight_diff = abs(f1.weight_min - f2.weight_min)

            # Apply youth weight difference limits
            max_allowed = get_max_diff_12_15(
                avg_weight
            )  # Use 12-15 rules as default for youth
            if weight_diff <= max_allowed:
                return (
                    True,
                    f"Youth match (weight diff: {weight_diff:.1f}kg ≤ {max_allowed}kg)",
                )
            else:
                return (
                    False,
                    f"Youth weight diff {weight_diff:.1f}kg exceeds limit {max_allowed}kg",
                )


def calculate_experience_penalty(exp1: int, exp2: int) -> float:
    """Calculate experience difference penalty using logarithmic scaling."""
    import math

    if exp1 == 0 and exp2 == 0:
        return 0  # Both beginners

    # Handle zero values
    exp1 = max(exp1, 1)
    exp2 = max(exp2, 1)

    # Use log scaling to compress large differences
    ratio = max(exp1, exp2) / min(exp1, exp2)
    log_penalty = math.log(ratio) * 8  # Reduced multiplier for balance

    # Cap maximum penalty
    return min(log_penalty, 25)


def get_experience_tier(fights: int) -> str:
    """Categorize fighters by experience level."""
    if fights == 0:
        return "beginner"
    elif fights <= 5:
        return "novice"
    elif fights <= 15:
        return "intermediate"
    elif fights <= 50:
        return "experienced"
    else:
        return "elite"


def calculate_tier_penalty(tier1: str, tier2: str) -> float:
    """Penalty for mismatched experience tiers."""
    tiers = ["beginner", "novice", "intermediate", "experienced", "elite"]
    try:
        diff = abs(tiers.index(tier1) - tiers.index(tier2))
        return diff * 6  # 6 points per tier difference
    except ValueError:
        return 8  # Default penalty for unknown tiers


def calculate_pair_score(f1: Fighter, f2: Fighter) -> float:
    """Calculate soft score for pair quality (lower is better)."""
    score = 0

    # Weight class match bonus - ONLY for youth categories (12-16)
    if f1.age <= 16 and f2.age <= 16:
        if f1.weight_class and f2.weight_class and f1.weight_class == f2.weight_class:
            score -= 15  # Reduced bonus for youth weight class alignment

    # For adults (17+), weight class is already enforced as hard constraint
    # No bonus needed - rely on other metrics

    # Weight range overlap penalty (prefer tighter overlaps)
    overlap_start = max(f1.weight_min, f2.weight_min)
    overlap_end = min(f1.weight_max, f2.weight_max)
    if overlap_end > overlap_start:
        overlap_size = overlap_end - overlap_start
        # Smaller overlap is better (more precise matching)
        score += (10 - overlap_size) * 1.5  # Reduced multiplier
    else:
        # No overlap (shouldn't happen due to is_valid_pair, but just in case)
        score += 30

    # Age difference penalty (within divisions, smaller differences are better)
    age_diff = abs(f1.age - f2.age)
    if age_diff > 0:  # Any difference within division
        score += age_diff * 2  # Reduced penalty since divisions are strict

    # Experience matching using tiered + logarithmic scoring
    tier1 = get_experience_tier(f1.total_fights)
    tier2 = get_experience_tier(f2.total_fights)
    score += calculate_tier_penalty(tier1, tier2)

    # Additional logarithmic experience penalty
    score += calculate_experience_penalty(f1.total_fights, f2.total_fights)

    # Class level difference penalty (higher for adults)
    class_diff = abs(get_class_rank(f1.class_level) - get_class_rank(f2.class_level))
    if f1.age >= 17 and f2.age >= 17:  # Adults
        score += class_diff * 4  # Higher penalty for adults
    else:  # Youth
        score += class_diff * 2  # Lower penalty for youth

    return score


def pair_fighters(
    df: pd.DataFrame,
    club_conflict_level: int = 3,  # Default to level 3 for this tournament
    sort_strategy: str = "quantity",  # Default to quantity for max pairings
    allow_subgroup_pairings: bool = True,  # Allow different subgroups from same club
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform greedy pairing of fighters based on official rules.

    Args:
        df: DataFrame with fighter data
        club_conflict_level: Level of club conflict checking (1-4)
        sort_strategy: "quality" (experienced first) or "quantity" (maximize pairs)
        allow_subgroup_pairings: Allow different subgroups from same club to pair

    Returns:
        matches_df: DataFrame with paired fighters
        unmatched_df: DataFrame with unpaired fighters
    """
    if df.empty:
        return pd.DataFrame(), df

    fighters = create_fighters(df)

    # Gender-aware sorting: prioritize minority gender first
    males = [f for f in fighters if f.gender == "м"]
    females = [f for f in fighters if f.gender == "ж"]

    # Determine which gender to prioritize (minority gender)
    if len(females) <= len(males):
        # Females are minority or equal - pair them first
        primary_gender, secondary_gender = females, males
    else:
        # Males are minority - pair them first
        primary_gender, secondary_gender = males, females

    # Sort fighters based on strategy, prioritizing minority gender
    def sort_fighter_group(group, strategy):
        if strategy == "quality":
            # Quality-first: Experienced fighters first
            group.sort(
                key=lambda f: (
                    -get_class_rank(f.class_level),  # Higher class first
                    -f.total_fights,  # More fights first
                    f.weight_min,
                )
            )
        elif strategy == "quantity":
            # Quantity-first: Most constrained fighters first
            def get_flexibility_score(fighter: Fighter) -> int:
                """Estimate how many potential valid opponents this fighter has."""
                score = 0
                if fighter.class_level and get_class_rank(fighter.class_level) > 0:
                    score += 2  # Higher class fighters have fewer opponents
                if fighter.total_fights > 10:
                    score += 1  # Experienced fighters have fewer peers
                # Weight range narrowness (smaller range = fewer potential opponents)
                weight_range = fighter.weight_max - fighter.weight_min
                if weight_range < 5:
                    score += 1
                return score

            group.sort(
                key=lambda f: (
                    -get_flexibility_score(f),  # Most constrained first
                    f.age,
                    f.weight_min,
                )
            )
        return group

    # Sort both gender groups
    primary_gender = sort_fighter_group(primary_gender, sort_strategy)
    secondary_gender = sort_fighter_group(secondary_gender, sort_strategy)

    # Combine with primary gender first
    fighters = primary_gender + secondary_gender

    matches = []
    unmatched = []

    while len(fighters) > 1:
        current_fighter = fighters.pop(0)  # Take the first one
        best_opponent = None
        best_opponent_idx = -1

        # Look for the best valid match
        best_score = float("inf")
        for i, opponent in enumerate(fighters):
            # Skip club conflicts based on configured level with subgroup override
            conflict = check_club_conflict(
                current_fighter, opponent, club_conflict_level
            )

            # Tournament-specific override: allow different subgroups from same club
            if (
                conflict
                and allow_subgroup_pairings
                and current_fighter.club_region == opponent.club_region
                and current_fighter.club_name == opponent.club_name
                and current_fighter.club_subgroup != opponent.club_subgroup
                and current_fighter.club_subgroup is not None
                and opponent.club_subgroup is not None
            ):
                conflict = False  # Allow subgroup pairing

            if conflict:
                continue

            # Check if valid match
            is_valid, reason = is_valid_pair(current_fighter, opponent)

            if is_valid:
                score = calculate_pair_score(current_fighter, opponent)
                if score < best_score:
                    best_opponent = opponent
                    best_opponent_idx = i
                    best_score = score

        if best_opponent:
            # Create match
            match = {
                "Match_ID": len(matches) + 1,
                "Red_Corner": current_fighter.name,
                "Red_Club": current_fighter.club,
                "Red_Weight": f">={current_fighter.weight_max}"
                if current_fighter.weight_min <= 0
                or current_fighter.weight_min == current_fighter.weight_max
                else f"{current_fighter.weight_min}-{current_fighter.weight_max}",
                "Red_Age": current_fighter.age,
                "Red_Record": current_fighter.record,
                "Red_Total_Fights": current_fighter.total_fights,
                "Blue_Corner": best_opponent.name,
                "Blue_Club": best_opponent.club,
                "Blue_Weight": f">={best_opponent.weight_max}"
                if best_opponent.weight_min <= 0
                or best_opponent.weight_min == best_opponent.weight_max
                else f"{best_opponent.weight_min}-{best_opponent.weight_max}",
                "Blue_Age": best_opponent.age,
                "Blue_Record": best_opponent.record,
                "Blue_Total_Fights": best_opponent.total_fights,
                "Weight_Diff": abs(
                    current_fighter.weight_min - best_opponent.weight_min
                ),
                "Age_Diff": abs(current_fighter.age - best_opponent.age),
                "Gender": current_fighter.gender,
                "Weight_Class": reason,  # Category or match type
            }
            matches.append(match)
            # Remove opponent from the pool
            fighters.pop(best_opponent_idx)
        else:
            # No match found
            unmatched.append(current_fighter)

    # Handle remaining fighter
    if fighters:
        unmatched.extend(fighters)

    matches_df = pd.DataFrame(matches)
    unmatched_df = pd.DataFrame(
        [
            {
                "Name": f.name,
                "Gender": f.gender,
                "Age": f.age,
                "Weight": f"{f.weight_min}-{f.weight_max}"
                if f.weight_min != f.weight_max
                else f">={f.weight_max}",
                "Club": f.club,
                "Trainer": f.trainer,
                "Record": f.record,
                "Class": f.class_level,
            }
            for f in unmatched
        ]
    )

    return matches_df, unmatched_df
