import csv
import json
import re
import requests


def generate_headers(payload: dict, phpsessid: str, base_url: str) -> dict:
    """
    Generates HTTP headers for requests.

    Args:
        payload (dict): The payload to be sent in the request.
        phpsessid (str): PHP session ID.
        base_url (str): Base URL for the year.

    Returns:
        dict: A dictionary containing the HTTP headers.
    """
    return {
        'Referer': base_url + '/',
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Cookie': f'PHPSESSID={phpsessid}',
        'Content-Length': str(len(json.dumps(payload).encode("utf-8"))),
    }


class FetchNmtResults:
    """
    A class for retrieving and saving NMT (National Multi-Subject Test) results for a university.
    """

    def __init__(self, university_code: int, filepath: str):
        """
        Initializes an instance of NmtResultsTableBuilder.

        Args:
            university_code (int): The code of the university.
            filepath (str): The path to the CSV file for saving results.
        """
        self.university_code = university_code
        self.filepath = filepath

    def fetch_offer_ids_list(self, base_url: str, phpsessid: str) -> list:
        """
        Retrieves a list of offer IDs for the university.

        Args:
            base_url (str): Base URL for the year.
            phpsessid (str): PHP session ID.

        Returns:
            list: A list of offer IDs, or an empty list if the request fails or the response is invalid.
        """
        offers_ids_url = f'{base_url}/offers-universities/'
        response = requests.post(
            offers_ids_url,
            data={'university': str(self.university_code), 'qualification': '1', 'education_base': '40'},
            headers=generate_headers({}, phpsessid, base_url)
        )
        if response.status_code == 200 and response.content:
            try:
                data = response.json()
                return data.get('universities', [{}])[0].get('ids', '').split(',')
            except (ValueError, json.decoder.JSONDecodeError):
                print("Warning: Received invalid JSON response.")
                return []
        return []

    def fetch_offer_data(self, offer_id: str, base_url: str, phpsessid: str) -> dict | None:
        """
        Retrieves data for a specific offer.

        Args:
            offer_id (str): The ID of the offer.
            base_url (str): Base URL for the year.
            phpsessid (str): PHP session ID.

        Returns:
            dict | None: A dictionary containing the offer data if the request is successful, otherwise None.
        """
        offer_data_url = f'{base_url}/offer-requests/'
        response = requests.post(
            offer_data_url,
            data={'id': offer_id, 'last': '0'},
            headers=generate_headers({}, phpsessid, base_url)
        )
        return response.json() if response.status_code == 200 else None

    def fetch_offer_subjects_map(self, offer_id: str, base_url: str) -> dict:
        """
        Retrieves a mapping of subject IDs to subject names for a specific offer.

        Args:
            offer_id (str): The ID of the offer.
            base_url (str): Base URL for the year.

        Returns:
            dict: A dictionary mapping subject IDs to subject names, or an empty dictionary if the request fails.
        """
        try:
            response = requests.get(f'{base_url}/offer/{offer_id}/')
            if response.status_code != 200:
                return {}
            match = re.search(r'let\s+offer\s*=\s*(\{.*?})(?=\s*let|\s*</script>)', response.text, re.DOTALL)
            if not match:
                return {}
            offer_data = json.loads(match.group(1).replace('&ndash;', '-'))
            return {str(k): v.get('sn', '') for k, v in offer_data.get('os', {}).items()}
        except (json.JSONDecodeError, Exception):
            return {}

    def fetch_results_table(self, year: int):
        """
        Builds a table (list of dictionaries) with NMT results for the given year and saves it to a CSV file.

        Workflow:
        1. Retrieves offer IDs and subject mappings.
        2. Collects all unique subject names and ensures they are sorted and non-empty.
        3. Processes each offer ID to extract relevant data and filters out incomplete rows.
        4. Drops columns that are empty across all rows (except the 'p' column).
        5. Ensures all rows have the same number of columns as the header.
        6. Saves the processed data to a CSV file.

        Args:
            year (int): The year for which the results are being retrieved.
        """
        base_url = f'https://vstup{year}.edbo.gov.ua'
        phpsessid = requests.get(base_url).cookies.get('PHPSESSID')

        offer_ids = self.fetch_offer_ids_list(base_url, phpsessid) or []
        all_subject_names = set()
        offers_subjects = {}

        for offer_id in offer_ids:
            offers_subjects[offer_id] = self.fetch_offer_subjects_map(offer_id, base_url)
            all_subject_names.update([name for name in offers_subjects[offer_id].values() if name])

        all_subject_names = sorted(set([name for name in all_subject_names if name]))
        columns = ['p'] + all_subject_names

        filtered = []
        for offer_id in offer_ids:
            data = self.fetch_offer_data(offer_id, base_url, phpsessid)
            if not data or 'requests' not in data:
                continue
            id_to_subject = offers_subjects.get(offer_id, {})
            for req in data['requests']:
                if req.get('ptid') in [1, 2]:
                    row = {col: '' for col in columns}
                    row['p'] = req.get('p', '')
                    for rss in req.get('rss', []):
                        subj_name = id_to_subject.get(str(rss.get('id', '')))
                        if subj_name and subj_name in all_subject_names:
                            row[subj_name] = (rss.get('f', '')[:3]
                                              if isinstance(rss.get('f', ''), str) else '')
                    row = {col: row.get(col, '') for col in columns}
                    if all((v == '' or v is None) for k, v in row.items() if k != 'p'):
                        continue
                    filtered.append(row)

        if filtered:
            cols_to_drop = []
            for col in columns:
                if col == 'p':
                    continue
                if all((str(row.get(col, '')).strip() == '') for row in filtered):
                    cols_to_drop.append(col)
            for row in filtered:
                for col in cols_to_drop:
                    if col in row:
                        del row[col]
            columns = [col for col in columns if col not in cols_to_drop]

        for i, row in enumerate(filtered):
            assert len(row) == len(columns), f"Row {i} has {len(row)} values, expected {len(columns)}"
        self.save_to_csv(filtered, columns)

    def save_to_csv(self, data, columns):
        """
        Saves the given data to a CSV file.

        Args:
            data (list): A list of dictionaries representing rows of data.
            columns (list): A list of column names for the CSV file.
        """
        if not data:
            return
        with open(self.filepath, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            for row in data:
                writer.writerow(row)