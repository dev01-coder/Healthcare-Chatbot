"""Tests for the retrieval engine."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.retrieval.retriever import tokenize, expand_query, _reciprocal_rank_fusion


def test_tokenize_basic():
    tokens = tokenize("What is diabetes?")
    assert "what" in tokens
    assert "is" in tokens
    assert "diabetes" in tokens


def test_tokenize_hyphenated():
    tokens = tokenize("co-morbidity is common")
    assert "co-morbidity" in tokens


def test_expand_query_synonym():
    expanded = expand_query("I have high blood pressure")
    assert "hypertension" in expanded
    assert "elevated bp" in expanded


def test_expand_query_no_match():
    original = "What is the weather today?"
    expanded = expand_query(original)
    assert expanded == original


def test_rrf_fusion_basic():
    list1 = [
        {"text": "doc_a", "source": "s1", "category": "c1"},
        {"text": "doc_b", "source": "s2", "category": "c2"},
    ]
    list2 = [
        {"text": "doc_b", "source": "s2", "category": "c2"},
        {"text": "doc_a", "source": "s1", "category": "c1"},
    ]
    result = _reciprocal_rank_fusion([list1, list2])
    assert len(result) == 2
    # doc_a and doc_b should have similar scores (appear in both lists)
    scores = {r["text"]: r["score"] for r in result}
    assert abs(scores["doc_a"] - scores["doc_b"]) < 0.01


def test_rrf_fusion_one_list():
    list1 = [
        {"text": "doc_a", "source": "s1", "category": "c1"},
        {"text": "doc_b", "source": "s2", "category": "c2"},
    ]
    result = _reciprocal_rank_fusion([list1])
    assert len(result) == 2
    assert result[0]["text"] == "doc_a"  # rank 1 has higher score


def test_rrf_empty_lists():
    result = _reciprocal_rank_fusion([[], []])
    assert result == []


if __name__ == "__main__":
    test_tokenize_basic()
    test_tokenize_hyphenated()
    test_expand_query_synonym()
    test_expand_query_no_match()
    test_rrf_fusion_basic()
    test_rrf_fusion_one_list()
    test_rrf_empty_lists()
    print("All retrieval tests passed!")
