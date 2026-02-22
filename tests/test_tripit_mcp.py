"""
Tests for the TripIt MCP server functionality.
"""

import json
import os
from unittest.mock import patch, MagicMock

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
