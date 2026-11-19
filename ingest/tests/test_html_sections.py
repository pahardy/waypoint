import pytest

from waypoint_ingest.html_sections import html_sections

PAGE = """<html><body>
<nav><p>Site menu</p></nav>
<main>
  <h1>Standard 999 - Flight Crew Rules</h1>
  <h2>Table of contents</h2>
  <ul><li><a href="#a">Division I</a></li></ul>
  <h2>Division I - General</h2>
  <h3>999.05 Recency Requirements</h3>
  <p>Pilots shall meet <strong>all</strong> of the following:</p>
  <ul>
    <li>(a) a flight review;
      <ul><li>(i) with an instructor;</li></ul>
    </li>
  </ul>
  <p>(amended 2008/04/17)</p>
  <h3>999.06 Examples</h3>
  <div class="col">MAYDAY MAYDAY MAYDAY</div>
  <table><tr><th>Item</th><th>Value</th></tr>
         <tr><td><p>Visibility</p></td><td>3 miles</td></tr></table>
  <h2>Schedule 1</h2>
  <h3>1. Prerequisites</h3><p>A letter.</p>
  <h2>Schedule 2</h2>
  <h3>1. Prerequisites</h3><p>Another letter.</p>
</main>
<footer><p>Date modified</p></footer>
</body></html>
"""


@pytest.fixture
def sections(tmp_path):
    path = tmp_path / "page.html"
    path.write_text(PAGE)
    return {s.ref: s for s in html_sections(path, "STD 999")}


def texts(section):
    return [p.text for p in section.paragraphs]


def test_sections_are_cited_by_heading_path(sections):
    assert list(sections) == [
        "STD 999 Division I - General / 999.05 Recency Requirements",
        "STD 999 Division I - General / 999.06 Examples",
        "STD 999 Schedule 1 / 1. Prerequisites",
        "STD 999 Schedule 2 / 1. Prerequisites",
    ]


def test_heading_path_starts_with_the_page_title(sections):
    section = sections["STD 999 Division I - General / 999.05 Recency Requirements"]
    assert section.heading_path == [
        "Standard 999 - Flight Crew Rules",
        "Division I - General",
        "999.05 Recency Requirements",
    ]


def test_nested_list_items_are_read_once_in_order(sections):
    section = sections["STD 999 Division I - General / 999.05 Recency Requirements"]
    assert texts(section) == [
        "Pilots shall meet all of the following:",
        "(a) a flight review;",
        "(i) with an instructor;",
        "(amended 2008/04/17)",
    ]


def test_loose_div_text_and_table_rows_are_kept(sections):
    assert texts(sections["STD 999 Division I - General / 999.06 Examples"]) == [
        "MAYDAY MAYDAY MAYDAY",
        "Item | Value",
        "3 miles",
        "Visibility",
    ]


def test_contents_navigation_and_footer_are_left_out(sections):
    everything = " ".join(t for s in sections.values() for t in texts(s))
    assert "Site menu" not in everything
    assert "Date modified" not in everything
    assert not any("contents" in ref.lower() for ref in sections)
