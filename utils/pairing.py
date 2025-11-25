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
def get_max_diff_12_14(weight):
    """Max weight difference for 12-14 year olds."""
    if weight <= 60:
        return 2.0
    if weight <= 70:
        return 3.0
    if weight <= 80:
        return 4.0
    return 5.0  # Over 80kg


def get_max_diff_15_16(weight):
    """Max weight difference for 15-16 year olds."""
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
    return 99.0  # Over 85kg (open)


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
    weight_class: str
    class_level: Optional[str] = None
    dob: Optional[str] = None


def get_weight_class(weight: float) -> str:
    """Get official weight class name for given weight."""
    for category in WEIGHT_CATEGORIES["adult"]:
        if category["min"] <= weight < category["max"]:
            return category["name"]
    return "Не определен"


def get_age_group(age: int) -> str:
    """Get age group for pairing rules."""
    if 12 <= age <= 14:
        return "12-14"
    elif 15 <= age <= 16:
        return "15-16"
    else:
        return "adult"


def parse_weight_range(weight_str: str) -> Tuple[float, float]:
    """Parse weight range string like '6-7' or 'до 22'."""
    if not weight_str or pd.isna(weight_str):
        return (0, 999)

    weight_str = str(weight_str).strip().lower()

    # Handle "до X" (up to X)
    if "до" in weight_str:
        try:
            max_weight = float(re.search(r"до\s*(\d+(?:\.\d+)?)", weight_str).group(1))
            return (0, max_weight)
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
        weight = float(row.get("Weight", 0))
        weight_class = get_weight_category(weight)

        fighter = Fighter(
            index=idx,
            name=row["Name"],
            gender=row["Gender"],
            age=int(row["Age"]),
            weight_min=weight,
            weight_max=weight,
            club=row["Club"],
            trainer=row["Trainer"],
            record=int(row.get("Record", row.get("Total_Fights", 0))),
            weight_class=weight_class,
            class_level=row.get("Class"),
            dob=str(row.get("DOB")) if pd.notna(row.get("DOB")) else None,
        )
        fighters.append(fighter)
    return fighters


def is_valid_pair(f1: Fighter, f2: Fighter) -> tuple[bool, str]:
    """Check if two fighters can be paired based on official rules."""
    # Basic safety checks
    if f1.gender != f2.gender:
        return False, "Gender mismatch"

    # Age gap check (>2 years invalid)
    if abs(f1.age - f2.age) > 2:
        return False, "Age gap too large"

    # Different club
    if f1.club and f2.club and f1.club == f2.club:
        return False, "Same club"

    # Different trainer
    if f1.trainer and f2.trainer and f1.trainer == f2.trainer:
        return False, "Same trainer"

    avg_weight = (f1.weight_min + f2.weight_min) / 2
    weight_diff = abs(f1.weight_min - f2.weight_min)

    # Youths 12-14
    if 12 <= f1.age <= 14 and 12 <= f2.age <= 14:
        max_allowed = get_max_diff_12_14(avg_weight)
        if weight_diff <= max_allowed:
            return True, "Valid 12-14 match"
        else:
            return False, f"Weight diff {weight_diff}kg exceeds limit {max_allowed}kg"

    # Youths 15-16
    elif 15 <= f1.age <= 16 and 15 <= f2.age <= 16:
        max_allowed = get_max_diff_15_16(avg_weight)
        if weight_diff <= max_allowed:
            return True, "Valid 15-16 match"
        else:
            return False, f"Weight diff {weight_diff}kg exceeds limit {max_allowed}kg"

    # Juniors (17-18) & Adults (19+)
    else:
        # Must be in SAME weight category
        cat1 = get_weight_category(f1.weight_min)
        cat2 = get_weight_category(f2.weight_min)

        if cat1 and cat1 == cat2:
            return True, f"Match in {cat1}"

        return False, f"Different categories: {cat1} vs {cat2}"


def calculate_pair_score(f1: Fighter, f2: Fighter) -> float:
    """Calculate soft score for pair quality (lower is better)."""
    score = 0

    # Weight class match bonus (lower score is better)
    if f1.weight_class and f2.weight_class and f1.weight_class == f2.weight_class:
        score -= 20  # Significant bonus for class match

    # Weight range overlap penalty
    # Calculate overlap quality (prefer tighter overlaps)
    overlap_start = max(f1.weight_min, f2.weight_min)
    overlap_end = min(f1.weight_max, f2.weight_max)
    if overlap_end > overlap_start:
        overlap_size = overlap_end - overlap_start
        # Smaller overlap is better (more precise matching)
        score += (10 - overlap_size) * 2
    else:
        # No overlap (shouldn't happen due to is_valid_pair, but just in case)
        score += 50

    # Age difference penalty
    age_diff = abs(f1.age - f2.age)
    if age_diff > AGE_GAP_WARNING:
        score += (age_diff - AGE_GAP_WARNING) * 5

    # Experience difference penalty (prefer similar experience)
    exp_diff = abs(f1.record - f2.record)
    score += exp_diff * 2

    return score


def pair_fighters(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform greedy pairing of fighters based on official rules.

    Returns:
        matches_df: DataFrame with paired fighters
        unmatched_df: DataFrame with unpaired fighters
    """
    if df.empty:
        return pd.DataFrame(), df

    fighters = create_fighters(df)

    # Sort fighters by Gender, Age, Weight
    fighters.sort(key=lambda f: (f.gender, f.age, f.weight_min))

    matches = []
    unmatched = []

    while len(fighters) > 1:
        current_fighter = fighters.pop(0)  # Take the first one
        best_opponent = None
        best_opponent_idx = -1

        # Look for the first valid match
        for i, opponent in enumerate(fighters):
            # Skip same club
            if (
                current_fighter.club
                and opponent.club
                and current_fighter.club == opponent.club
            ):
                continue

            # Check if valid match
            is_valid, reason = is_valid_pair(current_fighter, opponent)

            if is_valid:
                best_opponent = opponent
                best_opponent_idx = i
                break  # Found the first valid match (greedy approach)

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
                "Blue_Corner": best_opponent.name,
                "Blue_Club": best_opponent.club,
                "Blue_Weight": f">={best_opponent.weight_max}"
                if best_opponent.weight_min <= 0
                or best_opponent.weight_min == best_opponent.weight_max
                else f"{best_opponent.weight_min}-{best_opponent.weight_max}",
                "Blue_Age": best_opponent.age,
                "Blue_Record": best_opponent.record,
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
