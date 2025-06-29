import argparse
from edbo_tools.utils import fetch_offers_results_table, fetch_university_offers_ids_list, save_to_csv

def main():
    """
    Command-line interface for fetching and saving offer results.
    """
    parser = argparse.ArgumentParser(description="Fetch and save NMT results for a university.")
    parser.add_argument("--university", type=int, required=True, help="University code (integer).")
    parser.add_argument("--year", type=int, required=True, help="Year of results (integer).")
    parser.add_argument("--output", type=str, required=True, help="Path to the output CSV file.")

    args = parser.parse_args()

    # Fetch the list of offer IDs for the given university and year
    offer_ids = fetch_university_offers_ids_list(args.university, args.year)

    if not offer_ids:
        print("No offers found for the specified university and year.")
        return

    # Fetch and process the results for the retrieved offer IDs
    filtered, columns = fetch_offers_results_table(offer_ids, args.year)

    # Save the processed results to a CSV file
    save_to_csv(filtered, columns, args.output)
    print(f"Results saved to {args.output}")