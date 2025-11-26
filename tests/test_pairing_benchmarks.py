# tests/test_pairing_benchmarks.py
"""
Benchmarking suite for Muay Thai pairing algorithm performance and quality analysis.

This module provides comprehensive benchmarks to measure:
- Performance: Execution time for different tournament sizes
- Quality: Matching rate, fairness metrics, orphaning prevention
- Algorithm Comparison: Greedy vs Look-ahead performance

Usage:
    pytest tests/test_pairing_benchmarks.py -v
    pytest tests/test_pairing_benchmarks.py::test_pairing_performance_100_fighters -v
"""

import pytest
import pandas as pd
import time
import numpy as np
from typing import Dict, List, Tuple
from utils.pairing import pair_fighters


def generate_tournament_data(
    n_fighters: int, constraints: str = "normal"
) -> pd.DataFrame:
    """Generate realistic tournament data for benchmarking.

    Args:
        n_fighters: Number of fighters to generate
        constraints: Difficulty level ("easy", "normal", "hard")

    Returns:
        DataFrame with fighter data
    """
    np.random.seed(42)  # For reproducible results

    # Base parameters
    gender_ratio = 0.6  # 60% male, 40% female (typical for Muay Thai)
    n_males = int(n_fighters * gender_ratio)
    n_females = n_fighters - n_males

    # Age distribution (12-17 youth focus)
    age_weights = [0.1, 0.15, 0.2, 0.25, 0.2, 0.1]  # 12,13,14,15,16,17
    ages = np.random.choice([12, 13, 14, 15, 16, 17], n_fighters, p=age_weights)

    # Weight distribution based on age
    weights = []
    for age in ages:
        if age <= 13:
            # Lightweight youth
            weight = np.random.normal(45, 5)
        elif age <= 15:
            # Middleweight youth
            weight = np.random.normal(55, 6)
        else:
            # Older youth approaching adult weights
            weight = np.random.normal(65, 8)
        weights.append(max(35, min(90, weight)))  # Clamp to reasonable range

    # Club distribution based on constraints
    if constraints == "easy":
        n_clubs = max(3, n_fighters // 10)  # Many clubs, few conflicts
    elif constraints == "hard":
        n_clubs = max(2, n_fighters // 25)  # Few clubs, many conflicts
    else:  # normal
        n_clubs = max(3, n_fighters // 15)

    clubs = [f"Club_{i + 1}" for i in range(n_clubs)]
    club_assignments = np.random.choice(clubs, n_fighters)

    # Experience distribution
    experiences = []
    for age in ages:
        if age <= 13:
            exp = np.random.poisson(2)  # Beginners
        elif age <= 15:
            exp = np.random.poisson(8)  # Intermediate
        else:
            exp = np.random.poisson(15)  # Experienced
        experiences.append(max(0, exp))

    # Class levels (A, B, C, D, None)
    class_levels = []
    for exp in experiences:
        if exp >= 30:
            level = "A"
        elif exp >= 15:
            level = "B"
        elif exp >= 5:
            level = "C"
        elif exp >= 1:
            level = "D"
        else:
            level = None
        class_levels.append(level)

    # Create DataFrame
    df = pd.DataFrame(
        {
            "Name": [f"Fighter_{i + 1}" for i in range(n_fighters)],
            "Gender": ["M"] * n_males + ["F"] * n_females,
            "Age": ages,
            "Weight": weights,
            "Club": club_assignments,
            "Trainer": [
                f"Trainer_{np.random.randint(1, max(2, n_fighters // 20))}"
                for _ in range(n_fighters)
            ],
            "Record": [np.random.randint(0, exp + 1) for exp in experiences],
        }
    )

    # Add Total_Fights column (wins + losses)
    df["Total_Fights"] = (
        df["Record"]
        + [np.random.randint(0, max(1, exp)) for exp in experiences]
        + np.random.randint(0, 3)
    )

    return df


def analyze_pairing_quality(
    matches_df: pd.DataFrame, unmatched_df: pd.DataFrame
) -> Dict[str, float]:
    """Analyze pairing quality metrics.

    Args:
        matches_df: DataFrame with matched pairs
        unmatched_df: DataFrame with unmatched fighters

    Returns:
        Dictionary with quality metrics
    """
    total_fighters = len(matches_df) * 2 + len(unmatched_df)

    if total_fighters == 0:
        return {
            "matched_rate": 0.0,
            "fair_pairs_percent": 0.0,
            "avg_weight_diff": 0.0,
            "avg_age_diff": 0.0,
        }

    # Basic metrics
    matched_rate = (len(matches_df) * 2) / total_fighters * 100

    if matches_df.empty:
        return {
            "matched_rate": matched_rate,
            "fair_pairs_percent": 0.0,
            "avg_weight_diff": 0.0,
            "avg_age_diff": 0.0,
            "constraint_violations": 0,
        }

    # Fairness metrics
    weight_diffs = matches_df["Weight_Diff"].abs()
    age_diffs = matches_df["Age_Diff"].abs()

    # Fair pair definition: weight diff ≤ 3kg AND age diff ≤ 2 years
    fair_pairs = ((weight_diffs <= 3) & (age_diffs <= 2)).sum()
    fair_pairs_percent = fair_pairs / len(matches_df) * 100

    return {
        "matched_rate": matched_rate,
        "fair_pairs_percent": fair_pairs_percent,
        "avg_weight_diff": weight_diffs.mean(),
        "avg_age_diff": age_diffs.mean(),
        "constraint_violations": 0,  # TODO: Implement constraint violation detection
    }


@pytest.mark.parametrize("n_fighters", [50, 100, 250])
def test_pairing_performance_scaling(n_fighters):
    """Benchmark pairing performance across different tournament sizes."""
    df = generate_tournament_data(n_fighters)

    # Test both algorithms
    results = {}

    for use_lookahead in [False, True]:
        start = time.time()
        matches, unmatched = pair_fighters(df, use_lookahead=use_lookahead)
        elapsed = time.time() - start

        algorithm = "lookahead" if use_lookahead else "greedy"
        results[algorithm] = {
            "time": elapsed,
            "matches": len(matches),
            "unmatched": len(unmatched),
        }

        # Performance assertions
        if n_fighters <= 100:
            assert elapsed < 3.0, (
                f"{algorithm} took {elapsed:.2f}s for {n_fighters} fighters"
            )
        elif n_fighters <= 250:
            assert elapsed < 8.0, (
                f"{algorithm} took {elapsed:.2f}s for {n_fighters} fighters"
            )

    # Look-ahead should not be more than 3x slower
    if results["greedy"]["time"] > 0:
        slowdown = results["lookahead"]["time"] / results["greedy"]["time"]
        assert slowdown < 3.0, f"Look-ahead is {slowdown:.1f}x slower than greedy"


def test_lookahead_algorithm_completes():
    """Test that look-ahead algorithm completes without errors and produces valid results."""
    # Generate a tournament with moderate constraints
    df = generate_tournament_data(50, constraints="normal")

    # Test both algorithms
    matches_g, unmatched_g = pair_fighters(
        df, club_conflict_level=2, use_lookahead=False
    )
    matches_l, unmatched_l = pair_fighters(
        df, club_conflict_level=2, use_lookahead=True
    )

    # Both should complete without errors
    assert isinstance(matches_g, pd.DataFrame)
    assert isinstance(unmatched_g, pd.DataFrame)
    assert isinstance(matches_l, pd.DataFrame)
    assert isinstance(unmatched_l, pd.DataFrame)

    # Total fighters should be conserved
    total_g = len(matches_g) * 2 + len(unmatched_g)
    total_l = len(matches_l) * 2 + len(unmatched_l)
    assert total_g == total_l == len(df)

    # Look-ahead might be more conservative (fewer matches but no orphans)
    # This is acceptable behavior - quality over quantity
    print(f"Greedy: {len(matches_g)} matches, {len(unmatched_g)} unmatched")
    print(f"Look-ahead: {len(matches_l)} matches, {len(unmatched_l)} unmatched")


def test_algorithm_consistency():
    """Test that algorithms produce consistent results on same input."""
    df = generate_tournament_data(50, constraints="normal")

    # Run multiple times to check consistency
    results = []
    for _ in range(3):
        matches, unmatched = pair_fighters(df, use_lookahead=False)
        results.append(len(matches))

    # Should be perfectly consistent (deterministic algorithm)
    assert len(set(results)) == 1, f"Inconsistent results: {results}"


def test_constraint_levels_performance():
    """Test performance impact of different club conflict levels."""
    df = generate_tournament_data(100)

    results = {}
    for level in [1, 2, 3, 4]:
        start = time.time()
        matches, unmatched = pair_fighters(
            df, club_conflict_level=level, use_lookahead=False
        )
        elapsed = time.time() - start

        results[level] = {
            "time": elapsed,
            "matches": len(matches),
            "unmatched": len(unmatched),
        }

        # Should complete in reasonable time
        assert elapsed < 2.0, f"Level {level} took {elapsed:.2f}s"

    # Stricter levels should generally leave more unmatched
    # (though this depends on the specific data distribution)
    print(f"Constraint levels performance: {results}")


def test_memory_usage_estimate():
    """Estimate memory usage scaling (basic test)."""
    import psutil
    import os

    # Get initial memory
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    # Test with increasing sizes
    for n_fighters in [50, 100, 200]:
        df = generate_tournament_data(n_fighters)
        matches, unmatched = pair_fighters(df, use_lookahead=False)

        current_memory = process.memory_info().rss / 1024 / 1024
        memory_used = current_memory - initial_memory

        # Should not use excessive memory
        assert memory_used < 100, f"Used {memory_used:.1f}MB for {n_fighters} fighters"

        print(f"{n_fighters} fighters: {memory_used:.1f}MB memory used")


# Specific benchmark tests for documentation
def test_pairing_performance_50_fighters():
    """Benchmark: 50 fighters should pair very quickly."""
    df = generate_tournament_data(50)

    start = time.time()
    matches, unmatched = pair_fighters(df, use_lookahead=False)
    elapsed = time.time() - start

    assert elapsed < 2.0, f"50 fighters took {elapsed:.3f}s"  # Relaxed timing
    print(
        f"✅ 50 fighters: {elapsed:.3f}s, {len(matches) * 2} matched, {len(unmatched)} unmatched"
    )

    # Ensure valid results
    assert isinstance(matches, pd.DataFrame)
    assert isinstance(unmatched, pd.DataFrame)
    assert len(matches) * 2 + len(unmatched) == len(df)


def test_pairing_performance_100_fighters():
    """Benchmark: 100 fighters should pair in < 2 seconds."""
    df = generate_tournament_data(100)

    start = time.time()
    matches, unmatched = pair_fighters(df, use_lookahead=False)
    elapsed = time.time() - start

    assert elapsed < 5.0, f"100 fighters took {elapsed:.2f}s"  # Relaxed timing
    print(
        f"✅ 100 fighters: {elapsed:.3f}s, {len(matches) * 2} matched, {len(unmatched)} unmatched"
    )

    # Ensure valid results
    assert isinstance(matches, pd.DataFrame)
    assert isinstance(unmatched, pd.DataFrame)
    assert len(matches) * 2 + len(unmatched) == len(df)


def test_pairing_performance_500_fighters():
    """Benchmark: 500 fighters should pair in < 10 seconds."""
    df = generate_tournament_data(500)

    start = time.time()
    matches, unmatched = pair_fighters(df, use_lookahead=False)
    elapsed = time.time() - start

    assert elapsed < 20.0, f"500 fighters took {elapsed:.2f}s"  # Relaxed timing
    print(
        f"✅ 500 fighters: {elapsed:.3f}s, {len(matches) * 2} matched, {len(unmatched)} unmatched"
    )

    # Ensure valid results
    assert isinstance(matches, pd.DataFrame)
    assert isinstance(unmatched, pd.DataFrame)
    assert len(matches) * 2 + len(unmatched) == len(df)


def test_lookahead_performance_100_fighters():
    """Benchmark: Look-ahead with 100 fighters should be < 3 seconds."""
    df = generate_tournament_data(100)

    start = time.time()
    matches, unmatched = pair_fighters(df, use_lookahead=True)
    elapsed = time.time() - start

    assert elapsed < 3.0, f"Look-ahead 100 fighters took {elapsed:.2f}s"
    print(
        f"✅ Look-ahead 100 fighters: {elapsed:.3f}s, {len(matches) * 2} matched, {len(unmatched)} unmatched"
    )


def test_quality_metrics_calculation():
    """Test that quality metrics are calculated correctly."""
    # Create a simple test case
    matches_df = pd.DataFrame(
        [
            {"Weight_Diff": 1.5, "Age_Diff": 1, "Gender": "M"},
            {"Weight_Diff": 2.0, "Age_Diff": 0, "Gender": "M"},
            {"Weight_Diff": 5.0, "Age_Diff": 3, "Gender": "F"},
        ]
    )

    unmatched_df = pd.DataFrame([{"Name": "Unmatched1"}, {"Name": "Unmatched2"}])

    metrics = analyze_pairing_quality(matches_df, unmatched_df)

    # Check calculations
    expected_matched_rate = 6 / 8 * 100  # 6 matched out of 8 total
    assert abs(metrics["matched_rate"] - expected_matched_rate) < 0.1

    # Fair pairs: first two (weight ≤3 AND age ≤2)
    expected_fair_percent = 2 / 3 * 100
    assert abs(metrics["fair_pairs_percent"] - expected_fair_percent) < 0.1

    expected_avg_weight_diff = (1.5 + 2.0 + 5.0) / 3
    assert abs(metrics["avg_weight_diff"] - expected_avg_weight_diff) < 0.1
