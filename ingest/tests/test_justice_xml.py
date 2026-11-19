import pytest

from waypoint_ingest.justice_xml import regulation_sections
from waypoint_ingest.sources import Source

REGULATION = """<?xml version="1.0"?>
<Regulation><Body>
  <Heading level="1"><Label>PART I</Label><TitleText>General Provisions</TitleText></Heading>
  <Section><Label>101.01</Label>
    <Subsection><Label>(1)</Label><Text>The following definitions apply.</Text>
      <Definition><Text><DefinedTermEn>aircraft</DefinedTermEn> means a machine;</Text></Definition>
    </Subsection>
  </Section>
  <Heading level="1"><TitleText>Part VI — Operating Rules</TitleText></Heading>
  <Heading level="2"><TitleText>Subpart 2 — Flight Rules</TitleText></Heading>
  <Heading level="4"><TitleText>Minimum Altitudes</TitleText></Heading>
  <Section><Label>602.14</Label>
    <Subsection><Label>(1)</Label><Text><Repealed>[Repealed, SOR/2002-447, s. 2]</Repealed></Text></Subsection>
    <Subsection><Label>(2)</Label><Text>No person shall operate an aircraft</Text>
      <Paragraph><Label>(a)</Label><Text>over a built-up area below</Text>
        <Subparagraph><Label>(i)</Label><Text>1,000 feet, for aeroplanes;</Text></Subparagraph>
      </Paragraph>
    </Subsection>
    <HistoricalNote><HistoricalNoteSubItem>SOR/2002-447, s. 2</HistoricalNoteSubItem></HistoricalNote>
  </Section>
  <Heading level="4"><TitleText>Speed Limits</TitleText></Heading>
  <Section><Label>602.32</Label><Text>No person shall exceed <XRefExternal>250</XRefExternal> knots.</Text>
    <TableGroup><table><tgroup><tbody>
      <row><entry>Below 10,000 feet</entry><entry>250 knots</entry></row>
    </tbody></tgroup></table></TableGroup>
  </Section>
  <Section><Label>602.40</Label><Text><Repealed>[Repealed, SOR/2019-119]</Repealed></Text></Section>
  <Section><Label>602.41</Label><Text>[Reserved, SOR/2014-15, s. 1]</Text></Section>
  <Heading level="2"><TitleText>Subpart 3 — Other Rules</TitleText></Heading>
  <Section><Label>603.01</Label><Text>Other rule.</Text></Section>
</Body></Regulation>
"""


@pytest.fixture
def sections(tmp_path):
    path = tmp_path / "regulation.xml"
    path.write_text(REGULATION)
    return {s.ref: s for s in regulation_sections(path, "CAR")}


def texts(section):
    return [p.text for p in section.paragraphs]


def test_one_section_per_numbered_section_with_prefix(sections):
    assert list(sections) == ["CAR 101.01", "CAR 602.14", "CAR 602.32", "CAR 603.01"]


def test_repealed_and_reserved_sections_are_skipped(sections):
    assert "CAR 602.40" not in sections
    assert "CAR 602.41" not in sections


def test_heading_path_follows_heading_levels(sections):
    assert sections["CAR 602.14"].heading_path == [
        "Part VI — Operating Rules",
        "Subpart 2 — Flight Rules",
        "Minimum Altitudes",
        "CAR 602.14",
    ]


def test_a_new_heading_replaces_deeper_levels(sections):
    assert sections["CAR 603.01"].heading_path == [
        "Part VI — Operating Rules",
        "Subpart 3 — Other Rules",
        "CAR 603.01",
    ]


def test_heading_label_is_kept(sections):
    assert sections["CAR 101.01"].heading_path[0] == "PART I General Provisions"


def test_provisions_keep_labels_in_order_without_repeals_or_history(sections):
    assert texts(sections["CAR 602.14"]) == [
        "(2) No person shall operate an aircraft",
        "(a) over a built-up area below",
        "(i) 1,000 feet, for aeroplanes;",
    ]


def test_section_text_cross_references_and_table_rows_are_kept(sections):
    assert texts(sections["CAR 602.32"]) == [
        "No person shall exceed 250 knots.",
        "Below 10,000 feet | 250 knots",
    ]


def test_definitions_are_included(sections):
    assert texts(sections["CAR 101.01"])[1] == "aircraft means a machine;"


def test_regulation_sections_have_no_page(sections):
    assert {s.page for s in sections.values()} == {None}
    assert {p.page for s in sections.values() for p in s.paragraphs} == {None}


def test_xml_sources_need_a_section_prefix():
    with pytest.raises(ValueError, match="section_prefix"):
        Source(
            id="regs",
            title="Regulations",
            publisher="Department of Justice Canada",
            edition="1",
            published="2026",
            url="https://example.org/regs.xml",
            jurisdiction="CA",
            format="xml",
            priority=1,
            exams=["PPAER"],
            licence="test",
        )
