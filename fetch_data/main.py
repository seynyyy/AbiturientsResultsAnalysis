import argparse
from .FetchNmtResults import FetchNmtResults

def main():
    parser = argparse.ArgumentParser(description="Build NMT results table for a university.")
    parser.add_argument("--university", type=int, required=True, help="University code")
    parser.add_argument("--output", type=str, required=True, help="Path to output CSV file")
    parser.add_argument("--year", type=int, required=True, help="Year of results")
    args = parser.parse_args()

    fetcher = FetchNmtResults(args.university, args.output)
    fetcher.fetch_results_table(args.year)

if __name__ == "__main__":
    main()