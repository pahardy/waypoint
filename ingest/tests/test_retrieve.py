import pytest
from test_load import META, SOURCE, StubEmbed, chunk

from waypoint_ingest.load import embedding_text, load_source
from waypoint_ingest.retrieve import Hit, fuse, keyword_hits, search

CHUNKS = [
    chunk("RAC 1.1", "Set the altimeter to the aerodrome setting before take-off."),
    chunk("RAC 1.2", "Cruising altitudes depend on the magnetic track."),
    chunk("LRA 3.2", "A person who cheats fails the examination."),
]


@pytest.fixture
def loaded(conn):
    load_source(conn, SOURCE, META, CHUNKS, StubEmbed(), model="stub")
    return conn


def hit(chunk_id):
    return Hit(chunk_id, "aim", chunk_id, "1", 0.0, "")


def ids(hits):
    return [h.id for h in hits]


def test_vector_search_returns_the_nearest_chunk_with_its_edition(loaded):
    stub = StubEmbed()
    hits = search(loaded, embedding_text(CHUNKS[1]), stub, "vector", limit=2)
    assert (hits[0].id, hits[0].edition) == ("aim:RAC 1.2:0", "2026-2")
    assert hits[0].score == pytest.approx(1.0)
    assert stub.calls[0][1] == "query"


def test_keyword_search_matches_any_word_of_the_question(loaded):
    hits = keyword_hits(loaded, "What happens if I cheat on my exam?", limit=5)
    assert ids(hits) == ["aim:LRA 3.2:0"]


def test_keyword_search_stems_words_and_ranks_better_matches_first(loaded):
    hits = keyword_hits(loaded, "altimeter setting for take-off and cruising", 5)
    assert ids(hits) == ["aim:RAC 1.1:0", "aim:RAC 1.2:0"]


def test_keyword_search_also_matches_the_heading_path(loaded):
    assert ids(keyword_hits(loaded, "rules", limit=5)) != []


def test_keyword_search_with_only_stop_words_finds_nothing(loaded):
    assert keyword_hits(loaded, "what is the", limit=5) == []


def test_hybrid_search_finds_keyword_matches_vector_search_misses(loaded):
    hits = search(loaded, "cheat on an examination", StubEmbed(), "hybrid", limit=3)
    assert "aim:LRA 3.2:0" in ids(hits)


def test_fusion_favours_chunks_ranked_well_in_both_lists():
    vector = [hit("a"), hit("b"), hit("c")]
    keyword = [hit("b")]
    fused = fuse([vector, keyword], limit=3)
    assert ids(fused) == ["b", "a", "c"]
    assert fused[0].score == pytest.approx(1 / 62 + 1 / 61)


def test_fusion_respects_the_limit():
    assert ids(fuse([[hit("a"), hit("b")]], limit=1)) == ["a"]
