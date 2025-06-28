import pandas as pd
from tqdm import tqdm

class NmtResultsTableBuilder:
    """
    A class to build a pandas DataFrame table from university NMT exam results data.
    """

    def __init__(self, nmt_results_service):
        """
        Initializes the NmtResultsTableBuilder instance.

        Args:
            nmt_results_service: A service instance to interact with NMT results data.
        """
        self.nmt_results_service = nmt_results_service

    def build_results_table(self):
        """
        Builds a pandas DataFrame containing filtered NMT results data.

        Returns:
            pd.DataFrame: A DataFrame containing the processed NMT results data.
        """
        offer_ids = self.nmt_results_service.get_nmt_offer_ids_list() or []
        all_subject_names = set()
        offers_subjects = {}

        # Collect all unique subject names with progress bar
        for offer_id in tqdm(offer_ids, desc='Collecting subject names'):
            offers_subjects[offer_id] = self.nmt_results_service.get_nmt_offer_subjects_map(offer_id)
            all_subject_names.update([name for name in offers_subjects[offer_id].values() if name])

        # Ensure all_subject_names are unique and not empty
        all_subject_names = sorted(set([name for name in all_subject_names if name]))
        columns = ['p'] + all_subject_names

        # Process each offer ID to extract relevant data with progress bar
        filtered = []
        for offer_id in tqdm(offer_ids, desc='Processing NMT results'):
            data = self.nmt_results_service.get_nmt_offer_data(offer_id)
            if not data or 'requests' not in data:
                continue
            id_to_subject = offers_subjects.get(offer_id, {})
            for req in data['requests']:
                if req.get('ptid') in [1, 2]:
                    row = {col: '' for col in columns}  # Ensure all columns exist
                    row['p'] = req.get('p', '')
                    for rss in req.get('rss', []):
                        subj_name = id_to_subject.get(str(rss.get('id', '')))
                        if subj_name and subj_name in all_subject_names:
                            row[subj_name] = (rss.get('f', '')[:3]
                                              if isinstance(rss.get('f', ''), str) else '')
                    # Only keep keys from columns
                    row = {col: row.get(col, '') for col in columns}
                    # Check if all values except 'p' are empty/null
                    if all((v == '' or pd.isna(v)) for k, v in row.items() if k != 'p'):
                        continue  # Skip this row
                    filtered.append(row)

        df = pd.DataFrame(filtered, columns=columns)
        # Drop columns that are empty in all rows (except 'p')
        cols_to_drop = [col for col in df.columns if col != 'p' and df[col].astype(str).str.strip().eq('').all()]
        df = df.drop(columns=cols_to_drop)
        # Assert all rows have the same number of columns as header
        for i, row in df.iterrows():
            assert len(row) == len(df.columns), f"Row {i} has {len(row)} values, expected {len(df.columns)}"
        return df
