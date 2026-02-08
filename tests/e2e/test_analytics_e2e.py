import json
from pathlib import Path

import pytest

from analytics.data_aggregator import DataAggregator
from analytics.log_parser import LogParser
from analytics.report_generator import ReportGenerator
from analytics.statistics_calculator import StatisticsCalculator


def test_full_pipeline_with_sample_log():
    """
    End-to-end test using sample log file in e2e test directory.
    Tests the complete pipeline: parse → aggregate → calculate → report.
    """
    # Setup: Use sample log file
    sample_log_path = Path(__file__).parent / "sample_log.json"
    assert sample_log_path.exists(), "Sample log file must exist"

    # Step 1: Parse log
    parser = LogParser()
    game = parser.parse_file(str(sample_log_path))

    # Assertions on parsing
    assert game is not None, "Should parse sample log successfully"
    assert game.game_id == "test_game_001"
    assert len(game.rounds) == 2
    assert len(game.players) == 4

    # Step 2: Aggregate data
    aggregator = DataAggregator()
    model_data = aggregator.aggregate_by_model([game])

    # Assertions on aggregation
    assert len(model_data) == 2, "Should have 2 models (test-model-1 and test-model-2)"
    assert "test-model-1" in model_data
    assert "test-model-2" in model_data

    # Validate test-model-1 data (Alice and Bob)
    model1_data = model_data["test-model-1"]
    assert model1_data.total_games == 1
    assert model1_data.total_rounds == 4  # 2 players × 2 rounds
    assert len(model1_data.spy_rounds) == 1  # Alice was spy in round 1
    assert len(model1_data.civilian_rounds) == 3  # Bob in both, Alice in round 2

    # Validate test-model-2 data (Charlie and David)
    model2_data = model_data["test-model-2"]
    assert model2_data.total_games == 1
    assert model2_data.total_rounds == 4  # 2 players × 2 rounds
    assert len(model2_data.spy_rounds) == 1  # Charlie was spy in round 2
    assert len(model2_data.civilian_rounds) == 3  # David in both, Charlie in round 1

    # Step 3: Calculate statistics
    calculator = StatisticsCalculator()
    statistics = calculator.calculate_all_statistics(model_data)

    # Assertions on statistics
    assert len(statistics) == 2, "Should have stats for both models"

    # Validate test-model-1 statistics
    stats1 = statistics["test-model-1"]
    assert stats1.total_games == 1
    assert stats1.total_rounds == 4
    assert stats1.spy_rounds_count == 1
    assert stats1.civilian_rounds_count == 3
    assert 0.0 <= stats1.overall_win_rate <= 1.0
    assert 0.0 <= stats1.spy_win_rate <= 1.0
    assert 0.0 <= stats1.civilian_win_rate <= 1.0

    # Alice (spy) was caught, so spy_win_rate should be 0.0
    assert stats1.spy_win_rate == 0.0

    # Bob initiated successful vote, should have good civilian performance
    # Round 1: Spy voted out. Civilians won.
    # Round 2: Spy won by guess. Civilians lost.
    # Civilians participated in 3 rounds.
    # R1: Bob (Civilian) won.
    # R2: Alice (Civilian) lost. Bob (Civilian) lost.
    # So 1 win out of 3 civilian rounds.
    assert stats1.civilian_win_rate == 1 / 3

    # Validate test-model-2 statistics
    stats2 = statistics["test-model-2"]
    assert stats2.total_games == 1
    assert stats2.total_rounds == 4
    assert stats2.spy_rounds_count == 1
    assert stats2.civilian_rounds_count == 3

    # Charlie (spy) guessed correctly, so spy_win_rate should be 1.0
    assert stats2.spy_win_rate == 1.0
    assert stats2.spy_guess_accuracy == 1.0
    assert stats2.successful_spy_guesses == 1
    assert stats2.total_spy_guesses == 1

    # Round ending statistics
    # Round 1: Vote
    # Round 2: Spy Guess
    # These are global per model but counted per round participation.
    # Both models participated in both rounds (via their players).
    # Model 1 (Alice/Bob):
    #   R1 (Vote): Alice (Spy), Bob (Civilian). Both present.
    #   R2 (Guess): Alice (Civilian), Bob (Civilian). Both present.
    # So counts should sum to total rounds (4).
    # R1 counted twice? No, round ending is property of round.
    # If model has 2 players in same round, does it count ending condition twice?
    # Yes, because we iterate over `all_rounds`.
    # R1 ending "vote". Alice has R1 (Spy). Bob has R1 (Civilian).
    # So stats1.rounds_ended_by_vote should be 2.
    assert stats1.rounds_ended_by_vote == 2
    assert stats1.rounds_ended_by_spy_guess == 2
    assert stats2.rounds_ended_by_vote == 2
    assert stats2.rounds_ended_by_spy_guess == 2

    # Step 4: Generate reports
    generator = ReportGenerator()

    # Test text report
    text_report = generator.generate_text_report(statistics)
    assert len(text_report) > 0, "Text report should not be empty"
    assert "test-model-1" in text_report
    assert "test-model-2" in text_report

    # Test JSON report
    json_report = generator.generate_json_report(statistics)
    assert len(json_report) > 0, "JSON report should not be empty"
    parsed_json = json.loads(json_report)
    assert len(parsed_json) == 2
    assert "test-model-1" in parsed_json
    assert "test-model-2" in parsed_json

    # Test CSV report
    csv_report = generator.generate_csv_report(statistics)
    assert len(csv_report) > 0, "CSV report should not be empty"
    csv_lines = csv_report.strip().split("\n")
    assert len(csv_lines) == 3, "CSV should have header + 2 model rows"

    # Validate CSV contains model names
    assert "test-model-1" in csv_report
    assert "test-model-2" in csv_report


def test_e2e_parse_directory_with_sample():
    """
    Test parsing a directory containing the sample log file.
    """
    # Setup: Use directory containing sample log
    sample_dir = Path(__file__).parent

    # Parse directory
    parser = LogParser()
    games = parser.parse_directory(str(sample_dir))

    # Should find at least the sample_log.json file
    assert len(games) >= 1, "Should parse at least the sample log"

    # Find the sample game
    sample_game = next((g for g in games if g.game_id == "test_game_001"), None)
    assert sample_game is not None, "Should find sample game in parsed results"
    assert len(sample_game.rounds) == 2
