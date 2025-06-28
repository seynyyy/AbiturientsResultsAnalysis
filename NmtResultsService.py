import json
import re

import requests


class NmtResultsService:
    """
    A service class for interacting with university NMT results data.
    """

    def __init__(self, university_code: int, year: int):
        """
        Initializes the NmtResultsService instance.

        Args:
            university_code (int): The code of the university.
            year (int): The year for which to fetch NMT results.
        """
        self.university_code = university_code
        self.year = year
        self.base_url = f'https://vstup{year}.edbo.gov.ua'
        self.phpsessid = requests.get(self.base_url).cookies.get('PHPSESSID')
        self.offers_ids_url = f'{self.base_url}/offers-universities/'
        self.offer_data_url = f'{self.base_url}/offer-requests/'

    def generate_headers(self, payload: dict) -> dict:
        """
        Generates HTTP headers for requests.

        Args:
            payload (dict): The payload to be sent in the request.

        Returns:
            dict: A dictionary containing the HTTP headers.
        """
        return {
            'Referer': self.base_url + '/',
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Cookie': f'PHPSESSID={self.phpsessid}',
            'Content-Length': str(len(json.dumps(payload).encode("utf-8"))),
        }

    def get_nmt_offer_ids_list(self) -> list | None:
        response = requests.post(
            self.offers_ids_url,
            data={'university': str(self.university_code), 'qualification': '1', 'education_base': '40'},
            headers=self.generate_headers({})
        )
        if response.status_code == 200 and response.content:
            try:
                data = response.json()
                return data.get('universities', [{}])[0].get('ids', '').split(',')
            except (ValueError, json.decoder.JSONDecodeError):
                print("Warning: Received invalid JSON response.")
                return None
        return None

    def get_nmt_offer_data(self, offer_id: str) -> dict | None:
        """
        Fetches data for a specific NMT offer.

        Args:
            offer_id (str): The ID of the offer.

        Returns:
            dict | None: A dictionary containing the offer data if the request is successful, otherwise None.
        """
        response = requests.post(
            self.offer_data_url,
            data={'id': offer_id, 'last': '0'},
            headers=self.generate_headers({})
        )
        return response.json() if response.status_code == 200 else None

    def get_nmt_offer_subjects_map(self, offer_id: str) -> dict:
        """
        Fetches the mapping of subject IDs to subject names for a specific NMT offer.

        Args:
            offer_id (str): The ID of the offer.

        Returns:
            dict: A dictionary mapping subject IDs to subject names.
        """
        try:
            response = requests.get(f'{self.base_url}/offer/{offer_id}/')
            if response.status_code != 200:
                return {}

            match = re.search(r'let\s+offer\s*=\s*(\{.*?\})(?=\s*let|\s*</script>)', response.text, re.DOTALL)
            if not match:
                return {}

            offer_data = json.loads(match.group(1).replace('&ndash;', '-'))
            return {str(k): v.get('sn', '') for k, v in offer_data.get('os', {}).items()}
        except (json.JSONDecodeError, Exception):
            return {}
