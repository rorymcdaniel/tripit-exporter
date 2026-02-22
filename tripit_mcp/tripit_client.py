"""
TripIt API client to interact with the TripIt API.
"""

import base64
import hashlib
import hmac
import json
import random
import string
import time
from typing import Dict, List, Optional, Any
from urllib.parse import quote, urlencode

import httpx

from .oauth import TripItOAuth


class TripItAPIError(Exception):
    """Exception raised for errors in the TripIt API."""
    pass


class TripItAPIClient:
    """Client for TripIt API v1.

    Supports all CRUD operations: list, get, create, replace, delete.
    Uses OAuth 1.0a for authentication and JSON format for all requests.
    """

    API_BASE_URL = "https://api.tripit.com/v1"

    def __init__(self, consumer_key: str, consumer_secret: str,
                 oauth_token: str = None, oauth_token_secret: str = None):
        """
        Initialize the TripIt API client.

        Args:
            consumer_key: OAuth consumer key
            consumer_secret: OAuth consumer secret
            oauth_token: OAuth user token (optional)
            oauth_token_secret: OAuth user token secret (optional)
        """
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.oauth_token = oauth_token
        self.oauth_token_secret = oauth_token_secret
        self.client = httpx.Client(timeout=30.0)

    def _generate_nonce(self, length: int = 16) -> str:
        """Generate a random nonce for OAuth requests."""
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

    def _generate_oauth_signature(self, method: str, url: str, params: Dict[str, str],
                                  token_secret: str = "") -> str:
        """
        Generate OAuth signature for a request.

        Args:
            method: HTTP method
            url: Request URL
            params: Request parameters
            token_secret: OAuth token secret for signature key

        Returns:
            The OAuth signature
        """
        # Create signature base string exactly per OAuth 1.0a spec
        param_pairs = sorted((quote(k, safe='~'), quote(v if v is not None else '', safe='~'))
                             for k, v in params.items())
        param_string = '&'.join(f"{k}={v}" for k, v in param_pairs)
        base_string = f"{method.upper()}&{quote(url, safe='')}&{quote(param_string, safe='')}"

        # Create the signing key
        key = f"{quote(self.consumer_secret, safe='')}"
        if token_secret:
            key += f"&{quote(token_secret, safe='')}"
        else:
            key += "&"

        signature = base64.b64encode(
            hmac.new(key.encode(), base_string.encode(), hashlib.sha1).digest()
        ).decode()

        return signature

    def _prepare_oauth_params(self, method: str, url: str,
                              params: Dict[str, str] = None) -> Dict[str, str]:
        """
        Prepare OAuth parameters for a request.

        Args:
            method: HTTP method
            url: Request URL
            params: Additional parameters to include in the signature

        Returns:
            OAuth parameters
        """
        oauth_params = {
            'oauth_consumer_key': self.consumer_key,
            'oauth_nonce': self._generate_nonce(),
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': str(int(time.time())),
            'oauth_version': '1.0',
        }

        if self.oauth_token and self.oauth_token.strip():
            oauth_params['oauth_token'] = self.oauth_token

        # Combine with additional params for signature generation
        all_params = {}
        if params:
            all_params.update(params)
        all_params.update(oauth_params)

        token_secret = self.oauth_token_secret if self.oauth_token_secret and self.oauth_token_secret.strip() else ""
        oauth_params['oauth_signature'] = self._generate_oauth_signature(method, url, all_params, token_secret)

        return oauth_params

    def _build_authorization_header(self, oauth_params: Dict[str, str]) -> str:
        """
        Build OAuth Authorization header from parameters.

        Args:
            oauth_params: OAuth parameters

        Returns:
            Authorization header value
        """
        auth_header = 'OAuth ' + ', '.join(
            f'{quote(k, safe="")}="{quote(v, safe="~")}"' for k, v in sorted(oauth_params.items())
        )
        return auth_header

    def _make_request(self, method: str, endpoint: str, params: Dict[str, str] = None,
                      data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make a request to the TripIt API.

        Args:
            method: HTTP method (GET or POST)
            endpoint: API endpoint (e.g., 'list/trip', 'create')
            params: Query parameters for GET, or query params for POST
            data: For POST requests, the JSON object to send as the 'json' form parameter

        Returns:
            API response data as a dict

        Raises:
            TripItAPIError: On HTTP errors or request failures
        """
        url = f"{self.API_BASE_URL}/{endpoint}"

        # For POST with data, we send it as form-encoded with a 'json' key.
        # The TripIt API expects: POST body with json=<json_string>&format=json
        # Query params and form params both need to be included in OAuth signature.
        form_params = {}
        if method.upper() == 'POST' and data is not None:
            form_params['json'] = json.dumps(data)

        # Merge all params for OAuth signature computation
        sig_params = {}
        if params:
            sig_params.update(params)
        sig_params.update(form_params)

        oauth_params = self._prepare_oauth_params(method, url, sig_params)
        auth_header = self._build_authorization_header(oauth_params)

        headers = {
            'Authorization': auth_header,
            'Accept': 'application/json',
        }

        try:
            if method.upper() == 'GET':
                response = self.client.get(url, params=params, headers=headers)
            elif method.upper() == 'POST':
                # POST: query params go in URL, form data in body
                post_data = {}
                if params:
                    post_data.update(params)
                post_data.update(form_params)
                headers['Content-Type'] = 'application/x-www-form-urlencoded'
                response = self.client.post(url, content=urlencode(post_data), headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            error_message = self._format_http_error(e)
            raise TripItAPIError(error_message) from e

        except (httpx.RequestError, ValueError) as e:
            raise TripItAPIError(f"Request failed: {str(e)}") from e

    def _format_http_error(self, error: httpx.HTTPStatusError) -> str:
        """Format an HTTP error into a readable message, including TripIt warnings/errors."""
        status = error.response.status_code
        status_messages = {
            400: "Bad Request - malformed request",
            401: "Unauthorized - OAuth authentication failed",
            403: "Forbidden - account may be unconfirmed",
            404: "Not Found - resource doesn't exist or no permission",
            500: "Server Error - TripIt internal error",
            503: "Service Unavailable - TripIt is temporarily down",
        }
        base_msg = status_messages.get(status, f"HTTP {status}")
        error_message = f"TripIt API error: {base_msg}"

        try:
            error_data = error.response.json()
            # Check for TripIt Warning or Error objects in response
            if 'Error' in error_data:
                err_obj = error_data['Error']
                if isinstance(err_obj, list):
                    details = "; ".join(e.get('description', str(e)) for e in err_obj)
                else:
                    details = err_obj.get('description', str(err_obj))
                error_message += f" - {details}"
            elif 'Warning' in error_data:
                warn_obj = error_data['Warning']
                if isinstance(warn_obj, list):
                    details = "; ".join(w.get('description', str(w)) for w in warn_obj)
                else:
                    details = warn_obj.get('description', str(warn_obj))
                error_message += f" - Warning: {details}"
        except Exception:
            error_message += f" - {error.response.text}"

        return error_message

    @staticmethod
    def _extract_warnings(response: Dict[str, Any]) -> Optional[List[str]]:
        """Extract any warning messages from a TripIt API response."""
        warnings = []
        if 'Warning' in response:
            warn_obj = response['Warning']
            if isinstance(warn_obj, list):
                for w in warn_obj:
                    warnings.append(w.get('description', str(w)))
            else:
                warnings.append(warn_obj.get('description', str(warn_obj)))
        return warnings if warnings else None

    # ── List operations ──────────────────────────────────────────────

    def list_trips(self, past: bool = False, include_objects: bool = True,
                   traveler: Optional[str] = None,
                   page_num: Optional[int] = None,
                   page_size: Optional[int] = None) -> Dict[str, Any]:
        """
        List trips with optional filters and pagination.

        Args:
            past: If True, returns past trips. If False, returns current and future trips.
            include_objects: Whether to include trip objects in the response.
            traveler: Filter by traveler: 'true', 'false', or 'all'.
            page_num: Page number for pagination (1-based).
            page_size: Number of items per page.

        Returns:
            Dictionary with 'trips' list and 'pagination' metadata.
        """
        params = {
            'format': 'json',
            'past': 'true' if past else 'false',
        }

        if include_objects:
            params['include_objects'] = 'true'

        if traveler is not None:
            params['traveler'] = traveler

        if page_num is not None and page_num > 0:
            params['page_num'] = str(page_num)
        if page_size is not None and page_size > 0:
            params['page_size'] = str(page_size)

        response = self._make_request('GET', 'list/trip', params=params)

        result = {
            'trips': [],
            'pagination': {
                'page_num': int(response.get('page_num', 1)),
                'page_size': int(response.get('page_size', 0)),
                'max_page': int(response.get('max_page', 1)),
            },
        }

        if 'Trip' in response:
            if isinstance(response['Trip'], list):
                result['trips'] = response['Trip']
            else:
                result['trips'] = [response['Trip']]

        warnings = self._extract_warnings(response)
        if warnings:
            result['warnings'] = warnings

        return result

    def get_trip(self, trip_id: str, include_objects: bool = True) -> Dict[str, Any]:
        """
        Get details for a specific trip.

        Args:
            trip_id: The TripIt trip ID.
            include_objects: Whether to include trip objects in the response.

        Returns:
            Trip details dict.
        """
        params = {
            'format': 'json',
            'id': trip_id,
        }

        if include_objects:
            params['include_objects'] = 'true'

        response = self._make_request('GET', 'get/trip', params=params)

        if 'Trip' in response:
            return response['Trip']

        raise TripItAPIError(f"Trip with ID {trip_id} not found")

    # ── Object list/get operations ───────────────────────────────────

    def list_objects(self, trip_id: str, object_type: Optional[str] = None,
                     page_num: Optional[int] = None,
                     page_size: Optional[int] = None) -> Dict[str, Any]:
        """
        List travel objects within a trip.

        Args:
            trip_id: The trip ID to list objects for.
            object_type: Optional type filter (air, lodging, car, activity, etc.)
            page_num: Page number for pagination.
            page_size: Number of items per page.

        Returns:
            Dictionary with objects grouped by type and pagination metadata.
        """
        params = {
            'format': 'json',
            'trip_id': trip_id,
        }

        if page_num is not None and page_num > 0:
            params['page_num'] = str(page_num)
        if page_size is not None and page_size > 0:
            params['page_size'] = str(page_size)

        # Build the endpoint - TripIt API uses: list/object/trip_id/<id>[/type/<type>]
        endpoint = f"list/object/trip_id/{trip_id}"
        if object_type:
            endpoint += f"/type/{object_type}"

        # Remove trip_id from params since it's in the endpoint path
        del params['trip_id']

        response = self._make_request('GET', endpoint, params=params)

        result: Dict[str, Any] = {
            'pagination': {
                'page_num': int(response.get('page_num', 1)),
                'page_size': int(response.get('page_size', 0)),
                'max_page': int(response.get('max_page', 1)),
            },
        }

        # Collect all known object types from response
        object_type_keys = [
            'AirObject', 'LodgingObject', 'CarObject', 'ActivityObject',
            'RestaurantObject', 'TransportObject', 'RailObject', 'NoteObject',
            'CruiseObject', 'DirectionsObject', 'MapObject',
        ]
        objects: Dict[str, list] = {}
        for key in object_type_keys:
            if key in response:
                val = response[key]
                objects[key] = val if isinstance(val, list) else [val]

        result['objects'] = objects

        warnings = self._extract_warnings(response)
        if warnings:
            result['warnings'] = warnings

        return result

    def get_object(self, object_type: str, object_id: str) -> Dict[str, Any]:
        """
        Get a specific travel object by type and ID.

        Args:
            object_type: The object type (e.g., 'air', 'lodging', 'car').
            object_id: The object ID.

        Returns:
            The object details dict.
        """
        params = {
            'format': 'json',
        }

        endpoint = f"get/{object_type}/id/{object_id}"
        response = self._make_request('GET', endpoint, params=params)

        # The response key is the capitalized object type (e.g., AirObject)
        # Try common patterns
        type_map = {
            'air': 'AirObject',
            'lodging': 'LodgingObject',
            'car': 'CarObject',
            'activity': 'ActivityObject',
            'restaurant': 'RestaurantObject',
            'transport': 'TransportObject',
            'rail': 'RailObject',
            'note': 'NoteObject',
            'cruise': 'CruiseObject',
            'directions': 'DirectionsObject',
            'map': 'MapObject',
        }

        response_key = type_map.get(object_type)
        if response_key and response_key in response:
            return response[response_key]

        # Fallback: return full response minus metadata
        for key in ('timestamp', 'num_bytes'):
            response.pop(key, None)
        return response

    def get_profile(self) -> Dict[str, Any]:
        """
        Get the authenticated user's profile.

        Returns:
            Profile details dict.
        """
        params = {'format': 'json'}
        response = self._make_request('GET', 'get/profile', params=params)

        if 'Profile' in response:
            return response['Profile']

        raise TripItAPIError("Could not retrieve profile")

    # ── Create operations ────────────────────────────────────────────

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new object via the TripIt API.

        The data dict should contain the object type as key, e.g.:
        {"Trip": {"start_date": "2026-06-01", "end_date": "2026-06-07", ...}}

        Args:
            data: The object data to create.

        Returns:
            The created object response.
        """
        params = {'format': 'json'}
        response = self._make_request('POST', 'create', params=params, data=data)

        warnings = self._extract_warnings(response)
        if warnings:
            response['_warnings'] = warnings

        return response

    # ── Replace/update operations ────────────────────────────────────

    def replace(self, object_type: str, object_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Replace/update an existing object.

        Args:
            object_type: The object type (e.g., 'trip', 'air', 'lodging').
            object_id: The object ID.
            data: The replacement data.

        Returns:
            The updated object response.
        """
        params = {'format': 'json'}
        endpoint = f"replace/{object_type}/id/{object_id}"
        response = self._make_request('POST', endpoint, params=params, data=data)

        warnings = self._extract_warnings(response)
        if warnings:
            response['_warnings'] = warnings

        return response

    # ── Delete operations ────────────────────────────────────────────

    def delete(self, object_type: str, object_id: str) -> Dict[str, Any]:
        """
        Delete an object by type and ID.

        The TripIt API uses GET for delete operations.

        Args:
            object_type: The object type (e.g., 'trip', 'air', 'lodging').
            object_id: The object ID.

        Returns:
            The delete response.
        """
        params = {'format': 'json'}
        endpoint = f"delete/{object_type}/id/{object_id}"
        response = self._make_request('GET', endpoint, params=params)
        return response
