#!/usr/bin/env python3
import argparse
import logging
import sys
from pathlib import Path

from analytics.data_aggregator import DataAggregator
from analytics.log_parser import LogParser
from analytics.report_generator import ReportGenerator
from analytics.statistics_calculator import StatisticsCalculator
from game_logging.console_setup import setup_console_logging


def main():
    parser = argparse.ArgumentParser(description="Analyze Spyfall Arena game logs.")
    parser.add_argument(
        "--logs-dir",
        type=str,
        default="logs",
        help="Directory containing game logs (default: logs)",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["text", "json", "csv"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument("--output", type=str, help="Output file path (default: stdout)")
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging verbosity (default: INFO)",
    )

    args = parser.parse_args()

    # Setup logging
    setup_console_logging(args.log_level)

    # 1. Parse Logs
    parser_component = LogParser()
    games = parser_component.parse_directory(args.logs_dir)

    if not games:
        print(f"No valid game logs found in '{args.logs_dir}'.")
        return

    print(f"Parsed {len(games)} game logs.")

    # 2. Aggregate Data
    aggregator = DataAggregator()
    model_data = aggregator.aggregate_by_model(games)
    print(f"Aggregated data for {len(model_data)} models.")

    # 3. Calculate Statistics
    calculator = StatisticsCalculator()
    statistics = calculator.calculate_all_statistics(model_data)

    # 4. Generate Report
    generator = ReportGenerator()
    if args.format == "text":
        report = generator.generate_text_report(statistics)
    elif args.format == "json":
        report = generator.generate_json_report(statistics)
    elif args.format == "csv":
        report = generator.generate_csv_report(statistics)

    # 5. Output
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"Report written to {args.output}")
        except Exception as e:
            print(f"Error writing to file {args.output}: {e}")
            sys.exit(1)
    else:
        print(report)


if __name__ == "__main__":
    main()
