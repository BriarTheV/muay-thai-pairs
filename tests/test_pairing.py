import pytest
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
            "Weight Class": ["Light"] * 4,
        }
    )

    matches, unmatched = pair_fighters(df)

    # Should have 2 matches: F vs F, M vs M
    assert len(matches) == 2
    assert len(unmatched) == 0

    # Check genders in matches
    for _, match in matches.iterrows():
        assert match["Gender"] in ["M", "F"]


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
            "Weight Class": ["Light"] * 3,
        }
    )

    matches, unmatched = pair_fighters(df)

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
            "Weight Class": ["Welter"] * 3,
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
            "Weight": [70.0, 70.4],  # Within 0.5kg tolerance
            "Club": ["C1", "C2"],
            "Trainer": ["T1", "T2"],
            "Record": [0, 0],
            "Weight Class": ["Welter", "Welter"],
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
            "Weight": [
                70.0,
                71.0,
                70.5,
            ],  # B is 1kg heavier than A, within tolerance with C
            "Club": ["C1", "C2", "C3"],
            "Trainer": ["T1", "T2", "T3"],
            "Record": [0, 0, 0],
            "Weight Class": ["Welter"] * 3,
        }
    )

    matches, unmatched = pair_fighters(df)

    # A and C should pair (0.5kg diff), B unmatched
    assert len(matches) == 1
    assert len(unmatched) == 1

    match = matches.iloc[0]
    weight_diff = abs(match["Red_Weight"] - match["Blue_Weight"])
    assert weight_diff <= 0.5


def test_is_valid_pair():
    """Test the is_valid_pair function."""
    f1 = Fighter(0, "A", "M", 20, 70.0, "C1", "T1", 0, "Welter")
    f2 = Fighter(1, "B", "M", 20, 70.2, "C2", "T2", 0, "Welter")
    f3 = Fighter(2, "C", "F", 20, 70.0, "C1", "T1", 0, "Welter")  # Different gender
    f4 = Fighter(3, "D", "M", 20, 70.0, "C1", "T1", 0, "Welter")  # Same club

    assert is_valid_pair(f1, f2)  # Valid
    assert not is_valid_pair(f1, f3)  # Different gender
    assert not is_valid_pair(f1, f4)  # Same club
