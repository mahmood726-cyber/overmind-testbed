"""Test memory save -> recall -> dream -> prune -> search cycle."""
from __future__ import annotations

from overmind.memory.store import MemoryStore
from overmind.memory.dream_engine import DreamEngine
from overmind.storage.models import MemoryRecord


def _make_memory(mid, mtype, scope, title, content, relevance=0.9):
    return MemoryRecord(
        memory_id=mid, memory_type=mtype, scope=scope,
        title=title, content=content, relevance=relevance,
        confidence=0.8, tags=["test"],
    )


def test_save_and_recall(fresh_db, tmp_path):
    store = MemoryStore(fresh_db, tmp_path / "cp", tmp_path / "logs")
    mem = _make_memory("m1", "project_learning", "proj_a", "Test title", "Test content")
    store.save(mem)
    recalled = store.recall_for_project("proj_a")
    assert len(recalled) == 1
    assert recalled[0].title == "Test title"


def test_dream_merges_duplicates(fresh_db):
    # Titles must share >= 60% word overlap for DreamEngine._similar to merge them.
    # "Calibration slope fix needed" vs "Calibration slope fix required":
    #   shared={calibration, slope, fix}, union={calibration, slope, fix, needed, required}
    #   ratio = 3/5 = 0.60 >= 0.60 => merge triggered.
    mem_a = _make_memory("ma", "heuristic", "global",
                         "Calibration slope fix needed",
                         "Pattern: ValueError in 30 sessions")
    mem_b = _make_memory("mb", "heuristic", "global",
                         "Calibration slope fix required",
                         "Pattern: KeyError in 20 sessions")
    fresh_db.upsert_memory(mem_a)
    fresh_db.upsert_memory(mem_b)

    engine = DreamEngine(fresh_db)
    result = engine.dream()
    assert result["merges"] >= 1
    assert result["memories_after"] < result["memories_before"]


def test_dream_prunes_stale(fresh_db):
    stale = _make_memory("stale1", "project_learning", "old_proj",
                         "Ancient finding", "From 2024", relevance=0.05)
    fresh_db.upsert_memory(stale)

    engine = DreamEngine(fresh_db)
    result = engine.dream()
    assert result["archives"] >= 1

    mem = fresh_db.get_memory("stale1")
    assert mem.status == "archived"


def test_fts5_search(fresh_db, tmp_path):
    store = MemoryStore(fresh_db, tmp_path / "cp", tmp_path / "logs")
    mem = _make_memory("s1", "heuristic", "global",
                       "Calibration slope fix",
                       "Platt scaling improved from 0.194 to 0.874")
    store.save(mem)
    results = store.search("calibration")
    assert len(results) >= 1
    assert results[0].memory_id == "s1"


def test_decay_reduces_relevance(fresh_db, tmp_path):
    store = MemoryStore(fresh_db, tmp_path / "cp", tmp_path / "logs")
    mem = _make_memory("d1", "heuristic", "global", "Test decay", "Content", relevance=1.0)
    store.save(mem)
    store.decay_all(factor=0.5)
    after = store.get("d1")
    assert after.relevance == 0.5
