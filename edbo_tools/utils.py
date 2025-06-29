import csv
import requests
import json
import re

# Mapping of PRSID codes to their corresponding statuses
PRSID_MAP = {
    "1": "заява надійшла з сайту",
    "2": "затримано",
    "3": "скасовано вступником",
    "4": "скасовано (втрата пріор.)",
    "5": "зареєстровано",
    "6": "допущено",
    "7": "відмова",
    "8": "скасовано ЗО",
    "9": "рекомендовано (бюджет)",
    "10": "відхилено (бюджет)",
    "11": "допущено (контракт, за ріш. ПК)",
    "12": "рекомендовано (контракт)",
    "13": "відхилено (контракт)",
    "14": "до наказу",
    "15": "відраховано",
    "16": "деактивовано (зарах. на бюджет)"
}

# Mapping of PTID codes to their corresponding funding types
PTID_MAP = {
    "1": "бюджет",
    "2": "контракт"
}

# Pagination limit for API requests
PAGINATION_LIMIT = 100


def fetch_offers_results_table(offer_ids: list[int], year: int) -> tuple[list[dict], list[str]]:
    """
    Fetches and processes offer results to generate a table with columns: prid, pa, status, and subjects.

    Args:
        offer_ids (list[int]): List of offer IDs to process.
        year (int): The specific year for which the data is being fetched.

    Returns:
        tuple: A tuple containing:
            - filtered (list[dict]): List of dictionaries representing rows of the table.
            - columns (list[str]): List of column names for the table.
    """
    all_subject_names = set()
    offers_subjects = {}
    base_url = build_base_url(year)

    # Retrieve subject mappings for each offer
    for offer_id in offer_ids:
        try:
            response = requests.get(f'{base_url}/offer/{offer_id}/')
            if response.status_code != 200:
                offers_subjects[offer_id] = {}
                continue
            match = re.search(r'let\s+offer\s*=\s*(\{.*?})(?=\s*let|\s*</script>)', response.text, re.DOTALL)
            if not match:
                offers_subjects[offer_id] = {}
                continue
            offer_data = json.loads(match.group(1).replace('&ndash;', '-'))
            offers_subjects[offer_id] = {str(k): v.get('sn', '') for k, v in offer_data.get('os', {}).items()}
            all_subject_names.update([name for name in offers_subjects[offer_id].values() if name])
        except (requests.RequestException, json.JSONDecodeError):
            offers_subjects[offer_id] = {}

    # Sort subject names and define table columns
    all_subject_names = sorted(all_subject_names)
    columns = ['prid', 'pa', 'status'] + all_subject_names

    filtered = []
    for offer_id in offer_ids:
        last = 0
        while True:
            offer_data_url = f'{base_url}/offer-requests/'
            response = requests.post(
                offer_data_url,
                data={'id': offer_id, 'last': str(last)},
                headers=generate_headers({}, year)
            )
            if response.status_code != 200:
                break
            data = response.json()
            if not data or 'requests' not in data:
                break
            id_to_subject = offers_subjects.get(offer_id, {})
            requests_list = data['requests']
            for req in requests_list:
                row = {col: '' for col in columns}
                row['prid'] = req.get('prid', '')
                row['pa'] = req.get('pa', '')
                prsid = str(req.get('prsid', ''))
                ptid = str(req.get('ptid', ''))
                status = PRSID_MAP.get(prsid, prsid)
                if prsid == "14":
                    status += f" ({PTID_MAP.get(ptid, ptid)})"
                row['status'] = status
                for rss in req.get('rss', []):
                    subj_name = id_to_subject.get(str(rss.get('id', '')))
                    if subj_name and subj_name in all_subject_names:
                        row[subj_name] = (rss.get('f', '')[:3]
                                          if isinstance(rss.get('f', ''), str) else '')
                filtered.append(row)
            if len(requests_list) < PAGINATION_LIMIT:
                break
            last += PAGINATION_LIMIT

    return filtered, columns


def generate_headers(payload: dict, year: int) -> dict:
    """
    Generates HTTP headers for requests.

    Args:
        payload (dict): The payload to be sent in the request.
        year (int): The year to construct the base URL for.

    Returns:
        dict: A dictionary containing the HTTP headers.
    """
    return {
        'Referer': build_base_url(year) + '/',
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Content-Length': str(len(json.dumps(payload).encode("utf-8"))),
    }


def fetch_university_offers_ids_list(university_code: int, year: int) -> list:
    """
    Retrieves a list of offer IDs for the university.

    Args:
        university_code (int): The code of the university to fetch offers for.
        year (int): The specific year for which the data is being fetched.

    Returns:
        list: A list of offer IDs, or an empty list if the request fails or the response is invalid.
    """
    offers_ids_url = f'{build_base_url(year)}/offers-universities/'
    response = requests.post(
        offers_ids_url,
        data={'university': str(university_code), 'qualification': '1', 'education_base': '40'},
        headers=generate_headers({}, year)
    )
    if response.status_code == 200 and response.content:
        try:
            data = response.json()
            return data.get('universities', [{}])[0].get('ids', '').split(',')
        except (ValueError, json.decoder.JSONDecodeError):
            print("Warning: Received invalid JSON response.")
            return []
    return []


def save_to_csv(data, columns, filepath):
    """
    Saves the provided data to a CSV file.

    Args:
        data (list[dict]): The data to be written to the CSV file.
        columns (list[str]): The column names for the CSV file.
        filepath (str): The path to the file where the data will be saved.

    Returns:
        None
    """
    try:
        with open(filepath, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            writer.writerows(data)
        print(f"Data successfully saved to {filepath}")
    except Exception as e:
        print(f"An error occurred while saving to CSV: {e}")


def fetch_offer_results(offer_id: int, year: int) -> tuple[list[dict], list[str]]:
    """
    Fetches and processes results for a single offer ID.

    Args:
        offer_id (int): The offer ID to process.
        year (int): The specific year for which the data is being fetched.

    Returns:
        tuple: A tuple containing:
            - filtered (list[dict]): List of dictionaries representing rows of the table.
            - columns (list[str]): List of column names for the table.
    """
    return fetch_offers_results_table([offer_id], year)


def build_base_url(year: int) -> str:
    """
    Builds the base URL for the given year.

    Args:
        year (int): The year to construct the base URL for.

    Returns:
        str: The constructed base URL.
    """
    return f"https://vstup{year}.edbo.gov.ua/"
