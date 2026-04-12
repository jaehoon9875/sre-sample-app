"""Tests for README.md structure and content integrity."""

import pathlib
import re

README_PATH = pathlib.Path(__file__).parent.parent / "README.md"


def read_readme() -> str:
    return README_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Basic file checks
# ---------------------------------------------------------------------------


def test_readme_exists():
    assert README_PATH.exists(), "README.md must exist at the repository root"


def test_readme_is_not_empty():
    content = read_readme()
    assert len(content.strip()) > 0, "README.md must not be empty"


def test_readme_is_valid_utf8():
    # read_text with encoding="utf-8" raises UnicodeDecodeError on invalid files;
    # reaching this assertion means decoding succeeded.
    content = read_readme()
    assert isinstance(content, str)


# ---------------------------------------------------------------------------
# Required section headings (pre-existing content)
# ---------------------------------------------------------------------------


REQUIRED_SECTIONS = [
    "빠른 시작",
    "서비스 구성",
    "기술 스택",
    "GKE 배포",
    "SRE 실습 시나리오",
    "문서",
    "관련 프로젝트",
]


def test_readme_contains_required_sections():
    content = read_readme()
    for section in REQUIRED_SECTIONS:
        assert section in content, f"README.md must contain section: {section}"


# ---------------------------------------------------------------------------
# Tests for the line added in this PR  (`# test` at end of file)
# ---------------------------------------------------------------------------


def test_readme_ends_with_test_heading():
    """The PR appended '# test' to README.md; verify it is present."""
    content = read_readme()
    assert "# test" in content, "README.md must contain the '# test' heading added in this PR"


def test_readme_test_heading_is_h1():
    """'# test' must be a top-level (H1) heading, not preceded by additional '#' characters."""
    content = read_readme()
    # Match a line that is exactly "# test" (H1), not "## test" or "### test"
    assert re.search(r"^# test$", content, re.MULTILINE), (
        "The 'test' heading added in this PR must be an H1 (single '#') heading"
    )


def test_readme_test_heading_appears_once():
    """'# test' heading should appear exactly once to avoid duplication."""
    content = read_readme()
    matches = re.findall(r"^# test$", content, re.MULTILINE)
    assert len(matches) == 1, (
        f"Expected exactly one '# test' heading, found {len(matches)}"
    )


def test_readme_test_heading_is_near_end():
    """The '# test' line added in this PR should be in the last 10 lines of the file."""
    lines = read_readme().splitlines()
    # Strip trailing blank lines for a stable check
    stripped = [l for l in lines if l.strip()]
    assert stripped, "README.md must not be blank"
    last_10 = stripped[-10:]
    assert any(re.match(r"^# test$", line) for line in last_10), (
        "'# test' heading should be located near the end of README.md"
    )


# ---------------------------------------------------------------------------
# Regression / boundary cases
# ---------------------------------------------------------------------------


def test_readme_no_null_bytes():
    content = read_readme()
    assert "\x00" not in content, "README.md must not contain null bytes"


def test_readme_has_title():
    """README.md must start with an H1 project title."""
    content = read_readme()
    first_non_blank = next(
        (line for line in content.splitlines() if line.strip()), ""
    )
    assert first_non_blank.startswith("# "), (
        "README.md must begin with an H1 title heading"
    )


def test_readme_related_projects_section_intact():
    """Verify the '관련 프로젝트' section that immediately precedes the new line is still intact."""
    content = read_readme()
    assert "observability-platform" in content
    assert "cloud-sre-platform" in content