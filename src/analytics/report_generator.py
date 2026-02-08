import csv
import io
import json
from datetime import datetime
from typing import Dict, List

from analytics.models import ModelStatistics


class ReportGenerator:
    """Generates reports from model statistics."""

    def generate_text_report(self, statistics: Dict[str, ModelStatistics]) -> str:
        """Generate formatted text report."""
        if not statistics:
            return "No statistics available."

        # Sort by win rate descending
        sorted_stats = sorted(
            statistics.values(), key=lambda s: s.overall_win_rate, reverse=True
        )

        lines = []
        lines.append("=" * 80)
        lines.append(
            f"SPYFALL ARENA ANALYTICS REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        lines.append("=" * 80)
        lines.append("")

        # Summary Table
        lines.append(
            f"{'Model':<30} | {'Win Rate':<10} | {'Spy Win%':<10} | {'Civ Win%':<10} | {'Games':<5}"
        )
        lines.append("-" * 80)

        for s in sorted_stats:
            lines.append(
                f"{s.model_name:<30} | "
                f"{s.overall_win_rate:.2%}    | "
                f"{s.spy_win_rate:.2%}     | "
                f"{s.civilian_win_rate:.2%}     | "
                f"{s.total_games:<5}"
            )

        lines.append("")
        lines.append("=" * 80)
        lines.append("DETAILED STATISTICS")
        lines.append("=" * 80)

        for s in sorted_stats:
            lines.append(f"\nModel: {s.model_name}")
            lines.append("-" * 40)

            lines.append("  General:")
            lines.append(f"    Total Games: {s.total_games}")
            lines.append(f"    Overall Win Rate: {s.overall_win_rate:.2%}")
            lines.append(f"    Avg Score/Game: {s.average_score_per_game:.2f}")

            lines.append("  Spy Performance:")
            lines.append(
                f"    Spy Win Rate: {s.spy_win_rate:.2%} ({s.spy_rounds_count} rounds)"
            )
            lines.append(f"    Survival Rate: {s.spy_survival_rate:.2%}")
            lines.append(f"    Guess Accuracy: {s.spy_guess_accuracy:.2%}")
            lines.append(f"    Avg Spy Score: {s.average_spy_score:.2f}")

            lines.append("  Civilian Performance:")
            lines.append(
                f"    Civilian Win Rate: {s.civilian_win_rate:.2%} ({s.civilian_rounds_count} rounds)"
            )
            lines.append(f"    Avg Civ Score: {s.average_civilian_score:.2f}")

            lines.append("  Voting Behavior:")
            lines.append(f"    Voting Accuracy: {s.voting_accuracy:.2%}")
            lines.append(f"    Votes Initiated: {s.votes_initiated}")
            lines.append(
                f"    Initiation Success: {s.vote_initiation_success_rate:.2%}"
            )
            lines.append(f"    Times Suspected: {s.times_suspected}")

            lines.append("  Engagement:")
            lines.append(f"    Questions Asked: {s.questions_asked}")
            lines.append(f"    Questions Answered: {s.questions_answered}")
            lines.append(f"    Avg Turns/Round: {s.average_turns_per_round:.2f}")

        return "\n".join(lines)

    def generate_json_report(self, statistics: Dict[str, ModelStatistics]) -> str:
        """Generate JSON report."""
        import dataclasses

        # Convert dataclasses to dicts
        stats_dict = {
            name: dataclasses.asdict(stat) for name, stat in statistics.items()
        }
        return json.dumps(stats_dict, indent=2)

    def generate_csv_report(self, statistics: Dict[str, ModelStatistics]) -> str:
        """Generate CSV report."""
        if not statistics:
            return ""

        output = io.StringIO()

        # Get all field names from ModelStatistics
        # We can inspect one instance
        sample_stat = next(iter(statistics.values()))
        import dataclasses

        field_names = [f.name for f in dataclasses.fields(sample_stat)]

        # Filter out complex fields like dictionary (score_distribution) if strict CSV needed
        # But CSV writer handles string conversion. `score_distribution` will be stringified.

        writer = csv.DictWriter(output, fieldnames=field_names)
        writer.writeheader()

        for stat in statistics.values():
            writer.writerow(dataclasses.asdict(stat))

        return output.getvalue()
