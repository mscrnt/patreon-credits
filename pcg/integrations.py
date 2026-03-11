"""Unified integration clients for fetching supporter names.

Each class exposes a simple interface returning sorted unique name lists,
matching the style of PatreonAPI.fetch_active_patrons().
"""

import json
import logging
import os
from datetime import datetime

import requests

logger = logging.getLogger(__name__)


class BuyMeACoffeeAPI:
    """Fetch supporter names from Buy Me a Coffee REST API."""

    BASE_URL = 'https://developers.buymeacoffee.com/api/v1'

    def __init__(self, token):
        self.token = token

    def fetch_supporters(self):
        """Return sorted unique supporter names."""
        names = set()
        url = f'{self.BASE_URL}/supporters'
        headers = {'Authorization': f'Bearer {self.token}'}
        page = 1
        while True:
            resp = requests.get(url, headers=headers,
                                params={'page': page}, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get('data', []):
                name = (item.get('payer_name') or
                        item.get('support_name') or '').strip()
                if name:
                    names.add(name)
            # BMC uses next_page_url for pagination
            if not data.get('next_page_url'):
                break
            page += 1
        logger.info("Fetched %d supporters from Buy Me a Coffee", len(names))
        return sorted(names)


class StreamElementsAPI:
    """Fetch tipper names from StreamElements REST API."""

    BASE_URL = 'https://api.streamelements.com/kappa/v2'

    def __init__(self, jwt, channel_id):
        self.jwt = jwt
        self.channel_id = channel_id

    def fetch_tippers(self, after_ms=None, before_ms=None):
        """Return sorted unique tipper display names.

        *after_ms* / *before_ms* are optional epoch-millisecond timestamps
        that bracket the date range (maps to the SE ``after`` / ``before``
        query params).  Only tips with ``status == 'success'`` are included.
        """
        names = set()
        url = f'{self.BASE_URL}/tips/{self.channel_id}'
        headers = {
            'Authorization': f'Bearer {self.jwt}',
            'Accept': 'application/json',
        }
        params = {'limit': 100, 'offset': 0, 'sort': '-createdAt'}
        if after_ms is not None:
            params['after'] = int(after_ms)
        if before_ms is not None:
            params['before'] = int(before_ms)
        while True:
            resp = requests.get(url, headers=headers,
                                params=params, timeout=30)
            if resp.status_code == 401:
                raise ValueError('Invalid or expired JWT token')
            resp.raise_for_status()
            data = resp.json()
            docs = data.get('docs', [])
            if not docs:
                break
            for doc in docs:
                if doc.get('status') != 'success':
                    continue
                donation = doc.get('donation', {})
                user = donation.get('user', {})
                name = (user.get('username') or '').strip()
                if name:
                    names.add(name)
            total = data.get('total', 0)
            if params['offset'] + len(docs) >= total:
                break
            params['offset'] += params['limit']
        logger.info("Fetched %d tippers from StreamElements", len(names))
        return sorted(names)


class WebhookStore:
    """Base class for webhook-based name stores.

    Persists supporter names in a local JSON cache file with per-name
    timestamps, an auto-clear schedule, and clear-by-time-frame support.
    Subclasses override ``_extract_name()`` to handle platform-specific
    webhook payloads.
    """

    SCHEDULE_DAYS = {
        'never': None,
        'daily': 1,
        'weekly': 7,
        'monthly': 30,
    }

    def __init__(self, cache_path):
        self.cache_path = cache_path

    def _extract_name(self, payload):
        """Return the supporter name from a webhook payload dict.

        Subclasses must override this.
        """
        raise NotImplementedError

    def get_names(self):
        """Return sorted unique names from the cache."""
        self._check_auto_clear()
        data = self._read()
        return sorted(set(e['name'] for e in data['names']))

    def add_webhook_event(self, payload):
        """Extract and store the supporter name from a webhook payload."""
        self._check_auto_clear()

        if isinstance(payload, str):
            payload = json.loads(payload)

        name = self._extract_name(payload)
        if not name:
            return

        data = self._read()
        existing = {e['name'] for e in data['names']}
        if name not in existing:
            data['names'].append({
                'name': name,
                'added': datetime.utcnow().isoformat(),
            })
            data['names'].sort(key=lambda e: e['name'])
            self._write(data)

    def merge_names(self, names):
        """Bulk-add a list of name strings (from an API fetch).

        Skips duplicates. Each new name gets a timestamp.
        """
        if not names:
            return
        self._check_auto_clear()
        data = self._read()
        existing = {e['name'] for e in data['names']}
        now = datetime.utcnow().isoformat()
        added = 0
        for name in names:
            name = (name or '').strip()
            if name and name not in existing:
                data['names'].append({'name': name, 'added': now})
                existing.add(name)
                added += 1
        if added:
            data['names'].sort(key=lambda e: e['name'])
            self._write(data)

    def clear_names(self):
        """Remove all stored names and update last_cleared timestamp."""
        data = self._read()
        data['names'] = []
        data['last_cleared'] = datetime.utcnow().isoformat()
        self._write(data)

    def clear_older_than(self, days):
        """Remove names added more than *days* ago."""
        cutoff = datetime.utcnow().isoformat()
        now = datetime.utcnow()
        data = self._read()
        kept = []
        removed = 0
        for entry in data['names']:
            try:
                added = datetime.fromisoformat(entry['added'])
            except (ValueError, TypeError, KeyError):
                kept.append(entry)
                continue
            if (now - added).total_seconds() < days * 86400:
                kept.append(entry)
            else:
                removed += 1
        data['names'] = kept
        data['last_cleared'] = cutoff
        self._write(data)
        return removed

    def get_schedule(self):
        """Return the current auto-clear schedule and metadata."""
        data = self._read()
        return {
            'auto_clear': data['auto_clear'],
            'last_cleared': data['last_cleared'],
            'count': len(data['names']),
        }

    def set_schedule(self, schedule):
        """Set the auto-clear schedule.

        Accepts 'never', 'daily', 'weekly', 'monthly', or a positive
        integer for custom days.
        """
        data = self._read()
        if isinstance(schedule, int) and schedule > 0:
            data['auto_clear'] = schedule
        elif schedule in self.SCHEDULE_DAYS:
            data['auto_clear'] = schedule
        else:
            data['auto_clear'] = 'never'
        if not data['last_cleared']:
            data['last_cleared'] = datetime.utcnow().isoformat()
        self._write(data)

    def _check_auto_clear(self):
        """If the auto-clear schedule has elapsed, clear names."""
        data = self._read()
        schedule = data['auto_clear']
        last_cleared = data['last_cleared']

        if schedule == 'never' or not last_cleared:
            return

        if isinstance(schedule, int):
            interval_days = schedule
        else:
            interval_days = self.SCHEDULE_DAYS.get(schedule)
        if not interval_days:
            return

        try:
            cleared_at = datetime.fromisoformat(last_cleared)
        except (ValueError, TypeError):
            return

        if (datetime.utcnow() - cleared_at).total_seconds() >= interval_days * 86400:
            data['names'] = []
            data['last_cleared'] = datetime.utcnow().isoformat()
            self._write(data)

    def _read(self):
        if os.path.isfile(self.cache_path):
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {'names': [], 'auto_clear': 'never', 'last_cleared': None}

    def _write(self, data):
        with open(self.cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)


class KoFiStore(WebhookStore):
    """Ko-fi webhook name store.

    Ko-fi sends a form-encoded ``data`` field containing JSON with
    a ``from_name`` key.
    """

    def _extract_name(self, payload):
        return (payload.get('from_name') or '').strip()


class BmcStore(WebhookStore):
    """Buy Me a Coffee webhook name store.

    BMC webhook payloads contain supporter names in ``supporter_name``,
    ``payer_name``, or nested under ``response.supporter_name``.
    """

    def _extract_name(self, payload):
        name = (payload.get('supporter_name')
                or payload.get('payer_name')
                or payload.get('support_name')
                or '').strip()
        if not name:
            resp = payload.get('response') or payload.get('data') or {}
            if isinstance(resp, dict):
                name = (resp.get('supporter_name')
                        or resp.get('payer_name')
                        or resp.get('support_name')
                        or '').strip()
        return name


class StreamElementsStore(WebhookStore):
    """StreamElements tipper name store.

    Names are added via ``merge_names()`` after an API fetch rather than
    from individual webhook events.
    """

    def _extract_name(self, payload):
        return (payload.get('name') or '').strip()


class YouTubeAPI:
    """Fetch YouTube channel member names via the YouTube Data API v3.

    Requires OAuth 2.0 credentials with the
    youtube.channel-memberships.creator scope.
    """

    BASE_URL = 'https://www.googleapis.com/youtube/v3'

    def __init__(self, access_token):
        self.access_token = access_token

    def fetch_members(self):
        """Return sorted unique member display names."""
        names = set()
        url = f'{self.BASE_URL}/members'
        headers = {'Authorization': f'Bearer {self.access_token}'}
        params = {'part': 'snippet', 'maxResults': 50}
        while True:
            resp = requests.get(url, headers=headers,
                                params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get('items', []):
                details = item.get('snippet', {}).get('memberDetails', {})
                name = (details.get('displayName') or '').strip()
                if name:
                    names.add(name)
            token = data.get('nextPageToken')
            if not token:
                break
            params['pageToken'] = token
        logger.info("Fetched %d members from YouTube", len(names))
        return sorted(names)


class YouTubeOAuth:
    """Handle YouTube OAuth 2.0 token lifecycle.

    Manages the authorization URL, code-to-token exchange, token
    storage, and automatic refresh of expired access tokens.
    """

    AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
    TOKEN_URL = 'https://oauth2.googleapis.com/token'
    SCOPE = 'https://www.googleapis.com/auth/youtube.channel-memberships.creator'

    def __init__(self, token_path):
        self.token_path = token_path

    def get_auth_url(self, client_id, redirect_uri):
        """Build the Google OAuth consent URL."""
        from urllib.parse import urlencode
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': self.SCOPE,
            'access_type': 'offline',
            'prompt': 'consent',
        }
        return f'{self.AUTH_URL}?{urlencode(params)}'

    def exchange_code(self, code, client_id, client_secret, redirect_uri):
        """Exchange an authorization code for access + refresh tokens."""
        resp = requests.post(self.TOKEN_URL, data={
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
        }, timeout=30)
        resp.raise_for_status()
        token_data = resp.json()

        expires_in = token_data.get('expires_in', 3600)
        from datetime import timedelta
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        self._write({
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token', ''),
            'expires_at': expires_at.isoformat(),
        })
        return token_data['access_token']

    def get_access_token(self, client_id, client_secret):
        """Return a valid access token, refreshing if expired."""
        data = self._read()
        if not data or not data.get('refresh_token'):
            raise RuntimeError('YouTube not authorized')

        expires_at = datetime.fromisoformat(data['expires_at'])
        if datetime.utcnow() < expires_at:
            return data['access_token']

        # Refresh the token
        resp = requests.post(self.TOKEN_URL, data={
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': data['refresh_token'],
            'grant_type': 'refresh_token',
        }, timeout=30)
        resp.raise_for_status()
        token_data = resp.json()

        expires_in = token_data.get('expires_in', 3600)
        from datetime import timedelta
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        data['access_token'] = token_data['access_token']
        data['expires_at'] = expires_at.isoformat()
        self._write(data)
        return data['access_token']

    def is_authorized(self):
        """Check if valid tokens are stored."""
        data = self._read()
        return bool(data and data.get('refresh_token'))

    def revoke(self):
        """Delete stored tokens."""
        if os.path.isfile(self.token_path):
            os.remove(self.token_path)

    def _read(self):
        if os.path.isfile(self.token_path):
            try:
                with open(self.token_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return None

    def _write(self, data):
        with open(self.token_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
