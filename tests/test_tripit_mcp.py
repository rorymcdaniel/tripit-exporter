"""
Tests for the TripIt MCP server functionality.
"""

import asyncio
import json
import os
from unittest.mock import patch, MagicMock, PropertyMock

import httpx
import pytest

from tripit_mcp.tripit_client import TripItAPIClient, TripItAPIError
from tripit_mcp.models import (
    CreateTripInput,
    UpdateTripInput,
    ListTripsInput,
    GetTripInput,
    DeleteTripInput,
    ListObjectsInput,
    GetObjectInput,
    DeleteObjectInput,
    CreateFlightInput,
    FlightSegmentInput,
    CreateLodgingInput,
    CreateCarRentalInput,
    CreateActivityInput,
    CreateRestaurantInput,
    CreateTransportInput,
    CreateRailInput,
    RailSegmentInput,
    CreateNoteInput,
)


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def mock_env_vars():
    """Mock environment variables."""
    with patch.dict(os.environ, {
        "TRIPIT_CONSUMER_KEY": "test_consumer_key",
        "TRIPIT_CONSUMER_SECRET": "test_consumer_secret",
        "TRIPIT_OAUTH_TOKEN": "test_oauth_token",
        "TRIPIT_OAUTH_TOKEN_SECRET": "test_oauth_token_secret"
    }):
        yield


@pytest.fixture
def mock_tripit_client():
    """Mock TripIt API client."""
    with patch("tripit_mcp.server.TripItAPIClient") as mock_client:
        client_instance = MagicMock()
        mock_client.return_value = client_instance
        yield client_instance


@pytest.fixture
def api_client():
    """Create a TripItAPIClient with mocked _make_request."""
    client = TripItAPIClient("key", "secret")
    return client


# ── Pydantic Model Tests ────────────────────────────────────────────


class TestCreateTripInput:
    def test_valid_input(self):
        inp = CreateTripInput(
            primary_location="New York, NY",
            start_date="2026-06-01",
            end_date="2026-06-07",
        )
        assert inp.primary_location == "New York, NY"
        assert inp.start_date == "2026-06-01"
        assert inp.is_private is False

    def test_with_optional_fields(self):
        inp = CreateTripInput(
            primary_location="London",
            start_date="2026-07-01",
            end_date="2026-07-10",
            display_name="UK Trip",
            is_private=True,
        )
        assert inp.display_name == "UK Trip"
        assert inp.is_private is True

    def test_invalid_date_format(self):
        with pytest.raises(Exception):
            CreateTripInput(
                primary_location="Paris",
                start_date="June 1, 2026",
                end_date="2026-06-07",
            )

    def test_empty_location_rejected(self):
        with pytest.raises(Exception):
            CreateTripInput(
                primary_location="",
                start_date="2026-06-01",
                end_date="2026-06-07",
            )

    def test_whitespace_stripped(self):
        inp = CreateTripInput(
            primary_location="  Tokyo  ",
            start_date="2026-06-01",
            end_date="2026-06-07",
        )
        assert inp.primary_location == "Tokyo"


class TestUpdateTripInput:
    def test_partial_update(self):
        inp = UpdateTripInput(
            trip_id="12345",
            display_name="New Name",
        )
        assert inp.trip_id == "12345"
        assert inp.display_name == "New Name"
        assert inp.start_date is None

    def test_trip_id_required(self):
        with pytest.raises(Exception):
            UpdateTripInput()


class TestListTripsInput:
    def test_defaults(self):
        inp = ListTripsInput()
        assert inp.past is False
        assert inp.traveler is None
        assert inp.page_num is None

    def test_pagination(self):
        inp = ListTripsInput(page_num=2, page_size=10)
        assert inp.page_num == 2
        assert inp.page_size == 10

    def test_invalid_page_num(self):
        with pytest.raises(Exception):
            ListTripsInput(page_num=0)

    def test_invalid_page_size(self):
        with pytest.raises(Exception):
            ListTripsInput(page_size=26)


class TestFlightSegmentInput:
    def test_minimal_segment(self):
        seg = FlightSegmentInput(start_date="2026-06-01")
        assert seg.start_date == "2026-06-01"
        assert seg.start_airport_code is None

    def test_full_segment(self):
        seg = FlightSegmentInput(
            start_date="2026-06-01",
            start_time="08:00:00",
            end_date="2026-06-01",
            end_time="11:30:00",
            start_airport_code="SFO",
            end_airport_code="JFK",
            marketing_airline="United Airlines",
            marketing_flight_number="137",
            seats="23A",
        )
        assert seg.start_airport_code == "SFO"
        assert seg.marketing_flight_number == "137"


class TestCreateFlightInput:
    def test_valid_flight(self):
        inp = CreateFlightInput(
            trip_id="12345",
            segments=[
                {"start_date": "2026-06-01", "start_airport_code": "SFO", "end_airport_code": "JFK"},
            ],
        )
        assert inp.trip_id == "12345"
        assert len(inp.segments) == 1

    def test_empty_segments_rejected(self):
        with pytest.raises(Exception):
            CreateFlightInput(trip_id="12345", segments=[])

    def test_multi_segment_flight(self):
        inp = CreateFlightInput(
            trip_id="12345",
            segments=[
                {"start_date": "2026-06-01"},
                {"start_date": "2026-06-03"},
            ],
        )
        assert len(inp.segments) == 2


class TestCreateLodgingInput:
    def test_valid_lodging(self):
        inp = CreateLodgingInput(
            trip_id="12345",
            start_date="2026-06-01",
            end_date="2026-06-05",
            supplier_name="Hilton",
        )
        assert inp.supplier_name == "Hilton"
        assert inp.room_type is None


class TestCreateCarRentalInput:
    def test_valid_car_rental(self):
        inp = CreateCarRentalInput(
            trip_id="12345",
            start_date="2026-06-01",
            end_date="2026-06-05",
            supplier_name="Hertz",
            car_type="SUV",
        )
        assert inp.car_type == "SUV"


class TestCreateActivityInput:
    def test_valid_activity(self):
        inp = CreateActivityInput(
            trip_id="12345",
            display_name="City Tour",
            start_date="2026-06-02",
        )
        assert inp.display_name == "City Tour"

    def test_name_required(self):
        with pytest.raises(Exception):
            CreateActivityInput(
                trip_id="12345",
                display_name="",
                start_date="2026-06-02",
            )


class TestCreateRestaurantInput:
    def test_valid_restaurant(self):
        inp = CreateRestaurantInput(
            trip_id="12345",
            display_name="Le Bernardin",
            date="2026-06-03",
            time="19:30:00",
            cuisine="French",
        )
        assert inp.cuisine == "French"
        assert inp.number_patrons is None


class TestCreateTransportInput:
    def test_valid_transport(self):
        inp = CreateTransportInput(
            trip_id="12345",
            start_date="2026-06-01",
            start_location_name="JFK Airport",
            end_location_name="Hilton Times Square",
        )
        assert inp.start_location_name == "JFK Airport"


class TestCreateRailInput:
    def test_valid_rail(self):
        inp = CreateRailInput(
            trip_id="12345",
            segments=[{"start_date": "2026-06-02", "carrier_name": "Amtrak", "train_number": "171"}],
        )
        assert len(inp.segments) == 1
        assert inp.segments[0].carrier_name == "Amtrak"


class TestCreateNoteInput:
    def test_valid_note(self):
        inp = CreateNoteInput(
            trip_id="12345",
            display_name="Packing List",
            text="Don't forget sunscreen",
        )
        assert inp.display_name == "Packing List"

    def test_note_with_url(self):
        inp = CreateNoteInput(
            trip_id="12345",
            display_name="Travel Guide",
            url="https://example.com/guide",
        )
        assert inp.url == "https://example.com/guide"


class TestDeleteObjectInput:
    def test_valid_delete(self):
        inp = DeleteObjectInput(object_type="air", object_id="67890")
        assert inp.object_type == "air"


# ── TripItAPIClient Tests ───────────────────────────────────────────


class TestTripItAPIClientListTrips:
    def test_list_trips_basic(self):
        with patch.object(TripItAPIClient, "_make_request") as mock_request:
            mock_request.return_value = {
                "Trip": [
                    {
                        "id": "12345",
                        "display_name": "Test Trip",
                        "start_date": "2026-01-01",
                        "end_date": "2026-01-07",
                        "primary_location": "Test Location",
                        "is_private": "false",
                    }
                ],
                "page_num": "1",
                "page_size": "5",
                "max_page": "1",
            }

            client = TripItAPIClient("key", "secret")
            result = client.list_trips(past=False)

            assert len(result["trips"]) == 1
            assert result["trips"][0]["id"] == "12345"
            assert result["pagination"]["page_num"] == 1

            mock_request.assert_called_once_with(
                "GET",
                "list/trip",
                params={
                    "format": "json",
                    "past": "false",
                    "include_objects": "true",
                },
            )

    def test_list_trips_single_trip_as_dict(self):
        """TripIt returns a dict instead of list for single trips."""
        with patch.object(TripItAPIClient, "_make_request") as mock_request:
            mock_request.return_value = {
                "Trip": {
                    "id": "12345",
                    "display_name": "Solo Trip",
                },
                "page_num": "1",
                "page_size": "5",
                "max_page": "1",
            }

            client = TripItAPIClient("key", "secret")
            result = client.list_trips()

            assert len(result["trips"]) == 1
            assert result["trips"][0]["display_name"] == "Solo Trip"

    def test_list_trips_empty(self):
        with patch.object(TripItAPIClient, "_make_request") as mock_request:
            mock_request.return_value = {
                "page_num": "1",
                "page_size": "5",
                "max_page": "1",
            }

            client = TripItAPIClient("key", "secret")
            result = client.list_trips()

            assert result["trips"] == []

    def test_list_trips_with_pagination(self):
        with patch.object(TripItAPIClient, "_make_request") as mock_request:
            mock_request.return_value = {
                "Trip": [],
                "page_num": "2",
                "page_size": "10",
                "max_page": "3",
            }

            client = TripItAPIClient("key", "secret")
            result = client.list_trips(page_num=2, page_size=10)

            call_params = mock_request.call_args[1]["params"]
            assert call_params["page_num"] == "2"
            assert call_params["page_size"] == "10"

    def test_list_trips_with_traveler_filter(self):
        with patch.object(TripItAPIClient, "_make_request") as mock_request:
            mock_request.return_value = {"Trip": [], "page_num": "1", "page_size": "5", "max_page": "1"}

            client = TripItAPIClient("key", "secret")
            client.list_trips(traveler="all")

            call_params = mock_request.call_args[1]["params"]
            assert call_params["traveler"] == "all"


class TestTripItAPIClientGetTrip:
    def test_get_trip(self):
        with patch.object(TripItAPIClient, "_make_request") as mock_request:
            mock_request.return_value = {
                "Trip": {
                    "id": "12345",
                    "display_name": "Test Trip",
                    "start_date": "2026-01-01",
                    "end_date": "2026-01-07",
                }
            }

            client = TripItAPIClient("key", "secret")
            trip = client.get_trip(trip_id="12345")

            assert trip["id"] == "12345"
            assert trip["display_name"] == "Test Trip"

    def test_get_trip_not_found(self):
        with patch.object(TripItAPIClient, "_make_request") as mock_request:
            mock_request.return_value = {}

            client = TripItAPIClient("key", "secret")
            with pytest.raises(TripItAPIError, match="not found"):
                client.get_trip(trip_id="99999")


class TestTripItAPIClientCreate:
    def test_create_trip(self):
        with patch.object(TripItAPIClient, "_make_request") as mock_request:
            mock_request.return_value = {
                "Trip": {
                    "id": "99999",
                    "display_name": "New Trip",
                    "start_date": "2026-06-01",
                    "end_date": "2026-06-07",
                }
            }

            client = TripItAPIClient("key", "secret")
            result = client.create({
                "Trip": {
                    "start_date": "2026-06-01",
                    "end_date": "2026-06-07",
                    "primary_location": "New York, NY",
                }
            })

            assert "Trip" in result
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][0] == "POST"
            assert call_args[0][1] == "create"

    def test_create_with_data_passed_as_json(self):
        with patch.object(TripItAPIClient, "_make_request") as mock_request:
            mock_request.return_value = {"AirObject": {"id": "111"}}

            client = TripItAPIClient("key", "secret")
            data = {"AirObject": {"trip_id": "12345", "Segment": {"start_date": "2026-06-01"}}}
            client.create(data)

            call_kwargs = mock_request.call_args[1]
            assert call_kwargs["data"] == data


class TestTripItAPIClientReplace:
    def test_replace_trip(self):
        with patch.object(TripItAPIClient, "_make_request") as mock_request:
            mock_request.return_value = {
                "Trip": {"id": "12345", "display_name": "Updated Trip"}
            }

            client = TripItAPIClient("key", "secret")
            result = client.replace("trip", "12345", {"Trip": {"display_name": "Updated Trip"}})

            assert result["Trip"]["display_name"] == "Updated Trip"
            call_args = mock_request.call_args
            assert call_args[0][1] == "replace/trip/id/12345"


class TestTripItAPIClientDelete:
    def test_delete_trip(self):
        with patch.object(TripItAPIClient, "_make_request") as mock_request:
            mock_request.return_value = {"timestamp": "123"}

            client = TripItAPIClient("key", "secret")
            result = client.delete("trip", "12345")

            call_args = mock_request.call_args
            assert call_args[0][0] == "GET"
            assert call_args[0][1] == "delete/trip/id/12345"

    def test_delete_object(self):
        with patch.object(TripItAPIClient, "_make_request") as mock_request:
            mock_request.return_value = {"timestamp": "123"}

            client = TripItAPIClient("key", "secret")
            client.delete("air", "67890")

            call_args = mock_request.call_args
            assert call_args[0][1] == "delete/air/id/67890"


class TestTripItAPIClientListObjects:
    def test_list_objects(self):
        with patch.object(TripItAPIClient, "_make_request") as mock_request:
            mock_request.return_value = {
                "AirObject": [{"id": "111"}],
                "LodgingObject": {"id": "222"},
                "page_num": "1",
                "page_size": "10",
                "max_page": "1",
            }

            client = TripItAPIClient("key", "secret")
            result = client.list_objects(trip_id="12345")

            assert "AirObject" in result["objects"]
            assert len(result["objects"]["AirObject"]) == 1
            # Single object should be wrapped in list
            assert len(result["objects"]["LodgingObject"]) == 1

            call_args = mock_request.call_args
            assert call_args[0][1] == "list/object/trip_id/12345"

    def test_list_objects_with_type_filter(self):
        with patch.object(TripItAPIClient, "_make_request") as mock_request:
            mock_request.return_value = {
                "AirObject": [{"id": "111"}],
                "page_num": "1",
                "page_size": "10",
                "max_page": "1",
            }

            client = TripItAPIClient("key", "secret")
            client.list_objects(trip_id="12345", object_type="air")

            call_args = mock_request.call_args
            assert call_args[0][1] == "list/object/trip_id/12345/type/air"


class TestTripItAPIClientGetObject:
    def test_get_air_object(self):
        with patch.object(TripItAPIClient, "_make_request") as mock_request:
            mock_request.return_value = {
                "AirObject": {"id": "111", "Segment": []}
            }

            client = TripItAPIClient("key", "secret")
            result = client.get_object("air", "111")

            assert result["id"] == "111"
            call_args = mock_request.call_args
            assert call_args[0][1] == "get/air/id/111"


class TestTripItAPIClientGetProfile:
    def test_get_profile(self):
        with patch.object(TripItAPIClient, "_make_request") as mock_request:
            mock_request.return_value = {
                "Profile": {
                    "screen_name": "testuser",
                    "public_display_name": "Test User",
                }
            }

            client = TripItAPIClient("key", "secret")
            profile = client.get_profile()

            assert profile["screen_name"] == "testuser"

    def test_get_profile_error(self):
        with patch.object(TripItAPIClient, "_make_request") as mock_request:
            mock_request.return_value = {}

            client = TripItAPIClient("key", "secret")
            with pytest.raises(TripItAPIError, match="Could not retrieve profile"):
                client.get_profile()


class TestTripItAPIClientWarnings:
    def test_extract_warnings_list(self):
        response = {
            "Warning": [
                {"description": "Warning 1"},
                {"description": "Warning 2"},
            ]
        }
        warnings = TripItAPIClient._extract_warnings(response)
        assert warnings == ["Warning 1", "Warning 2"]

    def test_extract_warnings_single(self):
        response = {"Warning": {"description": "Single warning"}}
        warnings = TripItAPIClient._extract_warnings(response)
        assert warnings == ["Single warning"]

    def test_no_warnings(self):
        response = {"Trip": {"id": "123"}}
        warnings = TripItAPIClient._extract_warnings(response)
        assert warnings is None


# ── TripItService Tests ──────────────────────────────────────────────


try:
    from tripit_mcp.server import TripItService
    _server_import_ok = True
except Exception:
    _server_import_ok = False


@pytest.mark.skipif(not _server_import_ok, reason="FastMCP server import unavailable in this environment")
class TestTripItService:
    def test_init(self, mock_env_vars, mock_tripit_client):
        service = TripItService()

        assert service.consumer_key == "test_consumer_key"
        assert service.consumer_secret == "test_consumer_secret"
        assert service.oauth_token == "test_oauth_token"
        assert service.oauth_token_secret == "test_oauth_token_secret"

    def test_missing_credentials(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="credentials not found"):
                TripItService()


# ── Client Internal Method Tests ─────────────────────────────────────


class TestMakeRequestGET:
    """Test _make_request with real httpx mocking."""

    def test_get_success(self):
        client = TripItAPIClient("key", "secret", "token", "token_secret")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"Trip": {"id": "123"}}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, "get", return_value=mock_response) as mock_get:
            result = client._make_request("GET", "get/trip", params={"format": "json", "id": "123"})
            assert result == {"Trip": {"id": "123"}}
            mock_get.assert_called_once()
            # Verify URL was passed as first positional arg
            call_args = mock_get.call_args
            assert call_args[0][0] == "https://api.tripit.com/v1/get/trip"

    def test_get_http_error(self):
        client = TripItAPIClient("key", "secret", "token", "token_secret")
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_response.json.side_effect = ValueError("no json")
        mock_request = MagicMock()

        error = httpx.HTTPStatusError("Not Found", request=mock_request, response=mock_response)
        mock_response.raise_for_status.side_effect = error

        with patch.object(client.client, "get", return_value=mock_response):
            with pytest.raises(TripItAPIError, match="Not Found"):
                client._make_request("GET", "get/trip", params={"format": "json"})

    def test_request_error(self):
        client = TripItAPIClient("key", "secret", "token", "token_secret")

        with patch.object(client.client, "get", side_effect=httpx.RequestError("Connection refused")):
            with pytest.raises(TripItAPIError, match="Request failed"):
                client._make_request("GET", "list/trip", params={"format": "json"})

    def test_unsupported_method(self):
        client = TripItAPIClient("key", "secret")
        with pytest.raises(TripItAPIError, match="Unsupported HTTP method"):
            client._make_request("DELETE", "some/endpoint")


class TestMakeRequestPOST:
    def test_post_with_data(self):
        client = TripItAPIClient("key", "secret", "token", "token_secret")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"Trip": {"id": "999"}}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, "post", return_value=mock_response) as mock_post:
            result = client._make_request(
                "POST", "create",
                params={"format": "json"},
                data={"Trip": {"start_date": "2026-06-01"}},
            )
            assert result["Trip"]["id"] == "999"
            mock_post.assert_called_once()
            # Verify content-type header
            call_kwargs = mock_post.call_args[1]
            assert call_kwargs["headers"]["Content-Type"] == "application/x-www-form-urlencoded"

    def test_post_without_data(self):
        client = TripItAPIClient("key", "secret", "token", "token_secret")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "ok"}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, "post", return_value=mock_response):
            result = client._make_request("POST", "some/endpoint", params={"format": "json"})
            assert result["result"] == "ok"


class TestFormatHttpError:
    def _make_error(self, status_code, json_body=None, text="error"):
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.text = text
        if json_body is not None:
            mock_response.json.return_value = json_body
        else:
            mock_response.json.side_effect = ValueError("no json")
        mock_request = MagicMock()
        return httpx.HTTPStatusError("error", request=mock_request, response=mock_response)

    def test_400_error(self):
        client = TripItAPIClient("key", "secret")
        error = self._make_error(400)
        msg = client._format_http_error(error)
        assert "Bad Request" in msg

    def test_401_error(self):
        client = TripItAPIClient("key", "secret")
        error = self._make_error(401)
        msg = client._format_http_error(error)
        assert "Unauthorized" in msg

    def test_403_error(self):
        client = TripItAPIClient("key", "secret")
        error = self._make_error(403)
        msg = client._format_http_error(error)
        assert "Forbidden" in msg

    def test_404_error(self):
        client = TripItAPIClient("key", "secret")
        error = self._make_error(404)
        msg = client._format_http_error(error)
        assert "Not Found" in msg

    def test_500_error(self):
        client = TripItAPIClient("key", "secret")
        error = self._make_error(500)
        msg = client._format_http_error(error)
        assert "Server Error" in msg

    def test_503_error(self):
        client = TripItAPIClient("key", "secret")
        error = self._make_error(503)
        msg = client._format_http_error(error)
        assert "Service Unavailable" in msg

    def test_unknown_status(self):
        client = TripItAPIClient("key", "secret")
        error = self._make_error(418)
        msg = client._format_http_error(error)
        assert "HTTP 418" in msg

    def test_error_with_error_object(self):
        client = TripItAPIClient("key", "secret")
        error = self._make_error(400, json_body={"Error": {"description": "Invalid date format"}})
        msg = client._format_http_error(error)
        assert "Invalid date format" in msg

    def test_error_with_error_list(self):
        client = TripItAPIClient("key", "secret")
        error = self._make_error(400, json_body={
            "Error": [{"description": "Error 1"}, {"description": "Error 2"}]
        })
        msg = client._format_http_error(error)
        assert "Error 1" in msg
        assert "Error 2" in msg

    def test_error_with_warning_object(self):
        client = TripItAPIClient("key", "secret")
        error = self._make_error(400, json_body={"Warning": {"description": "Date in past"}})
        msg = client._format_http_error(error)
        assert "Warning" in msg
        assert "Date in past" in msg

    def test_error_with_warning_list(self):
        client = TripItAPIClient("key", "secret")
        error = self._make_error(400, json_body={
            "Warning": [{"description": "Warn 1"}, {"description": "Warn 2"}]
        })
        msg = client._format_http_error(error)
        assert "Warn 1" in msg
        assert "Warn 2" in msg

    def test_error_fallback_to_text(self):
        client = TripItAPIClient("key", "secret")
        error = self._make_error(500, text="Internal Server Error")
        msg = client._format_http_error(error)
        assert "Internal Server Error" in msg


class TestOAuthSignature:
    def test_generate_nonce_length(self):
        client = TripItAPIClient("key", "secret")
        nonce = client._generate_nonce(32)
        assert len(nonce) == 32

    def test_generate_oauth_signature(self):
        client = TripItAPIClient("consumer_key", "consumer_secret")
        sig = client._generate_oauth_signature(
            "GET", "https://api.tripit.com/v1/list/trip",
            {"oauth_consumer_key": "consumer_key", "format": "json"},
            token_secret="",
        )
        # Should return a base64-encoded string
        assert isinstance(sig, str)
        assert len(sig) > 0

    def test_prepare_oauth_params_with_token(self):
        client = TripItAPIClient("key", "secret", "token", "token_secret")
        params = client._prepare_oauth_params("GET", "https://api.tripit.com/v1/list/trip")
        assert params["oauth_consumer_key"] == "key"
        assert params["oauth_token"] == "token"
        assert "oauth_signature" in params

    def test_prepare_oauth_params_without_token(self):
        client = TripItAPIClient("key", "secret")
        params = client._prepare_oauth_params("GET", "https://api.tripit.com/v1/list/trip")
        assert params["oauth_consumer_key"] == "key"
        assert "oauth_token" not in params
        assert "oauth_signature" in params

    def test_build_authorization_header(self):
        client = TripItAPIClient("key", "secret")
        header = client._build_authorization_header({
            "oauth_consumer_key": "key",
            "oauth_nonce": "abc123",
        })
        assert header.startswith("OAuth ")
        assert "oauth_consumer_key" in header
        assert "oauth_nonce" in header


class TestGetObjectFallback:
    def test_get_unknown_type_fallback(self):
        """When object type isn't in type_map, return full response."""
        with patch.object(TripItAPIClient, "_make_request") as mock_request:
            mock_request.return_value = {
                "SomeNewObject": {"id": "999"},
                "timestamp": "123",
                "num_bytes": "456",
            }
            client = TripItAPIClient("key", "secret")
            result = client.get_object("somenew", "999")
            # timestamp and num_bytes should be stripped
            assert "timestamp" not in result
            assert "num_bytes" not in result
            assert "SomeNewObject" in result


# ── Server Tool Function Tests ───────────────────────────────────────


@pytest.fixture
def mock_service():
    """Mock _get_service() to return a service with a mocked client."""
    mock_client = MagicMock()
    mock_svc = MagicMock()
    mock_svc.client = mock_client
    with patch("tripit_mcp.server._get_service", return_value=mock_svc):
        yield mock_client


def _run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.mark.skipif(not _server_import_ok, reason="FastMCP server import unavailable")
class TestToolListTrips:
    def test_list_trips_success(self, mock_service):
        from tripit_mcp.server import tripit_list_trips
        mock_service.list_trips.return_value = {
            "trips": [
                {"id": "1", "display_name": "NYC", "start_date": "2026-06-01",
                 "end_date": "2026-06-07", "primary_location": "New York", "is_private": "false"}
            ],
            "pagination": {"page_num": 1, "page_size": 5, "max_page": 1},
        }
        result = _run(tripit_list_trips(past=False))
        assert len(result["trips"]) == 1
        assert result["trips"][0]["name"] == "NYC"
        assert result["trips"][0]["is_private"] is False

    def test_list_trips_with_warnings(self, mock_service):
        from tripit_mcp.server import tripit_list_trips
        mock_service.list_trips.return_value = {
            "trips": [],
            "pagination": {"page_num": 1, "page_size": 5, "max_page": 1},
            "warnings": ["Some warning"],
        }
        result = _run(tripit_list_trips())
        assert result["warnings"] == ["Some warning"]

    def test_list_trips_api_error(self, mock_service):
        from tripit_mcp.server import tripit_list_trips
        mock_service.list_trips.side_effect = TripItAPIError("API down")
        result = _run(tripit_list_trips())
        assert result["error"] == "API down"


@pytest.mark.skipif(not _server_import_ok, reason="FastMCP server import unavailable")
class TestToolGetTrip:
    def test_get_trip_success(self, mock_service):
        from tripit_mcp.server import tripit_get_trip
        mock_service.get_trip.return_value = {"id": "1", "display_name": "Trip"}
        result = _run(tripit_get_trip(trip_id="1"))
        assert result["trip"]["id"] == "1"

    def test_get_trip_error(self, mock_service):
        from tripit_mcp.server import tripit_get_trip
        mock_service.get_trip.side_effect = TripItAPIError("Not found")
        result = _run(tripit_get_trip(trip_id="999"))
        assert "error" in result


@pytest.mark.skipif(not _server_import_ok, reason="FastMCP server import unavailable")
class TestToolListObjects:
    def test_list_objects_success(self, mock_service):
        from tripit_mcp.server import tripit_list_objects
        mock_service.list_objects.return_value = {
            "objects": {"AirObject": [{"id": "1"}]},
            "pagination": {"page_num": 1, "page_size": 10, "max_page": 1},
        }
        result = _run(tripit_list_objects(trip_id="1"))
        assert "AirObject" in result["objects"]

    def test_list_objects_error(self, mock_service):
        from tripit_mcp.server import tripit_list_objects
        mock_service.list_objects.side_effect = TripItAPIError("Fail")
        result = _run(tripit_list_objects(trip_id="1"))
        assert "error" in result


@pytest.mark.skipif(not _server_import_ok, reason="FastMCP server import unavailable")
class TestToolGetObject:
    def test_get_object_success(self, mock_service):
        from tripit_mcp.server import tripit_get_object
        mock_service.get_object.return_value = {"id": "111", "Segment": []}
        result = _run(tripit_get_object(object_type="air", object_id="111"))
        assert result["object"]["id"] == "111"

    def test_get_object_error(self, mock_service):
        from tripit_mcp.server import tripit_get_object
        mock_service.get_object.side_effect = TripItAPIError("Not found")
        result = _run(tripit_get_object(object_type="air", object_id="999"))
        assert "error" in result


@pytest.mark.skipif(not _server_import_ok, reason="FastMCP server import unavailable")
class TestToolGetProfile:
    def test_get_profile_success(self, mock_service):
        from tripit_mcp.server import tripit_get_profile
        mock_service.get_profile.return_value = {"screen_name": "user1"}
        result = _run(tripit_get_profile())
        assert result["profile"]["screen_name"] == "user1"

    def test_get_profile_error(self, mock_service):
        from tripit_mcp.server import tripit_get_profile
        mock_service.get_profile.side_effect = TripItAPIError("Auth error")
        result = _run(tripit_get_profile())
        assert "error" in result


@pytest.mark.skipif(not _server_import_ok, reason="FastMCP server import unavailable")
class TestToolCreateTrip:
    def test_create_trip_success(self, mock_service):
        from tripit_mcp.server import tripit_create_trip
        mock_service.create.return_value = {
            "Trip": {"id": "999", "display_name": "New Trip"}
        }
        result = _run(tripit_create_trip(
            primary_location="New York",
            start_date="2026-06-01",
            end_date="2026-06-07",
        ))
        assert result["trip"]["id"] == "999"
        # Verify create was called with correct Trip data
        call_data = mock_service.create.call_args[0][0]
        assert call_data["Trip"]["primary_location"] == "New York"
        assert call_data["Trip"]["is_private"] == "false"

    def test_create_trip_with_display_name(self, mock_service):
        from tripit_mcp.server import tripit_create_trip
        mock_service.create.return_value = {"Trip": {"id": "999"}}
        result = _run(tripit_create_trip(
            primary_location="Paris",
            start_date="2026-07-01",
            end_date="2026-07-10",
            display_name="Paris Vacation",
            is_private=True,
        ))
        call_data = mock_service.create.call_args[0][0]
        assert call_data["Trip"]["display_name"] == "Paris Vacation"
        assert call_data["Trip"]["is_private"] == "true"

    def test_create_trip_api_error(self, mock_service):
        from tripit_mcp.server import tripit_create_trip
        mock_service.create.side_effect = TripItAPIError("Create failed")
        result = _run(tripit_create_trip(
            primary_location="Nowhere",
            start_date="2026-06-01",
            end_date="2026-06-07",
        ))
        assert result["error"] == "Create failed"

    def test_create_trip_validation_error(self, mock_service):
        from tripit_mcp.server import tripit_create_trip
        result = _run(tripit_create_trip(
            primary_location="NYC",
            start_date="bad-date",
            end_date="2026-06-07",
        ))
        assert "error" in result


@pytest.mark.skipif(not _server_import_ok, reason="FastMCP server import unavailable")
class TestToolUpdateTrip:
    def test_update_trip_success(self, mock_service):
        from tripit_mcp.server import tripit_update_trip
        mock_service.replace.return_value = {
            "Trip": {"id": "1", "display_name": "Updated"}
        }
        result = _run(tripit_update_trip(trip_id="1", display_name="Updated"))
        assert result["trip"]["display_name"] == "Updated"

    def test_update_trip_no_fields(self, mock_service):
        from tripit_mcp.server import tripit_update_trip
        result = _run(tripit_update_trip(trip_id="1"))
        assert "error" in result
        assert "No fields" in result["error"]

    def test_update_trip_api_error(self, mock_service):
        from tripit_mcp.server import tripit_update_trip
        mock_service.replace.side_effect = TripItAPIError("Update failed")
        result = _run(tripit_update_trip(trip_id="1", display_name="X"))
        assert "error" in result


@pytest.mark.skipif(not _server_import_ok, reason="FastMCP server import unavailable")
class TestToolDeleteTrip:
    def test_delete_trip_success(self, mock_service):
        from tripit_mcp.server import tripit_delete_trip
        mock_service.delete.return_value = {"timestamp": "123"}
        result = _run(tripit_delete_trip(trip_id="1"))
        assert result["success"] is True
        assert "1" in result["message"]

    def test_delete_trip_error(self, mock_service):
        from tripit_mcp.server import tripit_delete_trip
        mock_service.delete.side_effect = TripItAPIError("Delete failed")
        result = _run(tripit_delete_trip(trip_id="1"))
        assert "error" in result


@pytest.mark.skipif(not _server_import_ok, reason="FastMCP server import unavailable")
class TestToolCreateFlight:
    def test_create_flight_single_segment(self, mock_service):
        from tripit_mcp.server import tripit_create_flight
        mock_service.create.return_value = {"AirObject": {"id": "111"}}
        result = _run(tripit_create_flight(
            trip_id="1",
            segments=[{"start_date": "2026-06-01", "start_airport_code": "SFO", "end_airport_code": "JFK"}],
            supplier_name="United",
            supplier_conf_num="ABC123",
        ))
        assert result["flight"]["id"] == "111"
        call_data = mock_service.create.call_args[0][0]
        assert call_data["AirObject"]["trip_id"] == "1"
        assert call_data["AirObject"]["supplier_name"] == "United"
        # Single segment should NOT be wrapped in a list
        assert isinstance(call_data["AirObject"]["Segment"], dict)

    def test_create_flight_multi_segment(self, mock_service):
        from tripit_mcp.server import tripit_create_flight
        mock_service.create.return_value = {"AirObject": {"id": "111"}}
        result = _run(tripit_create_flight(
            trip_id="1",
            segments=[
                {"start_date": "2026-06-01", "start_time": "08:00", "start_airport_code": "SFO", "end_airport_code": "ORD"},
                {"start_date": "2026-06-01", "start_time": "14:00", "start_airport_code": "ORD", "end_airport_code": "JFK"},
            ],
        ))
        call_data = mock_service.create.call_args[0][0]
        # Multi-segment should be a list
        assert isinstance(call_data["AirObject"]["Segment"], list)
        assert len(call_data["AirObject"]["Segment"]) == 2

    def test_create_flight_segment_datetime_mapping(self, mock_service):
        from tripit_mcp.server import tripit_create_flight
        mock_service.create.return_value = {"AirObject": {"id": "111"}}
        _run(tripit_create_flight(
            trip_id="1",
            segments=[{
                "start_date": "2026-06-01", "start_time": "08:00",
                "end_date": "2026-06-01", "end_time": "11:30",
                "start_airport_code": "SFO",
            }],
        ))
        seg = mock_service.create.call_args[0][0]["AirObject"]["Segment"]
        assert seg["StartDateTime"] == {"date": "2026-06-01", "time": "08:00"}
        assert seg["EndDateTime"] == {"date": "2026-06-01", "time": "11:30"}
        assert seg["start_airport_code"] == "SFO"

    def test_create_flight_error(self, mock_service):
        from tripit_mcp.server import tripit_create_flight
        mock_service.create.side_effect = TripItAPIError("Create failed")
        result = _run(tripit_create_flight(trip_id="1", segments=[{"start_date": "2026-06-01"}]))
        assert "error" in result


@pytest.mark.skipif(not _server_import_ok, reason="FastMCP server import unavailable")
class TestToolCreateLodging:
    def test_create_lodging_success(self, mock_service):
        from tripit_mcp.server import tripit_create_lodging
        mock_service.create.return_value = {"LodgingObject": {"id": "222"}}
        result = _run(tripit_create_lodging(
            trip_id="1",
            start_date="2026-06-01",
            end_date="2026-06-05",
            supplier_name="Hilton",
            address="123 Main St",
            city="New York",
            state="NY",
            country="US",
            room_type="King Suite",
            number_guests=2,
        ))
        assert result["lodging"]["id"] == "222"
        call_data = mock_service.create.call_args[0][0]
        assert call_data["LodgingObject"]["supplier_name"] == "Hilton"
        assert call_data["LodgingObject"]["Address"]["city"] == "New York"
        assert call_data["LodgingObject"]["number_guests"] == 2

    def test_create_lodging_with_times(self, mock_service):
        from tripit_mcp.server import tripit_create_lodging
        mock_service.create.return_value = {"LodgingObject": {"id": "222"}}
        _run(tripit_create_lodging(
            trip_id="1", start_date="2026-06-01", end_date="2026-06-05",
            start_time="15:00", end_time="11:00",
        ))
        call_data = mock_service.create.call_args[0][0]
        assert call_data["LodgingObject"]["StartDateTime"]["time"] == "15:00"
        assert call_data["LodgingObject"]["EndDateTime"]["time"] == "11:00"


@pytest.mark.skipif(not _server_import_ok, reason="FastMCP server import unavailable")
class TestToolCreateCarRental:
    def test_create_car_rental_success(self, mock_service):
        from tripit_mcp.server import tripit_create_car_rental
        mock_service.create.return_value = {"CarObject": {"id": "333"}}
        result = _run(tripit_create_car_rental(
            trip_id="1",
            start_date="2026-06-01",
            end_date="2026-06-05",
            supplier_name="Hertz",
            car_type="SUV",
            start_location_name="JFK Airport",
            end_location_name="JFK Airport",
        ))
        assert result["car_rental"]["id"] == "333"
        call_data = mock_service.create.call_args[0][0]
        assert call_data["CarObject"]["start_location_name"] == "JFK Airport"


@pytest.mark.skipif(not _server_import_ok, reason="FastMCP server import unavailable")
class TestToolCreateActivity:
    def test_create_activity_success(self, mock_service):
        from tripit_mcp.server import tripit_create_activity
        mock_service.create.return_value = {"ActivityObject": {"id": "444"}}
        result = _run(tripit_create_activity(
            trip_id="1",
            display_name="City Tour",
            start_date="2026-06-02",
            start_time="09:00",
            end_date="2026-06-02",
            end_time="12:00",
            address="Times Square",
            city="New York",
        ))
        assert result["activity"]["id"] == "444"
        call_data = mock_service.create.call_args[0][0]
        assert call_data["ActivityObject"]["display_name"] == "City Tour"
        assert call_data["ActivityObject"]["EndDateTime"] == {"date": "2026-06-02", "time": "12:00"}
        assert call_data["ActivityObject"]["Address"]["address"] == "Times Square"


@pytest.mark.skipif(not _server_import_ok, reason="FastMCP server import unavailable")
class TestToolCreateRestaurant:
    def test_create_restaurant_success(self, mock_service):
        from tripit_mcp.server import tripit_create_restaurant
        mock_service.create.return_value = {"RestaurantObject": {"id": "555"}}
        result = _run(tripit_create_restaurant(
            trip_id="1",
            display_name="Le Bernardin",
            date="2026-06-03",
            time="19:30",
            cuisine="French",
            number_patrons=4,
            address="155 W 51st St",
            city="New York",
        ))
        assert result["restaurant"]["id"] == "555"
        call_data = mock_service.create.call_args[0][0]
        assert call_data["RestaurantObject"]["DateTime"]["time"] == "19:30"
        assert call_data["RestaurantObject"]["cuisine"] == "French"
        assert call_data["RestaurantObject"]["number_patrons"] == 4


@pytest.mark.skipif(not _server_import_ok, reason="FastMCP server import unavailable")
class TestToolCreateTransport:
    def test_create_transport_success(self, mock_service):
        from tripit_mcp.server import tripit_create_transport
        mock_service.create.return_value = {"TransportObject": {"id": "666"}}
        result = _run(tripit_create_transport(
            trip_id="1",
            start_date="2026-06-01",
            start_time="10:00",
            end_date="2026-06-01",
            end_time="11:00",
            start_location_name="Hotel",
            end_location_name="Airport",
        ))
        assert result["transport"]["id"] == "666"
        call_data = mock_service.create.call_args[0][0]
        assert call_data["TransportObject"]["start_location_name"] == "Hotel"
        assert call_data["TransportObject"]["EndDateTime"] == {"date": "2026-06-01", "time": "11:00"}


@pytest.mark.skipif(not _server_import_ok, reason="FastMCP server import unavailable")
class TestToolCreateRail:
    def test_create_rail_single_segment(self, mock_service):
        from tripit_mcp.server import tripit_create_rail
        mock_service.create.return_value = {"RailObject": {"id": "777"}}
        result = _run(tripit_create_rail(
            trip_id="1",
            segments=[{
                "start_date": "2026-06-02", "start_time": "07:00",
                "start_station_name": "Penn Station", "end_station_name": "Union Station",
                "carrier_name": "Amtrak", "train_number": "171",
            }],
            supplier_name="Amtrak",
        ))
        assert result["rail"]["id"] == "777"
        call_data = mock_service.create.call_args[0][0]
        seg = call_data["RailObject"]["Segment"]
        assert isinstance(seg, dict)  # single segment
        assert seg["carrier_name"] == "Amtrak"
        assert seg["StartDateTime"]["date"] == "2026-06-02"

    def test_create_rail_multi_segment(self, mock_service):
        from tripit_mcp.server import tripit_create_rail
        mock_service.create.return_value = {"RailObject": {"id": "777"}}
        _run(tripit_create_rail(
            trip_id="1",
            segments=[
                {"start_date": "2026-06-02"},
                {"start_date": "2026-06-03"},
            ],
        ))
        call_data = mock_service.create.call_args[0][0]
        assert isinstance(call_data["RailObject"]["Segment"], list)


@pytest.mark.skipif(not _server_import_ok, reason="FastMCP server import unavailable")
class TestToolCreateNote:
    def test_create_note_success(self, mock_service):
        from tripit_mcp.server import tripit_create_note
        mock_service.create.return_value = {"NoteObject": {"id": "888"}}
        result = _run(tripit_create_note(
            trip_id="1",
            display_name="Packing List",
            text="Sunscreen, hat",
            date="2026-06-01",
            url="https://example.com",
        ))
        assert result["note"]["id"] == "888"
        call_data = mock_service.create.call_args[0][0]
        assert call_data["NoteObject"]["DateTime"]["date"] == "2026-06-01"
        assert call_data["NoteObject"]["text"] == "Sunscreen, hat"
        assert call_data["NoteObject"]["url"] == "https://example.com"

    def test_create_note_minimal(self, mock_service):
        from tripit_mcp.server import tripit_create_note
        mock_service.create.return_value = {"NoteObject": {"id": "888"}}
        result = _run(tripit_create_note(trip_id="1", display_name="Note"))
        call_data = mock_service.create.call_args[0][0]
        assert "DateTime" not in call_data["NoteObject"]


@pytest.mark.skipif(not _server_import_ok, reason="FastMCP server import unavailable")
class TestToolDeleteObject:
    def test_delete_object_success(self, mock_service):
        from tripit_mcp.server import tripit_delete_object
        mock_service.delete.return_value = {"timestamp": "123"}
        result = _run(tripit_delete_object(object_type="air", object_id="111"))
        assert result["success"] is True
        assert "air" in result["message"]
        mock_service.delete.assert_called_once_with("air", "111")

    def test_delete_object_error(self, mock_service):
        from tripit_mcp.server import tripit_delete_object
        mock_service.delete.side_effect = TripItAPIError("Not found")
        result = _run(tripit_delete_object(object_type="air", object_id="999"))
        assert "error" in result


@pytest.mark.skipif(not _server_import_ok, reason="FastMCP server import unavailable")
class TestSetOptionalHelper:
    def test_set_optional_copies_non_none(self):
        from tripit_mcp.server import _set_optional
        target = {}

        class FakeInput:
            name = "Test"
            value = None
            count = 5

        _set_optional(target, FakeInput(), ["name", "value", "count"])
        assert target["name"] == "Test"
        assert "value" not in target
        assert target["count"] == 5

    def test_set_optional_handles_bool(self):
        from tripit_mcp.server import _set_optional
        target = {}

        class FakeInput:
            flag = True

        _set_optional(target, FakeInput(), ["flag"])
        assert target["flag"] == "true"


@pytest.mark.skipif(not _server_import_ok, reason="FastMCP server import unavailable")
class TestGetServiceLazy:
    def test_lazy_init(self, mock_env_vars):
        import tripit_mcp.server as srv
        # Reset the singleton
        srv._tripit_service = None
        with patch.object(srv, "TripItAPIClient"):
            svc = srv._get_service()
            assert svc is not None
            # Second call returns same instance
            assert srv._get_service() is svc
        srv._tripit_service = None  # cleanup
