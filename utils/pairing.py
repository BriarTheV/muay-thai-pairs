# utils/pairing.py - Core pairing logic

import pandas as pd
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
import re
from .type_helpers import safe_int_conversion


# Constants for class rankings and weight categories
CLASS_ORDER = {
    "A": 4,  # Highest class
    "B": 3,
    "C": 2,
    "D": 1,  # Lowest class
}

WEIGHT_CATEGORIES = {
    "adult": [
        {"name": "Light Fly", "min": 0, "max": 51.5},
        {"name": "Fly", "min": 51.5, "max": 54},
        {"name": "Bantam", "min": 54, "max": 57},
        {"name": "Feather", "min": 57, "max": 60},
        {"name": "Light", "min": 60, "max": 63.5},
        {"name": "Super Light", "min": 63.5, "max": 67},
        {"name": "Welter", "min": 67, "max": 71},
        {"name": "Super Welter", "min": 71, "max": 75},
        {"name": "Middle", "min": 75, "max": 81},
        {"name": "Super Middle", "min": 81, "max": 86},
        {"name": "Light Heavy", "min": 86, "max": 91},
        {"name": "Cruiser", "min": 91, "max": 100},
        {"name": "Heavy", "min": 100, "max": 999},
    ]
}

WEIGHT_CLASSES_ADULT = WEIGHT_CATEGORIES["adult"]


def find_weight_category_by_max(max_weight: float) -> Optional[Dict[str, Any]]:
    """Find weight category by its maximum weight limit.

    Used to correctly parse "до X" (up to X kg) expressions by identifying
    the IFMA weight category that has X as its upper limit.

    Args:
        max_weight: The upper weight limit (e.g., 54 for Fly category)

    Returns:
        Category dict {'name': str, 'min': float, 'max': float} or None if not found

    Examples:
        >>> find_weight_category_by_max(54)
        {'name': 'Fly', 'min': 51.5, 'max': 54}
        >>> find_weight_category_by_max(55)  # No exact match
        None
    """
    for category in WEIGHT_CLASSES_ADULT:
        # Use small epsilon for floating point comparison
        if abs(category["max"] - max_weight) < 0.01:
            return category
    return None


def normalize_gender(gender: str) -> str:
    """Normalize gender values to Russian standard (м/ж)."""
    if not gender or pd.isna(gender):
        return ""

    gender_str = str(gender).strip().lower()

    # English to Russian mapping
    if gender_str in ["m", "male", "man", "мужской"]:
        return "м"
    elif gender_str in ["f", "female", "woman", "женский"]:
        return "ж"

    # Already Russian
    if gender_str in ["м", "ж"]:
        return gender_str

    # Unknown - return as-is but warn
    return gender_str


def normalize_class(class_value: str) -> str:
    """Normalize class values to English standard (A/B/C/D/empty)."""
    if not class_value or pd.isna(class_value):
        return ""

    class_str = str(class_value).strip()

    # Russian to English mapping
    if class_str == "А":
        return "A"
    elif class_str == "Б":
        return "B"
    elif class_str == "С":
        return "C"
    elif class_str == "Д":
        return "D"
    elif class_str in ["0 боев", "0 fights", "no class"]:
        return ""  # No class

    # Already English or unknown - return as-is
    return class_str


@dataclass
class ValidationResult:
    """Enhanced validation result with detailed feedback."""

    is_valid: bool
    message: str
    severity: str  # "info", "warning", "error"
    suggested_fix: Optional[str] = None

    def __str__(self) -> str:
        """String representation for display."""
        emoji = {"info": "ℹ️", "warning": "⚠️", "error": "❌"}.get(self.severity, "❓")

        result = f"{emoji} {self.message}"
        if self.suggested_fix:
            result += f"\n💡 Suggested fix: {self.suggested_fix}"
        return result


def get_max_diff_12_15(avg_weight: float) -> float:
    """Get maximum allowed weight difference for 12-15 age group."""
    if avg_weight <= 40:
        return 2.0
    elif avg_weight <= 50:
        return 3.0
    else:
        return 4.0


def get_max_diff_16_17(avg_weight: float) -> float:
    """Get maximum allowed weight difference for 16-17 age group."""
    if avg_weight <= 50:
        return 3.0
    elif avg_weight <= 60:
        return 4.0
    else:
        return 5.0


def get_class_rank(class_level):
    """Get numerical rank for class level."""
    if not class_level or pd.isna(class_level):
        return 0
    # Handle both string and numeric class levels
    class_str = str(class_level).strip().upper()
    return CLASS_ORDER.get(class_str, 0)


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
            # Only conflict if BOTH fighters have valid region AND club data AND they match
            return (
                fighter1.club_region is not None
                and fighter1.club_name is not None
                and fighter2.club_region is not None
                and fighter2.club_name is not None
                and fighter1.club_region == fighter2.club_region
                and fighter1.club_name == fighter2.club_name
            )

        if conflict_level == 3:
            # Same region only
            # Only conflict if BOTH fighters have valid region data AND they match
            return (
                fighter1.club_region is not None
                and fighter2.club_region is not None
                and fighter1.club_region == fighter2.club_region
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
    if pd.isna(weight_str) or weight_str == "":
        return (0, 999)  # Default wide range

    weight_str = str(weight_str).lower().strip()

    # Russian "до" (under/up to) - NOW IDENTIFIES WEIGHT CATEGORY
    if "до" in weight_str:
        try:
            max_weight = float(re.search(r"до\s*(\d+(?:\.\d+)?)", weight_str).group(1))

            # Try to find matching IFMA weight category first
            category = find_weight_category_by_max(max_weight)
            if category:
                return (category["min"], category["max"])

            # Fallback: treat as range (0, max_weight) for backward compatibility
            return (0, max_weight)
        except (ValueError, AttributeError):
            pass

    # Greater than or equal (>=)
    if ">=" in weight_str or "≥" in weight_str:
        try:
            min_weight = float(
                re.search(r"[≥>=]\s*(\d+(?:\.\d+)?)", weight_str).group(1)
            )
            return (min_weight, 999)
        except (ValueError, AttributeError):
            pass

    # Less than or equal (<=)
    if "<=" in weight_str or "≤" in weight_str:
        try:
            max_weight = float(
                re.search(r"[≤<=]\s*(\d+(?:\.\d+)?)", weight_str).group(1)
            )
            return (0, max_weight)
        except (ValueError, AttributeError):
            pass

    # Greater than (>)
    if ">" in weight_str and ">=" not in weight_str:
        try:
            min_weight = float(re.search(r">\s*(\d+(?:\.\d+)?)", weight_str).group(1))
            return (min_weight + 0.1, 999)  # Slightly above to avoid equality
        except (ValueError, AttributeError):
            pass

    # Less than (<)
    if "<" in weight_str and "<=" not in weight_str:
        try:
            max_weight = float(re.search(r"<\s*(\d+(?:\.\d+)?)", weight_str).group(1))
            return (0, max_weight - 0.1)  # Slightly below to avoid equality
        except (ValueError, AttributeError):
            pass

    # Range X-Y
    range_match = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)", weight_str)
    if range_match:
        try:
            min_weight = float(range_match.group(1))
            max_weight = float(range_match.group(2))
            return (min_weight, max_weight)
        except (ValueError, TypeError):
            pass

    # Single weight
    try:
        weight = float(weight_str)
        return (weight, weight)
    except (ValueError, TypeError):
        return (0, 999)  # Fallback


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

        # Record column contains total fights - ensure robust type conversion
        record_val = row.get("Record", row.get("Total_Fights", 0))
        total_fights = safe_int_conversion(record_val)

        # Wins from separate column if available - ensure robust type conversion
        wins_val = row.get("Wins", 0)
        record = safe_int_conversion(wins_val)

        # Parse club hierarchy
        club_str = row["Club"]
        club_parsed = parse_club_hierarchy(club_str)

        fighter = Fighter(
            index=idx,
            name=row["Name"],
            gender=normalize_gender(row["Gender"]),
            age=int(row["Age"]),
            weight_min=weight_min,
            weight_max=weight_max,
            club=club_str,
            trainer=row["Trainer"],
            record=record,
            total_fights=total_fights,
            weight_class=weight_class,
            class_level=normalize_class(row.get("Class")),
            dob=str(row.get("DOB")) if pd.notna(row.get("DOB")) else None,
            club_region=club_parsed["region"],
            club_name=club_parsed["club"],
            club_subgroup=club_parsed["subgroup"],
        )
        fighters.append(fighter)
    return fighters


def is_valid_pair(f1: Fighter, f2: Fighter) -> ValidationResult:
    """Check if two fighters can be paired based on official rules with detailed feedback."""
    # Basic safety checks
    if f1.gender != f2.gender:
        return ValidationResult(
            is_valid=False,
            message=f"Gender mismatch: {f1.name} ({f1.gender}) vs {f2.name} ({f2.gender})",
            severity="error",
            suggested_fix="Pair fighters of the same gender only",
        )

    # Age division check (strict division boundaries)
    f1_age_div = get_age_division(f1.age)
    f2_age_div = get_age_division(f2.age)
    if f1_age_div != f2_age_div:
        return ValidationResult(
            is_valid=False,
            message=f"Different age divisions: {f1.name} ({f1_age_div}) vs {f2.name} ({f2_age_div})",
            severity="error",
            suggested_fix="Pair fighters from the same age division only",
        )

    # Different trainer (optional, can be disabled)
    if f1.trainer and f2.trainer and f1.trainer == f2.trainer:
        return ValidationResult(
            is_valid=False,
            message=f"Same trainer conflict: Both {f1.name} and {f2.name} train with '{f1.trainer}'",
            severity="warning",
            suggested_fix="Consider pairing with different trainers for fair competition",
        )

    avg_weight = (f1.weight_min + f2.weight_min) / 2
    weight_diff = abs(f1.weight_min - f2.weight_min)

    # Youths 12-15 (ages 12-13 and 14-15 divisions)
    if f1_age_div in ["12-13", "14-15"] and f2_age_div in ["12-13", "14-15"]:
        max_allowed = get_max_diff_12_15(avg_weight)
        if weight_diff <= max_allowed:
            return ValidationResult(
                is_valid=True,
                message=f"✅ Valid youth match ({f1_age_div}): weight diff {weight_diff:.1f}kg ≤ {max_allowed}kg",
                severity="info",
            )
        else:
            return ValidationResult(
                is_valid=False,
                message=f"Weight difference {weight_diff:.1f}kg exceeds youth limit {max_allowed}kg for {f1_age_div}",
                severity="error",
                suggested_fix=f"Find a {f1.name} opponent within {max_allowed}kg weight difference",
            )

    # Older Youths 16-17
    elif f1_age_div in ["16-17"] and f2_age_div in ["16-17"]:
        max_allowed = get_max_diff_16_17(avg_weight)
        if weight_diff <= max_allowed:
            return ValidationResult(
                is_valid=True,
                message=f"✅ Valid older youth match (16-17): weight diff {weight_diff:.1f}kg ≤ {max_allowed}kg",
                severity="info",
            )
        else:
            return ValidationResult(
                is_valid=False,
                message=f"Weight difference {weight_diff:.1f}kg exceeds older youth limit {max_allowed}kg",
                severity="error",
                suggested_fix=f"Find a {f1.name} opponent within {max_allowed}kg weight difference",
            )

    # Adults (18+) - OR youth with undefined categories
    else:
        # Check if either fighter has an undefined weight category (likely youth)
        cat1 = get_weight_category(f1.weight_min)
        cat2 = get_weight_category(f2.weight_min)

        # If both have valid categories, require exact match (adult rules)
        if cat1 and cat2:
            if cat1 == cat2:
                return ValidationResult(
                    is_valid=True,
                    message=f"✅ Adult match in {cat1} category",
                    severity="info",
                )
            else:
                return ValidationResult(
                    is_valid=False,
                    message=f"Different weight categories: {f1.name} ({cat1}) vs {f2.name} ({cat2})",
                    severity="error",
                    suggested_fix=f"Pair {f1.name} with another fighter in {cat1} category",
                )

        # If either has undefined category (youth or light weights), use floating rules
        else:
            # Use youth floating weight rules for undefined categories
            max_allowed = get_max_diff_12_15(
                avg_weight
            )  # Use 12-15 rules as default for youth
            if weight_diff <= max_allowed:
                return ValidationResult(
                    is_valid=True,
                    message=f"✅ Youth match (undefined category): weight diff {weight_diff:.1f}kg ≤ {max_allowed}kg",
                    severity="info",
                    suggested_fix="Consider verifying weight categories for future tournaments",
                )
            else:
                return ValidationResult(
                    is_valid=False,
                    message=f"Youth weight difference {weight_diff:.1f}kg exceeds limit {max_allowed}kg",
                    severity="error",
                    suggested_fix=f"Find a {f1.name} opponent within {max_allowed}kg weight difference",
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


def would_orphan_fighter(
    f1: Fighter, f2: Fighter, remaining: List[Fighter]
) -> Optional[Fighter]:
    """Check if pairing f1-f2 would leave any remaining fighter with no valid opponents.

    This implements the look-ahead heuristic to prevent orphaning constrained fighters.

    Args:
        f1: First fighter in proposed pair
        f2: Second fighter in proposed pair
        remaining: List of fighters still available for pairing

    Returns:
        The orphaned fighter if this pairing would orphan someone, None if safe to pair
    """
    # Create temporary list without the proposed pair
    temp_remaining = [f for f in remaining if f not in (f1, f2)]

    # Check each remaining fighter to see if they would be orphaned
    for fighter in temp_remaining:
        # Count how many valid opponents this fighter has left
        valid_opponents = 0

        for opponent in temp_remaining:
            if opponent == fighter:
                continue

            # Check if this pairing is valid
            if is_valid_pair(fighter, opponent).is_valid:
                valid_opponents += 1

        # If this fighter has no valid opponents left, they would be orphaned
        if valid_opponents == 0:
            return fighter  # This fighter would be orphaned

    return None  # Safe to proceed with this pairing


def pair_fighters(
    df: pd.DataFrame,
    club_conflict_level: int = 3,  # Default to level 3 for this tournament
    sort_strategy: str = "quantity",  # Default to quantity for max pairings
    allow_subgroup_pairings: bool = True,  # Allow different subgroups from same club
    use_lookahead: bool = False,  # Use look-ahead heuristic to prevent orphaning
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform pairing of fighters based on official rules.

    Uses greedy algorithm by default, or greedy + look-ahead heuristic when enabled.

    Args:
        df: DataFrame with fighter data
        club_conflict_level: Level of club conflict checking (1-4)
        sort_strategy: "quality" (experienced first) or "quantity" (maximize pairs)
        allow_subgroup_pairings: Allow different subgroups from same club to pair
        use_lookahead: Use look-ahead heuristic to prevent orphaning constrained fighters

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
            validation = is_valid_pair(current_fighter, opponent)

            if validation.is_valid:
                score = calculate_pair_score(current_fighter, opponent)
                if score < best_score:
                    best_opponent = opponent
                    best_opponent_idx = i
                    best_score = score

        if best_opponent:
            # Look-ahead check: ensure this pairing doesn't orphan constrained fighters
            if use_lookahead:
                orphaned = would_orphan_fighter(
                    current_fighter, best_opponent, fighters
                )
                if orphaned:
                    # This pairing would orphan someone - try to find an alternative
                    # Look for the next best opponent that doesn't cause orphaning
                    alternative_found = False

                    # Get all valid opponents sorted by score (skip the best one we already tried)
                    scored_opponents = []
                    for i, opponent in enumerate(fighters):
                        if opponent == best_opponent:
                            continue  # Skip the one we already tried

                        # Check club conflicts
                        conflict = check_club_conflict(
                            current_fighter, opponent, club_conflict_level
                        )

                        # Tournament-specific override for subgroups
                        if (
                            conflict
                            and allow_subgroup_pairings
                            and current_fighter.club_region == opponent.club_region
                            and current_fighter.club_name == opponent.club_name
                            and current_fighter.club_subgroup != opponent.club_subgroup
                            and current_fighter.club_subgroup is not None
                            and opponent.club_subgroup is not None
                        ):
                            conflict = False

                        if conflict:
                            continue

                        # Check if valid match
                        validation = is_valid_pair(current_fighter, opponent)
                        if validation.is_valid:
                            score = calculate_pair_score(current_fighter, opponent)
                            scored_opponents.append((opponent, score, i))

                    # Sort by score (best first)
                    scored_opponents.sort(key=lambda x: x[1])

                    # Try alternatives
                    for alt_opponent, alt_score, alt_idx in scored_opponents:
                        if not would_orphan_fighter(
                            current_fighter, alt_opponent, fighters
                        ):
                            # Found a safe alternative
                            best_opponent = alt_opponent
                            best_opponent_idx = alt_idx
                            alternative_found = True
                            break

                    if not alternative_found:
                        # No safe pairing found - mark current fighter as unmatched
                        unmatched.append(current_fighter)
                        continue

            # Create match (either original or alternative)
            match = {
                "Match_ID": len(matches) + 1,
                "Red_Corner": current_fighter.name,
                "Red_Club": current_fighter.club,
                "Red_Weight": f">={current_fighter.weight_max}"
                if current_fighter.weight_min <= 0
                or current_fighter.weight_min == current_fighter.weight_max
                else f"{current_fighter.weight_min}-{current_fighter.weight_max}",
                "Red_Age": current_fighter.age,
                "Red_Record": safe_int_conversion(current_fighter.record),
                "Red_Total_Fights": safe_int_conversion(current_fighter.total_fights),
                "Blue_Corner": best_opponent.name,
                "Blue_Club": best_opponent.club,
                "Blue_Weight": f">={best_opponent.weight_max}"
                if best_opponent.weight_min <= 0
                or best_opponent.weight_min == best_opponent.weight_max
                else f"{best_opponent.weight_min}-{best_opponent.weight_max}",
                "Blue_Age": best_opponent.age,
                "Blue_Record": safe_int_conversion(best_opponent.record),
                "Blue_Total_Fights": safe_int_conversion(best_opponent.total_fights),
                "Weight_Diff": abs(
                    current_fighter.weight_min - best_opponent.weight_min
                ),
                "Age_Diff": abs(current_fighter.age - best_opponent.age),
                "Gender": current_fighter.gender,
                "Weight_Class": current_fighter.weight_class
                or get_weight_category(current_fighter.weight_min),
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
                "Record": safe_int_conversion(f.record),
                "Class": f.class_level,
            }
            for f in unmatched
        ]
    )

    return matches_df, unmatched_df
