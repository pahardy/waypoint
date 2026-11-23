"""Official PSTAR questions from TP 11919, with their answers from the answer
key and their references from the guide's "Examination Question References"."""

import re
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf
import yaml
from pydantic import BaseModel

from waypoint_ingest.sources import REPO_ROOT

QUESTIONS_FILE = REPO_ROOT / "db" / "seed" / "pstar-questions.yaml"
FIRST_PAGE = 7
END_MARK = "EXAMINATION QUESTION REFERENCES"
REMOVED = "Intentionally removed"
SECTION = re.compile(r"^(\d{1,2})\.0 ")
QUESTION = re.compile(r"^(\d{1,2}\.\d{2})\.?\s+(.*)$")
CHOICE = re.compile(r"^\(([1-4])\)\s*(.*)$")
LIST_ITEM = re.compile(r"^[A-H]\. ")
ANSWER = re.compile(r"^\s*(\d{1,2}\.\d{2})\s+([1-4])\b", re.MULTILINE)
SAME_ROW_DY = 3


class Question(BaseModel):
    """One official PSTAR question with its answer from the answer key."""

    id: str
    number: str
    objective_id: str
    stem: str
    choices: list[str]
    answer_index: int
    references: list[str]
    source: str = "tp11919"
    page: int


@dataclass
class Row:
    """One visual row of a page: its spans as (x, text) cells, left to right."""

    page: int
    y: float
    bold: bool
    size: int
    cells: list[tuple[float, str]] = field(default_factory=list)

    @property
    def x(self) -> float:
        return self.cells[0][0]

    @property
    def text(self) -> str:
        return " ".join(text for _, text in self.cells)


@dataclass
class Draft:
    """A question being assembled from its rows."""

    number: str
    page: int
    stem: list[str]
    choices: list[list[str]] = field(default_factory=list)
    table_split: float | None = None


def page_rows(doc: pymupdf.Document, page_number: int) -> list[Row]:
    """Group a page's spans into rows, keeping each span's x position."""
    spans = [
        span
        for block in doc[page_number - 1].get_text("dict")["blocks"]
        for line in block.get("lines", [])
        for span in line["spans"]
        if span["text"].strip()
    ]
    spans.sort(key=lambda s: (s["bbox"][1], s["bbox"][0]))
    rows: list[Row] = []
    for span in spans:
        if not rows or abs(rows[-1].y - span["bbox"][1]) >= SAME_ROW_DY:
            rows.append(Row(page_number, span["bbox"][1], False, 0))
        row = rows[-1]
        row.cells.append((span["bbox"][0], " ".join(span["text"].split())))
        row.bold = row.bold or bool(span["flags"] & 16)
        row.size = max(row.size, round(span["size"]))
    for row in rows:
        row.cells.sort()
    return rows


def question_rows(pdf_path: Path) -> list[Row]:
    """Rows of the question pages, without page numbers."""
    doc = pymupdf.open(pdf_path)
    rows = []
    for page_number in range(FIRST_PAGE, doc.page_count + 1):
        for row in page_rows(doc, page_number):
            if row.text.startswith(END_MARK):
                return rows
            if row.size == 11:
                rows.append(row)
    return rows


def reference_rows(pdf_path: Path) -> list[Row]:
    """Rows of the "Examination Question References" pages, without the
    legend, section headings or page numbers."""
    doc = pymupdf.open(pdf_path)
    rows, started = [], False
    for page_number in range(FIRST_PAGE, doc.page_count + 1):
        for row in page_rows(doc, page_number):
            started = started or row.text.startswith(END_MARK)
            if started and row.size == 12 and not row.bold and row.x < 130:
                rows.append(row)
    return rows


def parse_references(rows: list[Row]) -> dict[str, list[str]]:
    """Question number to its references, one per row, in the guide's order."""
    references: dict[str, list[str]] = {}
    current = None
    for row in rows:
        if row.x < 80 and (match := QUESTION.match(row.text)):
            current = match.group(1)
            references[current] = [tidy_reference(match.group(2))]
        elif current:
            references[current].append(tidy_reference(row.text))
    return references


def tidy_reference(text: str) -> str:
    """One space either side of each dash: "TC AIM-COM– Call Signs" becomes
    "TC AIM-COM – Call Signs"."""
    return re.sub(r"\s*–\s*", " – ", text).strip().rstrip(",")


def parse_questions(rows: list[Row]) -> list[Draft]:
    """Assemble stems and choices from the question rows."""
    drafts: list[Draft] = []
    for row in rows:
        if row.bold and SECTION.match(row.text):
            continue
        if not row.bold and row.x < 80 and (match := QUESTION.match(row.text)):
            drafts.append(Draft(match.group(1), row.page, [match.group(2)]))
        elif len(row.cells) == 2 and row.text == "in flight on the ground":
            drafts[-1].table_split = row.cells[1][0]
        elif match := CHOICE.match(row.text):
            drafts[-1].choices.append(choice_cells(drafts[-1], row, match.group(2)))
        elif drafts[-1].choices:
            add_continuation(drafts[-1], row)
        else:
            drafts[-1].stem.append(row.text)
    return drafts


def choice_cells(draft: Draft, row: Row, text: str) -> list[str]:
    """A new choice: one cell, or two for an "in flight / on the ground" table."""
    if draft.table_split is None:
        return [text]
    left = [t for x, t in row.cells[1:] if x < draft.table_split]
    right = [t for x, t in row.cells if x >= draft.table_split]
    return [" ".join(left), " ".join(right)]


def add_continuation(draft: Draft, row: Row) -> None:
    """Append a wrapped row to the cell it sits under."""
    cells = draft.choices[-1]
    if draft.table_split is None:
        cells[0] = f"{cells[0]} {row.text}"
        return
    for x, text in row.cells:
        column = 1 if x >= draft.table_split else 0
        cells[column] = f"{cells[column]} {text}"


def stem_text(lines: list[str]) -> str:
    """Join stem rows; lettered items and finished sentences start new lines."""
    text = lines[0]
    for line in lines[1:]:
        breaks = LIST_ITEM.match(line) or text.endswith((".", "?", ":"))
        text = f"{text}\n{line}" if breaks else f"{text} {line}"
    return text


def choice_text(cells: list[str]) -> str:
    """A choice's text; table choices name both columns."""
    if len(cells) == 1:
        return cells[0]
    return f"in flight: {cells[0]} on the ground: {cells[1]}"


def read_answers(answer_key_path: Path) -> dict[str, int]:
    """Question number to its correct choice (1 to 4)."""
    text = "".join(page.get_text() for page in pymupdf.open(answer_key_path))
    return {number: int(choice) for number, choice in ANSWER.findall(text)}


def extract_questions(
    pdf_path: Path, answer_key_path: Path
) -> tuple[list[Question], list[str]]:
    """Questions with their answers, and any problems found while matching."""
    drafts = parse_questions(question_rows(pdf_path))
    references = parse_references(reference_rows(pdf_path))
    answers = read_answers(answer_key_path)
    numbers = {d.number for d in drafts}
    problems = [f"in answer key only: {n}" for n in sorted(answers.keys() - numbers)]
    questions = []
    for draft in drafts:
        if draft.stem == [REMOVED]:
            continue
        if len(draft.choices) != 4:
            problems.append(f"{draft.number}: {len(draft.choices)} choices")
            continue
        if draft.number not in answers:
            problems.append(f"{draft.number}: no answer")
            continue
        if draft.number not in references:
            problems.append(f"{draft.number}: no references")
            continue
        section = int(draft.number.split(".")[0])
        questions.append(
            Question(
                id=f"pstar-{draft.number}",
                number=draft.number,
                objective_id=f"pstar.regulations.{section:03d}",
                stem=stem_text(draft.stem),
                choices=[choice_text(cells) for cells in draft.choices],
                answer_index=answers[draft.number] - 1,
                references=references[draft.number],
                page=draft.page,
            )
        )
    return questions, problems


def write_questions(questions: list[Question], path: Path = QUESTIONS_FILE) -> None:
    """Write questions as YAML."""
    data = [q.model_dump() for q in questions]
    header = (
        "# Generated by `uv run ingest pstar-questions` from TP 11919 (7th ed.)\n"
        "# and its answer key. Official Transport Canada questions. Do not edit.\n"
    )
    path.write_text(
        header + yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=1000)
    )


def load_questions(path: Path = QUESTIONS_FILE) -> list[Question]:
    """Load the committed questions."""
    return [Question(**item) for item in yaml.safe_load(path.read_text())]
