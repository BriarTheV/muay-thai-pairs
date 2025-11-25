# utils/pairing.py - Core pairing logic

import pandas as pd
import re
from typing import List, Tuple, Optional
from dataclasses import dataclass

# Constants
WEIGHT_TOLERANCE = 0.5  # kg
AGE_GAP_WARNING = 2  # years for Juniors
WEIGHT_GAP_PERCENT_WARNING = 5  # %

# Official Muay Thai Weight Categories (kg)
WEIGHT_CATEGORIES = {
    "adult": [
        {"name": "Первый наилегчайший вес", "min": 45, "max": 48},
        {"name": "Наилегчайший вес", "min": 48, "max": 51},
        {"name": "Легчайший вес", "min": 51, "max": 54},
        {"name": "Полулегкий вес", "min": 54, "max": 57},
        {"name": "Легкий вес", "min": 57, "max": 60},
        {"name": "Первый полусредний вес", "min": 60, "max": 63.5},
        {"name": "Второй полусредний вес", "min": 63.5, "max": 67},
        {"name": "Первый средний вес", "min": 67, "max": 71},
        {"name": "Средний вес", "min": 71, "max": 75},
        {"name": "Полутяжелый вес", "min": 75, "max": 81},
        {"name": "Первый тяжелый вес", "min": 81, "max": 86},
        {"name": "Тяжелый вес", "min": 86, "max": 91},
        {"name": "Супертяжелый вес", "min": 91, "max": float("inf")},
    ]
}

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


def get_weight_difference_limit(age: int, weight: float) -> float:
    """Get maximum allowed weight difference for pairing."""
    age_group = get_age_group(age)
    if age_group == "adult":
        return WEIGHT_TOLERANCE

    rules = JUNIOR_PAIRING_RULES[age_group]
    for (min_w, max_w), limit in rules.items():
        if min_w <= weight < max_w:
            return limit

    return WEIGHT_TOLERANCE  # fallback


def create_fighters(df: pd.DataFrame) -> List[Fighter]:
    """Convert DataFrame to list of Fighter objects."""
    fighters = []
    for idx, row in df.iterrows():
        weight_str = row.get("Weight", "")
        weight_min, weight_max = parse_weight_range(weight_str)
        weight_class = row.get(
            "Weight Class", get_weight_class((weight_min + weight_max) / 2)
        )

        fighter = Fighter(
            index=idx,
            name=row["Name"],
            gender=row["Gender"],
            age=int(row["Age"]),
            weight_min=weight_min,
            weight_max=weight_max,
            club=row["Club"],
            trainer=row["Trainer"],
            record=int(row.get("Record", row.get("Total_Fights", 0))),
            weight_class=weight_class,
            class_level=row.get("Class"),
            dob=str(row.get("DOB")) if pd.notna(row.get("DOB")) else None,
        )
        fighters.append(fighter)
    return fighters


def is_valid_pair(f1: Fighter, f2: Fighter, strict_age: bool = True) -> bool:
    """Check hard constraints for pairing."""
    # Same gender (already grouped)
    if f1.gender != f2.gender:
        return False

    # Age difference check (never more than 1 year apart)
    if strict_age and abs(f1.age - f2.age) > 1:
        return False

    # Different club
    if f1.club and f2.club and f1.club == f2.club:
        return False

    # Different trainer (optional strict mode, but for now always)
    if f1.trainer and f2.trainer and f1.trainer == f2.trainer:
        return False

    # Weight class compatibility (takes precedence)
    if f1.weight_class and f2.weight_class:
        if f1.weight_class == f2.weight_class:
            return True  # Classes match, allow pairing regardless of weight

    # Weight compatibility check (fallback)
    # Use age-based weight difference limits
    weight_diff_limit = max(
        get_weight_difference_limit(f1.age, f1.weight_min),
        get_weight_difference_limit(f2.age, f2.weight_min),
    )

    if abs(f1.weight_min - f2.weight_min) > weight_diff_limit:
        return False

    return True


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


def pair_fighters(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform greedy pairing of fighters.

    Returns:
        normal_matches_df: DataFrame with normal paired fighters
        special_matches_df: DataFrame with special pairs (large age/weight differences)
        unmatched_df: DataFrame with unpaired fighters
    """
    if df.empty:
        return pd.DataFrame(), df

    fighters = create_fighters(df)

    # Sort fighters by age first, then by weight
    fighters.sort(key=lambda f: (f.age, f.weight_min))

    matches = []
    unmatched = []

    # Group by gender and weight class
    groups = {}
    for f in fighters:
        key = (f.gender, f.weight_class)
        if key not in groups:
            groups[key] = []
        groups[key].append(f)

    match_id = 1

    for (gender, weight_class), group in groups.items():
        # Sort by record descending (higher experience first)
        group.sort(key=lambda f: f.record, reverse=True)

        paired_indices = set()

        for i, f1 in enumerate(group):
            if f1.index in paired_indices:
                continue

            best_pair = None
            best_score = float("inf")

            for j, f2 in enumerate(group):
                if i == j or f2.index in paired_indices:
                    continue

                if is_valid_pair(f1, f2):
                    score = calculate_pair_score(f1, f2)
                    if score < best_score:
                        best_score = score
                        best_pair = f2

            if best_pair:
                # Create match
                match = {
                    "Match_ID": match_id,
                    "Red_Corner": f1.name,
                    "Red_Club": f1.club,
                    "Red_Weight": f">={f1.weight_max}"
                    if f1.weight_min <= 0 or f1.weight_min == f1.weight_max
                    else f"{f1.weight_min}-{f1.weight_max}",
                    "Red_Age": f1.age,
                    "Red_Record": f1.record,
                    "Blue_Corner": best_pair.name,
                    "Blue_Club": best_pair.club,
                    "Blue_Weight": f">={best_pair.weight_max}"
                    if best_pair.weight_min <= 0
                    or best_pair.weight_min == best_pair.weight_max
                    else f"{best_pair.weight_min}-{best_pair.weight_max}",
                    "Blue_Age": best_pair.age,
                    "Blue_Record": best_pair.record,
                    "Weight_Diff": abs(
                        (f1.weight_min + f1.weight_max) / 2
                        - (best_pair.weight_min + best_pair.weight_max) / 2
                    ),
                    "Age_Diff": abs(f1.age - best_pair.age),
                    "Gender": gender,
                    "Weight_Class": weight_class,
                }
                matches.append(match)
                paired_indices.add(f1.index)
                paired_indices.add(best_pair.index)
                match_id += 1

        # Add unmatched
        for f in group:
            if f.index not in paired_indices:
                unmatched.append(f)

    # Try to pair remaining unmatched fighters with relaxed constraints
    special_matches = []
    remaining_unmatched = []

    if unmatched:
        # Sort unmatched by age
        unmatched.sort(key=lambda f: f.age)

        paired_indices = set()
        for i, f1 in enumerate(unmatched):
            if f1.index in paired_indices:
                continue

            best_pair = None
            best_score = float("inf")

            for j, f2 in enumerate(unmatched):
                if i == j or f2.index in paired_indices:
                    continue

                if is_valid_pair(f1, f2, strict_age=False):  # Relaxed age check
                    score = calculate_pair_score(f1, f2)
                    if score < best_score:
                        best_score = score
                        best_pair = f2

            if best_pair:
                match_id = len(matches) + len(special_matches) + 1
                match = {
                    "Match_ID": match_id,
                    "Red_Corner": f1.name,
                    "Red_Club": f1.club,
                    "Red_Weight": f">={f1.weight_max}"
                    if f1.weight_min <= 0 or f1.weight_min == f1.weight_max
                    else f"{f1.weight_min}-{f1.weight_max}",
                    "Red_Age": f1.age,
                    "Red_Record": f1.record,
                    "Blue_Corner": best_pair.name,
                    "Blue_Club": best_pair.club,
                    "Blue_Weight": f">={best_pair.weight_max}"
                    if best_pair.weight_min <= 0
                    or best_pair.weight_min == best_pair.weight_max
                    else f"{best_pair.weight_min}-{best_pair.weight_max}",
                    "Blue_Age": best_pair.age,
                    "Blue_Record": best_pair.record,
                    "Weight_Diff": abs(
                        (f1.weight_min + f1.weight_max) / 2
                        - (best_pair.weight_min + best_pair.weight_max) / 2
                    ),
                    "Age_Diff": abs(f1.age - best_pair.age),
                    "Gender": f1.gender,
                    "Weight_Class": f1.weight_class,
                    "Special_Pair": True,  # Mark as special pair
                }
                special_matches.append(match)
                paired_indices.add(f1.index)
                paired_indices.add(best_pair.index)

        # Remaining truly unmatched
        remaining_unmatched = [f for f in unmatched if f.index not in paired_indices]

    matches_df = pd.DataFrame(matches)
    special_matches_df = pd.DataFrame(special_matches)

    # Combine and renumber all pairs
    if not special_matches_df.empty:
        all_matches = pd.concat([matches_df, special_matches_df], ignore_index=True)
        all_matches["Match_ID"] = range(1, len(all_matches) + 1)

        # Split back
        normal_matches = all_matches[all_matches["Special_Pair"] != True].drop(
            columns=["Special_Pair"], errors="ignore"
        )
        special_matches_final = all_matches[all_matches["Special_Pair"] == True].drop(
            columns=["Special_Pair"], errors="ignore"
        )
    else:
        matches_df["Match_ID"] = range(1, len(matches_df) + 1)
        normal_matches = matches_df
        special_matches_final = special_matches_df

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
            for f in remaining_unmatched
        ]
    )

    return normal_matches, special_matches_final, unmatched_df
