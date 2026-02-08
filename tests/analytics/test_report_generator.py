import csv
import io
import json

import pytest

from analytics.models import ModelStatistics
from analytics.report_generator import ReportGenerator


@pytest.fixture
def sample_stats():
    return {
        "gpt-4": ModelStatistics(
            model_name="gpt-4",
            total_games=10,
            overall_win_rate=0.8,
            spy_win_rate=0.9,
            civilian_win_rate=0.7,
            score_distribution={0: 2, 5: 8},
        ),
        "claude-3": ModelStatistics(
            model_name="claude-3",
            total_games=10,
            overall_win_rate=0.6,
            spy_win_rate=0.5,
            civilian_win_rate=0.7,
        ),
    }


def test_generate_text_report(sample_stats):
    generator = ReportGenerator()
    report = generator.generate_text_report(sample_stats)

    assert "SPYFALL ARENA ANALYTICS REPORT" in report
    assert "gpt-4" in report
    assert "claude-3" in report
    assert "80.00%" in report  # Win rate formatted


def test_generate_text_report_empty():
    generator = ReportGenerator()
    report = generator.generate_text_report({})
    assert "No statistics available" in report


def test_generate_json_report(sample_stats):
    generator = ReportGenerator()
    json_str = generator.generate_json_report(sample_stats)

    data = json.loads(json_str)
    assert "gpt-4" in data
    assert "claude-3" in data
    assert data["gpt-4"]["overall_win_rate"] == 0.8
    assert data["gpt-4"]["score_distribution"]["0"] == 2  # JSON keys are strings


def test_generate_csv_report(sample_stats):
    generator = ReportGenerator()
    csv_str = generator.generate_csv_report(sample_stats)

    # Use CSV reader to verify
    reader = csv.DictReader(io.StringIO(csv_str))
    rows = list(reader)

    assert len(rows) == 2

    # Verify rows (order might depend on dict iteration, but typically stable in Python 3.7+)
    # gpt-4 should be present
    gpt4_row = next(r for r in rows if r["model_name"] == "gpt-4")
    assert float(gpt4_row["overall_win_rate"]) == 0.8

    # Check score_distribution stringification
    assert (
        "{'0': 2, '5': 8}" in gpt4_row["score_distribution"]
        or "{0: 2, 5: 8}" in gpt4_row["score_distribution"]
    )


def test_generate_csv_report_empty():
    generator = ReportGenerator()
    csv_str = generator.generate_csv_report({})
    assert csv_str == ""
