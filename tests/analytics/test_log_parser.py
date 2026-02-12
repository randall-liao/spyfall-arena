import json
from pathlib import Path

import pytest

from analytics.log_parser import LogParser
from analytics.models import GameRecord, PlayerConfig, RoundRecord

# Sample data for tests
SAMPLE_GAME_JSON = {
    "game_id": "game_1",
    "timestamp": "2024-01-01T12:00:00",
    "players": [
        {
            "nickname": "Alice",
            "model_name": "gpt-4",
            "provider": "OPEN_ROUTER",
            "temperature": 0.7,
        },
        {
            "nickname": "Bob",
            "model_name": "claude-3",
            "provider": "OPEN_ROUTER",
            "temperature": 0.5,
        },
    ],
    "rounds": [
        {
            "round_number": 1,
            "location": "Beach",
            "spy": "Bob",
            "role_assignments": {
                "Alice": {"is_spy": False, "location": "Beach"},
                "Bob": {"is_spy": True, "location": None},
            },
            "turns": [],
            "vote_attempts": [],
            "spy_guess": None,
            "ending_condition": "spy_guess",
            "round_scores": {"Alice": 0, "Bob": 5},
        }
    ],
    "final_scores": {"Alice": 0, "Bob": 5},
    "status": "completed",
}

# Sample with full round data
FULL_ROUND_GAME_JSON = {
    "game_id": "game_2",
    "timestamp": "2024-01-01T13:00:00",
    "players": SAMPLE_GAME_JSON["players"],
    "rounds": [
        {
            "round_number": 1,
            "location": "Beach",
            "spy": "Bob",
            "role_assignments": {
                "Alice": {"is_spy": False, "location": "Beach"},
                "Bob": {"is_spy": True, "location": None},
            },
            "turns": [
                {
                    "turn_number": 1,
                    "asker_nickname": "Alice",
                    "answerer_nickname": "Bob",
                    "question": "Q",
                    "answer": "A",
                    "timestamp": "2024-01-01T13:05:00",
                }
            ],
            "vote_attempts": [
                {
                    "initiator": "Alice",
                    "suspect": "Bob",
                    "votes": {"Alice": True, "Bob": False},
                    "passed": False,
                    "timestamp": "2024-01-01T13:10:00",
                }
            ],
            "spy_guess": {
                "spy_nickname": "Bob",
                "guessed_location": "Beach",
                "actual_location": "Beach",
                "correct": True,
                "timestamp": "2024-01-01T13:15:00",
            },
            "ending_condition": "spy_guess",
            "round_scores": {"Alice": 0, "Bob": 5},
        }
    ],
    "final_scores": {"Alice": 0, "Bob": 5},
    "status": "completed",
}


def test_parse_valid_json_string():
    parser = LogParser()
    json_str = json.dumps(SAMPLE_GAME_JSON)
    record = parser.parse_json_string(json_str)
    assert record is not None
    assert record.game_id == "game_1"
    assert len(record.players) == 2
    assert record.players[0].nickname == "Alice"
    assert len(record.rounds) == 1
    assert record.rounds[0].spy == "Bob"


def test_parse_full_round_data():
    parser = LogParser()
    json_str = json.dumps(FULL_ROUND_GAME_JSON)
    record = parser.parse_json_string(json_str)
    assert record is not None
    round_rec = record.rounds[0]
    assert len(round_rec.turns) == 1
    assert len(round_rec.vote_attempts) == 1
    assert round_rec.spy_guess is not None
    assert round_rec.spy_guess.correct is True


def test_parse_invalid_json_string():
    parser = LogParser()
    record = parser.parse_json_string("{invalid json")
    assert record is None


def test_parse_file(tmp_path):
    parser = LogParser()
    file_path = tmp_path / "game.json"
    file_path.write_text(json.dumps(SAMPLE_GAME_JSON), encoding="utf-8")

    record = parser.parse_file(str(file_path))
    assert record is not None
    assert record.game_id == "game_1"


def test_parse_directory(tmp_path):
    parser = LogParser()
    (tmp_path / "game1.json").write_text(json.dumps(SAMPLE_GAME_JSON), encoding="utf-8")
    (tmp_path / "game2.json").write_text(json.dumps(SAMPLE_GAME_JSON), encoding="utf-8")
    (tmp_path / "ignore.txt").write_text("ignore me", encoding="utf-8")

    records = parser.parse_directory(str(tmp_path))
    assert len(records) == 2


def test_parse_malformed_json(tmp_path):
    parser = LogParser()
    file_path = tmp_path / "bad.json"
    file_path.write_text("{broken json", encoding="utf-8")

    record = parser.parse_file(str(file_path))
    assert record is None


def test_parse_missing_fields(tmp_path):
    parser = LogParser()
    file_path = tmp_path / "missing.json"
    incomplete_json = SAMPLE_GAME_JSON.copy()
    del incomplete_json["game_id"]
    file_path.write_text(json.dumps(incomplete_json), encoding="utf-8")

    record = parser.parse_file(str(file_path))
    assert record is None


def test_parse_non_existent_file():
    parser = LogParser()
    record = parser.parse_file("non_existent.json")
    assert record is None


def test_parse_non_existent_directory():
    parser = LogParser()
    records = parser.parse_directory("non_existent_dir")
    assert records == []


def test_parse_game_data_exception():
    """Test exception handling within _parse_game_data (e.g. malformed internal structure)"""
    parser = LogParser()
    bad_data = SAMPLE_GAME_JSON.copy()
    # Making players not a list to cause iteration error
    bad_data["players"] = "not a list"

    # We pass it as a JSON string to trigger _parse_game_data
    record = parser.parse_json_string(json.dumps(bad_data))
    assert record is None


def test_parse_round_error():
    """Test error parsing a specific round, which should cause the whole game parsing to fail based on current implementation"""
    parser = LogParser()
    bad_round_data = SAMPLE_GAME_JSON.copy()
    # Missing required field inside a round
    bad_round_data["rounds"] = [
        {
            "round_number": 1,
            # Missing 'location'
            "spy": "Bob",
            "role_assignments": {},
            "turns": [],
            "vote_attempts": [],
            "spy_guess": None,
            "ending_condition": "spy_guess",
            "round_scores": {},
        }
    ]

    record = parser.parse_json_string(json.dumps(bad_round_data))
    assert record is None
