# EdboTools

A Python library and CLI tool for retrieving and saving data. The tool fetches data from [vstup.edbo.gov.ua](https://vstup.edbo.gov.ua) and saves it as a CSV file.


This is an unofficial library and CLI tool. It is not affiliated with or endorsed by the Unified State Electronic Database on Education (ЄДЕБО) or any official government entity. Use this tool at your own discretion and ensure compliance with applicable laws and regulations.
## Features

- Fetches NMT results for a specified university and year
- Saves results in a clean, structured CSV format
- Includes a command-line interface (CLI) for quick use

## Installation

Install directly from the repository:
```bash
pip install git+https://github.com/seynyyy/EdboTools.git
```

Or clone and install locally:

```bash
git clone https://github.com/seynyyy/EdboTools.git
cd edbo_tools
pip install .
```

## Requirements

- Python 3.8+
- requests

## Usage

### As a Library

```python
from edbo_tools.utils import fetch_offers_results_table, fetch_university_offers_ids_list, save_to_csv

offer_ids = fetch_university_offers_ids_list(123, 2024)
filtered, columns = fetch_offers_results_table(offer_ids, 2024)
save_to_csv(filtered, columns, "results.csv")
```

### Command-Line Interface
After installation, use the CLI:

```bash
fetch-results --university 123 --output results.csv --year 2024
```

* --university: University code (integer)
* --output: Path to output CSV file
* --year: Year of results (integer)

## Attribution
If you use or redistribute results obtained via this project, please provide a link to the original data source:

* [vstup.edbo.gov.ua](https://vstup.edbo.gov.ua)

* And cite the original repository: [edbo_tools](https://github.com/seynyyy/EdboTools)

## Data Source and API Usage

This project uses data from the Unified State Electronic Database on Education (ЄДЕБО) via the official public website [vstup.edbo.gov.ua](https://vstup.edbo.gov.ua).

All collected and used data is:
- Anonymized (does not contain personal or sensitive information)
- Publicly available without authentication
- Used solely for analytical, educational, or informational purposes

This project complies with:
- [Law of Ukraine on Access to Public Information](https://zakon.rada.gov.ua/laws/show/2939-17)
- [Regulations on Open Data](https://zakon.rada.gov.ua/laws/show/835-2015-%D0%BF)

### License
MIT License 

Use at your own risk. Data is for informational and educational purposes only.