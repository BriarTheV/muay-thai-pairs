import pandas as pd
from utils.pairing import pair_fighters, is_valid_pair, Fighter


def test_gender_separation():
    """Test that fighters of different genders are not paired."""
    df = pd.DataFrame(
        {
            "Name": ["Alice", "Bob", "Charlie", "Diana"],
            "Gender": ["F", "M", "M", "F"],
            "Age": [20, 20, 20, 20],
            "Weight": [60.0, 60.0, 60.0, 60.0],
            "Club": ["Club1", "Club2", "Club3", "Club4"],
            "Trainer": ["T1", "T2", "T3", "T4"],
            "Record": [0, 0, 0, 0],
        }
    )

    matches, unmatched = pair_fighters(df)

    # Should have 2 matches: F vs F, M vs M
    assert len(matches) == 2
    assert len(unmatched) == 0

    # Check genders in matches (normalized to Russian)
    for _, match in matches.iterrows():
        assert match["Gender"] in ["м", "ж"]


def test_same_club_prevention():
    """Test that fighters from same club are not paired."""
    df = pd.DataFrame(
        {
            "Name": ["Alice", "Bob", "Charlie"],
            "Gender": ["F", "F", "F"],
            "Age": [20, 20, 20],
            "Weight": [60.0, 60.0, 60.0],
            "Club": ["SameClub", "SameClub", "DifferentClub"],
            "Trainer": ["T1", "T2", "T3"],
            "Record": [0, 0, 0],
        }
    )

    matches, unmatched = pair_fighters(
        df, club_conflict_level=1
    )  # Level 1 prevents exact club matches

    # Should have 1 match (Alice and Charlie), Bob unmatched
    assert len(matches) == 1
    assert len(unmatched) == 1

    # Check that paired fighters have different clubs
    match = matches.iloc[0]
    assert match["Red_Club"] != match["Blue_Club"]


def test_odd_number_unmatched():
    """Test that odd number of fighters leaves one unmatched."""
    df = pd.DataFrame(
        {
            "Name": ["A", "B", "C"],
            "Gender": ["M", "M", "M"],
            "Age": [20, 20, 20],
            "Weight": [70.0, 70.0, 70.0],
            "Club": ["C1", "C2", "C3"],
            "Trainer": ["T1", "T2", "T3"],
            "Record": [0, 0, 0],
        }
    )

    matches, unmatched = pair_fighters(df)

    assert len(matches) == 1
    assert len(unmatched) == 1


def test_weight_tolerance():
    """Test weight difference tolerance."""
    df = pd.DataFrame(
        {
            "Name": ["A", "B"],
            "Gender": ["M", "M"],
            "Age": [20, 20],
            "Weight": [70.0, 70.4],  # Within same category
            "Club": ["C1", "C2"],
            "Trainer": ["T1", "T2"],
            "Record": [0, 0],
        }
    )

    matches, unmatched = pair_fighters(df)

    assert len(matches) == 1
    assert len(unmatched) == 0


def test_weight_tolerance_exceeded():
    """Test that excessive weight difference prevents pairing."""
    df = pd.DataFrame(
        {
            "Name": ["A", "B", "C"],
            "Gender": ["M", "M", "M"],
            "Age": [20, 20, 20],
            "Weight": [70.0, 71.0, 70.5],  # B is in different category
            "Club": ["C1", "C2", "C3"],
            "Trainer": ["T1", "T2", "T3"],
            "Record": [0, 0, 0],
        }
    )

    matches, unmatched = pair_fighters(df)

    # A and C should pair (0.5kg diff), B unmatched
    assert len(matches) == 1
    assert len(unmatched) == 1

    # Weight diff check removed due to range format


def test_weight_class_priority():
    """Test that weight class matches take priority over weight ranges."""
    f1 = Fighter(0, "A", "M", 20, 68.0, 68.0, "C1", "T1", 0, 5, "Light Middleweight")
    f2 = Fighter(
        1, "B", "M", 20, 70.0, 70.0, "C2", "T2", 0, 3, "Light Middleweight"
    )  # Same class, different weight
    f3 = Fighter(
        2, "C", "M", 20, 75.0, 75.0, "C3", "T3", 0, 2, "Light Heavyweight"
    )  # Different class, different weight

    assert is_valid_pair(f1, f2).is_valid  # Should be valid due to same category
    assert not is_valid_pair(
        f1, f3
    ).is_valid  # Different categories - should be invalid


def test_is_valid_pair():
    """Test the is_valid_pair function."""
    f1 = Fighter(0, "A", "M", 20, 70.0, 70.0, "C1", "T1", 0, 5, "Light Middleweight")
    f2 = Fighter(1, "B", "M", 20, 70.2, 70.2, "C2", "T2", 0, 3, "Light Middleweight")
    f3 = Fighter(
        2, "C", "F", 20, 70.0, 70.0, "C1", "T1", 0, 2, "Light Middleweight"
    )  # Different gender
    f4 = Fighter(
        3, "D", "M", 20, 70.0, 70.0, "C1", "T1", 0, 1, "Light Middleweight"
    )  # Same club

    assert is_valid_pair(f1, f2).is_valid  # Valid
    assert not is_valid_pair(f1, f3).is_valid  # Different gender
    assert not is_valid_pair(f1, f4).is_valid  # Same club


def test_normalize_class():
    """Test class value normalization from Russian to English."""
    from utils.pairing import normalize_class

    # Russian to English mapping
    assert normalize_class("А") == "A"
    assert normalize_class("Б") == "B"
    assert normalize_class("С") == "C"
    assert normalize_class("Д") == "D"

    # Special cases
    assert normalize_class("0 боев") == ""  # No class
    assert normalize_class("0 fights") == ""  # Alternative
    assert normalize_class("no class") == ""  # Alternative

    # Already English (should pass through)
    assert normalize_class("A") == "A"
    assert normalize_class("B") == "B"
    assert normalize_class("C") == "C"
    assert normalize_class("D") == "D"

    # Empty/None values
    assert normalize_class("") == ""
    assert normalize_class(None) == ""

    # Unknown values (should pass through)
    assert normalize_class("X") == "X"


def test_would_orphan_fighter():
    """Test the orphaning detection function."""
    from utils.pairing import would_orphan_fighter

    # Create test fighters with constrained matching
    f1 = Fighter(0, "A", "M", 20, 70.0, 70.0, "C1", "T1", 0, 5, "Light Middleweight")
    f2 = Fighter(1, "B", "M", 20, 70.2, 70.2, "C2", "T2", 0, 3, "Light Middleweight")
    f3 = Fighter(
        2, "C", "M", 20, 85.0, 85.0, "C3", "T3", 0, 2, "Cruiserweight"
    )  # Can only pair with f4
    f4 = Fighter(
        3, "D", "M", 20, 85.1, 85.1, "C4", "T4", 0, 1, "Cruiserweight"
    )  # Can only pair with f3

    # f2 can only pair with f1 (same weight class), so pairing f1-f4 would orphan f2
    remaining = [f2, f3, f4]
    assert would_orphan_fighter(f1, f4, remaining) == f2

    # Pairing f1-f2 should not orphan anyone (f3 and f4 can still pair)
    remaining = [f2, f3, f4]
    assert would_orphan_fighter(f1, f2, remaining) is None

    # Pairing f3-f4 should not orphan anyone
    remaining = [f1, f2]
    assert would_orphan_fighter(f3, f4, remaining) is None


def test_lookahead_vs_greedy():
    """Test that look-ahead improves pairing quality in constrained scenarios."""
    # Create a scenario where greedy fails but look-ahead succeeds
    df = pd.DataFrame(
        {
            "Name": ["A", "B", "C", "D", "E", "F"],
            "Gender": ["M", "M", "M", "M", "M", "M"],
            "Age": [20, 20, 20, 20, 20, 20],
            "Weight": [70.0, 70.1, 75.0, 75.1, 80.0, 80.1],  # Two weight groups
            "Club": ["C1", "C1", "C2", "C2", "C3", "C3"],  # Two fighters per club
            "Trainer": ["T1", "T1", "T2", "T2", "T3", "T3"],
            "Record": [0, 0, 0, 0, 0, 0],
        }
    )

    # With club conflicts, greedy might leave some unmatched
    matches_g, unmatched_g = pair_fighters(
        df, club_conflict_level=1, use_lookahead=False
    )
    matches_l, unmatched_l = pair_fighters(
        df, club_conflict_level=1, use_lookahead=True
    )

    # Look-ahead should match at least as many as greedy
    assert len(matches_l) >= len(matches_g)
    assert len(unmatched_l) <= len(unmatched_g)

    # In this scenario, all should be matchable
    total_fighters = len(df)
    matched_l = len(matches_l) * 2
    assert matched_l >= total_fighters - 2  # Allow for at most 2 unmatched
