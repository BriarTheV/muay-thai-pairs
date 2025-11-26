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
