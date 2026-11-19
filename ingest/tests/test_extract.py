from waypoint_ingest.extract import extract_sections


def body(section):
    return " ".join(line.text for line in section.lines)


def by_ref(sections):
    return {s.heading.ref: s for s in sections}


def test_sections_follow_the_bookmarks(outlined_pdf):
    sections, missing = extract_sections(outlined_pdf)
    assert [s.heading.ref for s in sections] == [
        "GEN 1.0",
        "GEN 1.1",
        "GEN 1.2",
        "GEN 2.0",
    ]
    assert [h.ref for h in missing] == ["GEN 2.1"]


def test_section_keeps_heading_path_and_page(outlined_pdf):
    sections = by_ref(extract_sections(outlined_pdf)[0])
    assert sections["GEN 1.1"].heading.path == [
        "GEN—General",
        "1.0 General Information",
        "1.1 Aeronautical Information Services",
    ]
    assert sections["GEN 2.0"].heading.page == 2
    assert body(sections["GEN 2.0"]) == "Safety text on page two."


def test_wrapped_heading_is_not_body_text(outlined_pdf):
    sections = by_ref(extract_sections(outlined_pdf)[0])
    assert body(sections["GEN 1.1"]).startswith("The first paragraph")


def test_heading_beside_side_tab_is_found(outlined_pdf):
    sections = by_ref(extract_sections(outlined_pdf)[0])
    assert body(sections["GEN 1.2"]) == "Units text in the right column."


def test_headers_and_page_numbers_are_removed(outlined_pdf):
    sections, _ = extract_sections(outlined_pdf)
    everything = " ".join(body(s) for s in sections)
    assert "TC AIM" not in everything
    assert "October" not in everything
    assert not any(line.text.isdigit() for s in sections for line in s.lines)
