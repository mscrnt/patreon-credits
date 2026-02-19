import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime
from path_utils import get_env_path, get_cache_path

load_dotenv(get_env_path())


class PatreonAPI:
    def __init__(self):
        load_dotenv(get_env_path(), override=True)
        self.token = os.getenv('PATREON_TOKEN')
        self.campaign_id = os.getenv('PATREON_CAMPAIGN_ID')
        self.use_dummy_data = os.getenv('USE_DUMMY_DATA', 'false').lower() == 'true'
        self.base_url = 'https://www.patreon.com/api/oauth2/v2'
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

    @staticmethod
    def detect_campaign_id(token):
        """Call the Patreon API to auto-detect the campaign ID from a token.

        Returns (campaign_id, error_message). On success error_message is None.
        """
        try:
            resp = requests.get(
                'https://www.patreon.com/api/oauth2/v2/campaigns',
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json',
                },
                timeout=15,
            )
            if resp.status_code == 401:
                return None, 'Invalid token (401 Unauthorized)'
            if resp.status_code != 200:
                return None, f'API error: {resp.status_code}'
            data = resp.json()
            campaigns = data.get('data', [])
            if not campaigns:
                return None, 'No campaigns found for this token'
            return campaigns[0]['id'], None
        except requests.RequestException as exc:
            return None, str(exc)

    def get_dummy_patrons(self):
        """Generate dummy patron data for testing"""
        dummy_names = [
            "Alice Johnson", "Bob Smith", "Charlie Davis", "Diana Miller",
            "Ethan Wilson", "Fiona Brown", "George Taylor", "Hannah Anderson",
            "Ian Thomas", "Julia Jackson", "Kevin White", "Laura Harris",
            "Michael Martin", "Nancy Thompson", "Oliver Garcia", "Patricia Martinez",
            "Quinn Robinson", "Rachel Clark", "Samuel Rodriguez", "Tina Lewis",
            "Uma Lee", "Victor Walker", "Wendy Hall", "Xavier Allen",
            "Yolanda Young", "Zachary Hernandez", "Amy King", "Brian Wright",
            "Catherine Lopez", "David Hill", "Emma Scott", "Frank Green",
            "Grace Adams", "Henry Baker", "Iris Gonzalez", "Jack Nelson",
            "Karen Carter", "Liam Mitchell", "Mia Perez", "Noah Roberts",
            "Olivia Turner", "Paul Phillips", "Quinn Campbell", "Rose Parker",
            "Steve Evans", "Tracy Edwards", "Ulysses Collins", "Vera Stewart",
            "William Sanchez", "Xena Morris", "Yvonne Rogers", "Zoe Reed"
        ]
        return sorted(dummy_names, key=str.lower)

    def fetch_active_patrons(self):
        """Fetch all active patrons from the campaign"""
        if self.use_dummy_data:
            patrons = self.get_dummy_patrons()
            self.cache_patrons(patrons)
            return patrons

        patrons = []
        url = f'{self.base_url}/campaigns/{self.campaign_id}/members'

        params = {
            'include': 'user',
            'fields[member]': 'full_name,patron_status,email',
            'fields[user]': 'full_name',
            'page[count]': 100
        }

        while url:
            response = requests.get(url, headers=self.headers, params=params if '?' not in url else None)

            if response.status_code != 200:
                raise Exception(f"API Error: {response.status_code} - {response.text}")

            data = response.json()

            # Process members
            for member in data.get('data', []):
                if member.get('attributes', {}).get('patron_status') == 'active_patron':
                    # Try to get name from member attributes first
                    name = member.get('attributes', {}).get('full_name')

                    # If no name in member, try to get from included user data
                    if not name and 'included' in data:
                        user_id = member.get('relationships', {}).get('user', {}).get('data', {}).get('id')
                        for included in data.get('included', []):
                            if included.get('id') == user_id and included.get('type') == 'user':
                                name = included.get('attributes', {}).get('full_name')
                                break

                    if name:
                        patrons.append(name)

            # Check for next page
            url = data.get('links', {}).get('next')
            params = None  # Clear params for pagination URLs

        # Sort alphabetically
        patrons.sort(key=str.lower)

        # Cache the results
        self.cache_patrons(patrons)

        return patrons

    def cache_patrons(self, patrons):
        """Cache patron list to file"""
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'patrons': patrons
        }
        with open(get_cache_path(), 'w') as f:
            json.dump(cache_data, f, indent=2)

    def get_cached_patrons(self):
        """Get patrons from cache if available"""
        path = get_cache_path()
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f).get('patrons', [])
        return []
