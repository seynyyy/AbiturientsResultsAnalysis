from NmtResultsTableBuilder import NmtResultsTableBuilder
from NmtResultsService import NmtResultsService

UNIVERSITY_CODE = 137

if __name__ == "__main__":
    print("Starting NMT results processing...")

    offers_service = NmtResultsService(UNIVERSITY_CODE, 2023)
    offer_table_builder = NmtResultsTableBuilder(offers_service)
    df = offer_table_builder.build_results_table()

    df.to_csv('results2023.csv', index=False, encoding='utf-8-sig')

    UNIVERSITY_CODE = 137

    offers_service = NmtResultsService(UNIVERSITY_CODE, 2024)
    offer_table_builder = NmtResultsTableBuilder(offers_service)
    df = offer_table_builder.build_results_table()

    df.to_csv('results2024.csv', index=False, encoding='utf-8-sig')

