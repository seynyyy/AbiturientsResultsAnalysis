import json
import pandas as pd
import requests
import re

UNIVERSITY_CODE = 137
UNIVERSITY_OFFERS_IDS_URL = 'https://vstup2023.edbo.gov.ua/offers-universities/'
UNIVERSITY_OFFER_DATA_URL = 'https://vstup2023.edbo.gov.ua/offer-requests/'

# Get PHPSESSID from 2023 site
phpsessid = requests.get('https://vstup2023.edbo.gov.ua').cookies.get('PHPSESSID')


def generate_headers(payload: dict) -> dict:
    content_length = len(json.dumps(payload).encode("utf-8"))
    return {
        'Referer': 'https://vstup2023.edbo.gov.ua/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, /; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Connection': 'keep-alive',
        'Accept-Encoding': 'gzip, deflate, br',
        'Host': 'vstup2023.edbo.gov.ua',
        'Content-Length': str(content_length),
        'Cookie': f'PHPSESSID={phpsessid}',
    }


def get_offers_ids_list() -> list | None:
    # Get the list of ids of offers for the specified university
    url = UNIVERSITY_OFFERS_IDS_URL

    payload = {'university': str(UNIVERSITY_CODE), 'qualification': '1', 'education_base': '40'}
    headers = generate_headers(payload)

    response = requests.post(url, data=payload, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data['universities'][0]['ids'].split(',')
    return None


def get_offer_data(offer_id) -> dict | None:
    url = UNIVERSITY_OFFER_DATA_URL
    payload = {'id': offer_id, 'last': '0'}
    headers = generate_headers(payload)
    resp = requests.post(url, data=payload, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    return None


def get_offer_subjects_map(offer_id):
    url = f'https://vstup2023.edbo.gov.ua/offer/{offer_id}/'
    try:
        resp = requests.get(url)
        if resp.status_code != 200:
            return {}
        
        # Force encoding to UTF-8 to handle Ukrainian characters properly
        resp.encoding = 'utf-8'
        
        # More precise regex pattern to extract the offer JSON object
        pattern = r'let\s+offer\s*=\s*(\{.*?\})(?=\s*let|\s*</script>)'
        m = re.search(pattern, resp.text, re.DOTALL)
        if not m:
            # Try a simpler pattern as fallback
            pattern = r'let\s+offer\s*=\s*(\{.*\})'
            m = re.search(pattern, resp.text, re.DOTALL)
            if not m:
                print(f"No offer data found in HTML for offer_id: {offer_id}")
                return {}
        
        try:
            offer_json = m.group(1)
            # Fix HTML entities that might cause JSON parsing issues
            offer_json = offer_json.replace('&ndash;', '-')
            
            # Parse the JSON data
            offer_data = json.loads(offer_json)
            
            # Extract subject mapping from 'os' field
            os_map = offer_data.get('os', {})
            
            # Create mapping of id -> subject name
            return {str(k): v.get('sn', '') for k, v in os_map.items()}
        except json.JSONDecodeError as e:
            print(f"JSON decode error for offer_id {offer_id}: {str(e)}, content: {offer_json[:100]}...")
            return {}
        except Exception as e:
            print(f"Error parsing offer data for offer_id {offer_id}: {str(e)}")
            return {}
    except Exception as e:
        print(f"Request error for offer_id {offer_id}: {str(e)}")
        return {}

offers_ids = get_offers_ids_list()
filtered = []
all_subject_names = set()
offers_subjects = {}

# First pass: gather all subjects
for offer_id in offers_ids or []:
    id_to_subject = get_offer_subjects_map(offer_id)
    offers_subjects[offer_id] = id_to_subject
    all_subject_names.update(id_to_subject.values())

all_subject_names = sorted([name for name in all_subject_names if name])

# Second pass: build the table
for offer_id in offers_ids or []:
    data = get_offer_data(offer_id)
    if not data or 'requests' not in data or not data['requests']:
        print(f"Empty response for offer_id: {offer_id}")
        continue
    id_to_subject = offers_subjects.get(offer_id, {})
    for req in data['requests']:
        if req.get('ptid') in [1, 2]:
            row = {'p': req.get('p', '')}
            rss_list = req.get('rss', [])
            for rss in rss_list:
                rss_id = str(rss.get('id', ''))
                subj_name = id_to_subject.get(rss_id, '')
                if subj_name:
                    f_val = rss.get('f', '')
                    # Extract only first 3 characters of f value
                    row[subj_name] = f_val[:3] if isinstance(f_val, str) else ''
            filtered.append(row)

# Create DataFrame and drop columns that are empty in all rows
df = pd.DataFrame(filtered)
# Keep only columns that have at least one non-empty value
for col in df.columns:
    if col != 'p' and df[col].astype(str).str.strip().eq('').all():
        df = df.drop(columns=[col])

df.to_csv('offers2023.csv', index=False, encoding='utf-8-sig')
print(df)