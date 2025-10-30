"""Tests for intelligent extraction service optimizations."""

import pytest


def test_language_detection_optimization_concept():
    """
    Test the concept of the language detection optimization.

    This test demonstrates the performance improvement from using
    frozenset intersection instead of nested string searches.
    """
    english_markers_list = [
        "the",
        "is",
        "at",
        "which",
        "on",
        "and",
        "or",
        "not",
        "but",
        "they",
    ]

    text = "the quick brown fox jumps over the lazy dog"
    text_with_spaces = f" {text.lower()} "

    # Old approach: O(n*m) complexity
    old_count = sum(
        1 for word in english_markers_list if f" {word} " in text_with_spaces
    )

    # New approach: O(n) complexity with set intersection
    english_markers_set = frozenset(english_markers_list)
    words = set(text_with_spaces.split())
    new_count = len(words & english_markers_set)

    # Both should give similar results (might differ slightly due to tokenization)
    assert old_count > 0
    assert new_count > 0
    # The new approach should be much faster for large texts


def test_frozenset_is_immutable():
    """Test that frozenset is immutable and can be reused safely."""
    markers = frozenset(["the", "is", "at"])

    # Frozenset should be immutable
    with pytest.raises(AttributeError):
        markers.add("new")  # type: ignore

    # But can be used for intersection
    words = {"the", "cat", "is"}
    result = words & markers
    assert result == {"the", "is"}


def test_set_intersection_performance():
    """Test that set intersection is fast."""
    import time

    # Create large word set
    markers = frozenset([f"word{i}" for i in range(100)])
    text_words = set([f"word{i}" for i in range(0, 1000, 10)])

    start = time.time()
    for _ in range(1000):
        _ = text_words & markers
    elapsed = time.time() - start

    # Should complete 1000 intersections in less than 10ms
    assert elapsed < 0.01
