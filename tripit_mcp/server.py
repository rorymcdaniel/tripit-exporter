"""
FastMCP server implementation for TripIt API using FastMCP v2.

Provides comprehensive CRUD access to TripIt trip data, flights, hotels,
car rentals, activities, restaurants, ground transport, trains, and notes.
"""

import json
import os
from typing import Any, Dict, Optional

from fastmcp import FastMCP

from .models import (
    CreateActivityInput,
    CreateCarRentalInput,
    CreateFlightInput,
    CreateLodgingInput,
    CreateNoteInput,
    CreateRailInput,
    CreateRestaurantInput,
    CreateTransportInput,
    CreateTripInput,
    DeleteObjectInput,
    DeleteTripInput,
    GetObjectInput,
    GetTripInput,
    ListObjectsInput,
    ListTripsInput,
    UpdateTripInput,
)
from .tripit_client import TripItAPIClient, TripItAPIError


# Initialize FastMCP application
app = FastMCP(
    name="TripIt MCP Server",
    instructions=(
        "A Model Context Protocol (MCP) server that provides full CRUD access "
        "to TripIt trip data including flights, hotels, car rentals, activities, "
        "restaurants, ground transport, trains, and notes."
    ),
)


class TripItService:
    """Service class for TripIt API operations."""

    def __init__(self):
        """Initialize the TripIt service with credentials from environment."""
        self.consumer_key = os.environ.get("TRIPIT_CONSUMER_KEY", None)
        self.consumer_secret = os.environ.get("TRIPIT_CONSUMER_SECRET", None)
        self.oauth_token = os.environ.get("TRIPIT_OAUTH_TOKEN", None)
        self.oauth_token_secret = os.environ.get("TRIPIT_OAUTH_TOKEN_SECRET", None)

        if not self.consumer_key or not self.consumer_secret:
            raise ValueError(
                "TripIt API credentials not found in environment variables. "
                "Please set TRIPIT_CONSUMER_KEY and TRIPIT_CONSUMER_SECRET."
            )

        self.client = TripItAPIClient(
            self.consumer_key,
            self.consumer_secret,
            self.oauth_token,
            self.oauth_token_secret,
        )


# Lazy-initialized TripIt service (created on first tool call)
_tripit_service: Optional[TripItService] = None


def _get_service() -> TripItService:
    """Get or create the TripIt service singleton."""
    global _tripit_service
    if _tripit_service is None:
        _tripit_service = TripItService()
    return _tripit_service


# ═══════════════════════════════════════════════════════════════════════
# Read Tools
# ═══════════════════════════════════════════════════════════════════════


@app.tool(
    name="tripit_list_trips",
    description="List TripIt trips with optional filters for past/future, traveler, and pagination.",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def tripit_list_trips(
    past: bool = False,
    traveler: Optional[str] = None,
    include_objects: bool = False,
    page_num: Optional[int] = None,
    page_size: Optional[int] = None,
) -> Dict[str, Any]:
    """List TripIt trips with optional filters.

    Returns current/future trips by default. Set past=true for past trips.
    Use traveler filter to see trips by relationship (yours, others, or all).
    """
    try:
        inp = ListTripsInput(
            past=past,
            traveler=traveler,
            include_objects=include_objects,
            page_num=page_num,
            page_size=page_size,
        )
        trips_data = _get_service().client.list_trips(
            past=inp.past,
            include_objects=inp.include_objects,
            traveler=inp.traveler,
            page_num=inp.page_num,
            page_size=inp.page_size,
        )

        formatted_trips = []
        for trip in trips_data["trips"]:
            formatted_trip = {
                "id": trip.get("id"),
                "name": trip.get("display_name"),
                "start_date": trip.get("start_date"),
                "end_date": trip.get("end_date"),
                "primary_location": trip.get("primary_location"),
                "is_private": trip.get("is_private") == "true",
            }
            formatted_trips.append(formatted_trip)

        result: Dict[str, Any] = {
            "trips": formatted_trips,
            "pagination": trips_data["pagination"],
        }
        if trips_data.get("warnings"):
            result["warnings"] = trips_data["warnings"]
        return result

    except TripItAPIError as e:
        return {"error": str(e)}


@app.tool(
    name="tripit_get_trip",
    description="Get full details for a specific TripIt trip by ID.",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def tripit_get_trip(
    trip_id: str,
    include_objects: bool = True,
) -> Dict[str, Any]:
    """Get detailed information for a single trip.

    Returns the full trip data including all travel objects (flights, hotels, etc.)
    when include_objects is true.
    """
    try:
        inp = GetTripInput(trip_id=trip_id, include_objects=include_objects)
        trip = _get_service().client.get_trip(
            trip_id=inp.trip_id,
            include_objects=inp.include_objects,
        )
        return {"trip": trip}
    except (TripItAPIError, ValueError) as e:
        return {"error": str(e)}


@app.tool(
    name="tripit_list_objects",
    description="List travel objects (flights, hotels, etc.) within a trip, optionally filtered by type.",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def tripit_list_objects(
    trip_id: str,
    object_type: Optional[str] = None,
    page_num: Optional[int] = None,
    page_size: Optional[int] = None,
) -> Dict[str, Any]:
    """List travel objects within a trip.

    Returns all objects by default. Use object_type to filter: 'air', 'lodging',
    'car', 'activity', 'restaurant', 'transport', 'rail', or 'note'.
    """
    try:
        inp = ListObjectsInput(
            trip_id=trip_id,
            object_type=object_type,
            page_num=page_num,
            page_size=page_size,
        )
        result = _get_service().client.list_objects(
            trip_id=inp.trip_id,
            object_type=inp.object_type,
            page_num=inp.page_num,
            page_size=inp.page_size,
        )
        return result
    except TripItAPIError as e:
        return {"error": str(e)}


@app.tool(
    name="tripit_get_object",
    description="Get a specific travel object (flight, hotel, etc.) by type and ID.",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def tripit_get_object(
    object_type: str,
    object_id: str,
) -> Dict[str, Any]:
    """Get a specific travel object by its type and ID.

    Supported types: 'air', 'lodging', 'car', 'activity', 'restaurant',
    'transport', 'rail', 'note'.
    """
    try:
        inp = GetObjectInput(object_type=object_type, object_id=object_id)
        obj = _get_service().client.get_object(
            object_type=inp.object_type,
            object_id=inp.object_id,
        )
        return {"object": obj}
    except TripItAPIError as e:
        return {"error": str(e)}


@app.tool(
    name="tripit_get_profile",
    description="Get the authenticated TripIt user's profile information.",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def tripit_get_profile() -> Dict[str, Any]:
    """Get the authenticated user's TripIt profile.

    Returns profile details including name, email, and account information.
    """
    try:
        profile = _get_service().client.get_profile()
        return {"profile": profile}
    except TripItAPIError as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# Write Tools - Trips
# ═══════════════════════════════════════════════════════════════════════


@app.tool(
    name="tripit_create_trip",
    description="Create a new trip on TripIt.",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def tripit_create_trip(
    primary_location: str,
    start_date: str,
    end_date: str,
    display_name: Optional[str] = None,
    is_private: bool = False,
) -> Dict[str, Any]:
    """Create a new trip.

    Provide at minimum a location and start/end dates. Dates must be YYYY-MM-DD format.
    """
    try:
        inp = CreateTripInput(
            primary_location=primary_location,
            start_date=start_date,
            end_date=end_date,
            display_name=display_name,
            is_private=is_private,
        )

        trip_data: Dict[str, Any] = {
            "start_date": inp.start_date,
            "end_date": inp.end_date,
            "primary_location": inp.primary_location,
            "is_private": "true" if inp.is_private else "false",
        }
        if inp.display_name:
            trip_data["display_name"] = inp.display_name

        response = _get_service().client.create({"Trip": trip_data})

        if "Trip" in response:
            return {"trip": response["Trip"]}
        return response

    except (TripItAPIError, ValueError) as e:
        return {"error": str(e)}


@app.tool(
    name="tripit_update_trip",
    description="Update an existing trip on TripIt.",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def tripit_update_trip(
    trip_id: str,
    primary_location: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    display_name: Optional[str] = None,
    is_private: Optional[bool] = None,
) -> Dict[str, Any]:
    """Update an existing trip.

    Only provided fields will be updated. Dates must be YYYY-MM-DD format.
    """
    try:
        inp = UpdateTripInput(
            trip_id=trip_id,
            primary_location=primary_location,
            start_date=start_date,
            end_date=end_date,
            display_name=display_name,
            is_private=is_private,
        )

        trip_data: Dict[str, Any] = {}
        if inp.primary_location is not None:
            trip_data["primary_location"] = inp.primary_location
        if inp.start_date is not None:
            trip_data["start_date"] = inp.start_date
        if inp.end_date is not None:
            trip_data["end_date"] = inp.end_date
        if inp.display_name is not None:
            trip_data["display_name"] = inp.display_name
        if inp.is_private is not None:
            trip_data["is_private"] = "true" if inp.is_private else "false"

        if not trip_data:
            return {"error": "No fields to update. Provide at least one field to change."}

        response = _get_service().client.replace("trip", inp.trip_id, {"Trip": trip_data})

        if "Trip" in response:
            return {"trip": response["Trip"]}
        return response

    except (TripItAPIError, ValueError) as e:
        return {"error": str(e)}


@app.tool(
    name="tripit_delete_trip",
    description="Delete a trip from TripIt. This also deletes all objects within the trip.",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def tripit_delete_trip(trip_id: str) -> Dict[str, Any]:
    """Delete a trip and all its travel objects.

    This is destructive and cannot be undone.
    """
    try:
        inp = DeleteTripInput(trip_id=trip_id)
        response = _get_service().client.delete("trip", inp.trip_id)
        return {"success": True, "message": f"Trip {inp.trip_id} deleted.", "response": response}
    except TripItAPIError as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# Write Tools - Flights
# ═══════════════════════════════════════════════════════════════════════


def _build_segment_data(segment) -> Dict[str, Any]:
    """Build a TripIt Segment dict from a segment input model."""
    seg: Dict[str, Any] = {}
    for field_name in type(segment).model_fields:
        value = getattr(segment, field_name)
        if value is not None:
            # Map field names to TripIt API keys
            if field_name == "start_date":
                seg.setdefault("StartDateTime", {})["date"] = value
            elif field_name == "start_time":
                seg.setdefault("StartDateTime", {})["time"] = value
            elif field_name == "end_date":
                seg.setdefault("EndDateTime", {})["date"] = value
            elif field_name == "end_time":
                seg.setdefault("EndDateTime", {})["time"] = value
            elif field_name == "notes":
                seg["notes"] = value
            else:
                seg[field_name] = value
    return seg


@app.tool(
    name="tripit_create_flight",
    description="Create a flight (air reservation) with one or more segments in a trip.",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def tripit_create_flight(
    trip_id: str,
    segments: list,
    booking_site_name: Optional[str] = None,
    booking_site_conf_num: Optional[str] = None,
    supplier_name: Optional[str] = None,
    supplier_conf_num: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a flight reservation with one or more segments.

    Each segment needs at minimum a start_date. Provide airport codes, airline,
    and flight number for complete flight information. Segments should be provided
    as a list of objects with fields like start_date, start_time, end_date,
    end_time, start_airport_code, end_airport_code, marketing_airline,
    marketing_flight_number, seats, etc.
    """
    try:
        # Validate segments through Pydantic
        inp = CreateFlightInput(
            trip_id=trip_id,
            segments=segments,
            booking_site_name=booking_site_name,
            booking_site_conf_num=booking_site_conf_num,
            supplier_name=supplier_name,
            supplier_conf_num=supplier_conf_num,
            notes=notes,
        )

        segment_data = [_build_segment_data(seg) for seg in inp.segments]

        air_data: Dict[str, Any] = {
            "trip_id": inp.trip_id,
            "Segment": segment_data if len(segment_data) > 1 else segment_data[0],
        }
        if inp.booking_site_name:
            air_data["booking_site_name"] = inp.booking_site_name
        if inp.booking_site_conf_num:
            air_data["booking_site_conf_num"] = inp.booking_site_conf_num
        if inp.supplier_name:
            air_data["supplier_name"] = inp.supplier_name
        if inp.supplier_conf_num:
            air_data["supplier_conf_num"] = inp.supplier_conf_num
        if inp.notes:
            air_data["notes"] = inp.notes

        response = _get_service().client.create({"AirObject": air_data})

        if "AirObject" in response:
            return {"flight": response["AirObject"]}
        return response

    except (TripItAPIError, ValueError) as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# Write Tools - Lodging
# ═══════════════════════════════════════════════════════════════════════


@app.tool(
    name="tripit_create_lodging",
    description="Create a hotel/lodging reservation in a trip.",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def tripit_create_lodging(
    trip_id: str,
    start_date: str,
    end_date: str,
    supplier_name: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    address: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    country: Optional[str] = None,
    room_type: Optional[str] = None,
    number_guests: Optional[int] = None,
    number_rooms: Optional[int] = None,
    booking_site_name: Optional[str] = None,
    booking_site_conf_num: Optional[str] = None,
    supplier_conf_num: Optional[str] = None,
    supplier_phone: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a hotel or lodging reservation.

    Provide check-in and check-out dates (YYYY-MM-DD). Include hotel name,
    address, and confirmation number for complete reservation details.
    """
    try:
        inp = CreateLodgingInput(
            trip_id=trip_id, supplier_name=supplier_name,
            start_date=start_date, end_date=end_date,
            start_time=start_time, end_time=end_time,
            address=address, city=city, state=state, country=country,
            room_type=room_type, number_guests=number_guests, number_rooms=number_rooms,
            booking_site_name=booking_site_name, booking_site_conf_num=booking_site_conf_num,
            supplier_conf_num=supplier_conf_num, supplier_phone=supplier_phone,
            notes=notes,
        )

        lodging_data: Dict[str, Any] = {
            "trip_id": inp.trip_id,
            "StartDateTime": {"date": inp.start_date},
            "EndDateTime": {"date": inp.end_date},
        }
        if inp.start_time:
            lodging_data["StartDateTime"]["time"] = inp.start_time
        if inp.end_time:
            lodging_data["EndDateTime"]["time"] = inp.end_time

        # Address fields
        addr: Dict[str, str] = {}
        if inp.address:
            addr["address"] = inp.address
        if inp.city:
            addr["city"] = inp.city
        if inp.state:
            addr["state"] = inp.state
        if inp.country:
            addr["country"] = inp.country
        if addr:
            lodging_data["Address"] = addr

        _set_optional(lodging_data, inp, [
            "supplier_name", "room_type", "number_guests", "number_rooms",
            "booking_site_name", "booking_site_conf_num",
            "supplier_conf_num", "supplier_phone", "notes",
        ])

        response = _get_service().client.create({"LodgingObject": lodging_data})

        if "LodgingObject" in response:
            return {"lodging": response["LodgingObject"]}
        return response

    except (TripItAPIError, ValueError) as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# Write Tools - Car Rental
# ═══════════════════════════════════════════════════════════════════════


@app.tool(
    name="tripit_create_car_rental",
    description="Create a car rental reservation in a trip.",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def tripit_create_car_rental(
    trip_id: str,
    start_date: str,
    end_date: str,
    supplier_name: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    start_location_name: Optional[str] = None,
    start_location_address: Optional[str] = None,
    end_location_name: Optional[str] = None,
    end_location_address: Optional[str] = None,
    car_type: Optional[str] = None,
    booking_site_name: Optional[str] = None,
    booking_site_conf_num: Optional[str] = None,
    supplier_conf_num: Optional[str] = None,
    supplier_phone: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a car rental reservation.

    Provide pickup and dropoff dates (YYYY-MM-DD). Include rental company,
    location, and confirmation number for complete details.
    """
    try:
        inp = CreateCarRentalInput(
            trip_id=trip_id, supplier_name=supplier_name,
            start_date=start_date, end_date=end_date,
            start_time=start_time, end_time=end_time,
            start_location_name=start_location_name,
            start_location_address=start_location_address,
            end_location_name=end_location_name,
            end_location_address=end_location_address,
            car_type=car_type,
            booking_site_name=booking_site_name, booking_site_conf_num=booking_site_conf_num,
            supplier_conf_num=supplier_conf_num, supplier_phone=supplier_phone,
            notes=notes,
        )

        car_data: Dict[str, Any] = {
            "trip_id": inp.trip_id,
            "StartDateTime": {"date": inp.start_date},
            "EndDateTime": {"date": inp.end_date},
        }
        if inp.start_time:
            car_data["StartDateTime"]["time"] = inp.start_time
        if inp.end_time:
            car_data["EndDateTime"]["time"] = inp.end_time
        if inp.start_location_name:
            car_data["start_location_name"] = inp.start_location_name
        if inp.start_location_address:
            car_data["start_location_address"] = inp.start_location_address
        if inp.end_location_name:
            car_data["end_location_name"] = inp.end_location_name
        if inp.end_location_address:
            car_data["end_location_address"] = inp.end_location_address

        _set_optional(car_data, inp, [
            "supplier_name", "car_type",
            "booking_site_name", "booking_site_conf_num",
            "supplier_conf_num", "supplier_phone", "notes",
        ])

        response = _get_service().client.create({"CarObject": car_data})

        if "CarObject" in response:
            return {"car_rental": response["CarObject"]}
        return response

    except (TripItAPIError, ValueError) as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# Write Tools - Activity
# ═══════════════════════════════════════════════════════════════════════


@app.tool(
    name="tripit_create_activity",
    description="Create an activity (tour, excursion, etc.) in a trip.",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def tripit_create_activity(
    trip_id: str,
    display_name: str,
    start_date: str,
    start_time: Optional[str] = None,
    end_date: Optional[str] = None,
    end_time: Optional[str] = None,
    address: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    country: Optional[str] = None,
    booking_site_name: Optional[str] = None,
    booking_site_conf_num: Optional[str] = None,
    supplier_name: Optional[str] = None,
    supplier_conf_num: Optional[str] = None,
    supplier_phone: Optional[str] = None,
    supplier_url: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Create an activity like a tour, excursion, or event.

    Provide a name and start date at minimum. Include address and provider
    details for complete information.
    """
    try:
        inp = CreateActivityInput(
            trip_id=trip_id, display_name=display_name,
            start_date=start_date, start_time=start_time,
            end_date=end_date, end_time=end_time,
            address=address, city=city, state=state, country=country,
            booking_site_name=booking_site_name, booking_site_conf_num=booking_site_conf_num,
            supplier_name=supplier_name, supplier_conf_num=supplier_conf_num,
            supplier_phone=supplier_phone, supplier_url=supplier_url,
            notes=notes,
        )

        activity_data: Dict[str, Any] = {
            "trip_id": inp.trip_id,
            "display_name": inp.display_name,
            "StartDateTime": {"date": inp.start_date},
        }
        if inp.start_time:
            activity_data["StartDateTime"]["time"] = inp.start_time
        if inp.end_date:
            activity_data["EndDateTime"] = {"date": inp.end_date}
            if inp.end_time:
                activity_data["EndDateTime"]["time"] = inp.end_time

        addr: Dict[str, str] = {}
        if inp.address:
            addr["address"] = inp.address
        if inp.city:
            addr["city"] = inp.city
        if inp.state:
            addr["state"] = inp.state
        if inp.country:
            addr["country"] = inp.country
        if addr:
            activity_data["Address"] = addr

        _set_optional(activity_data, inp, [
            "booking_site_name", "booking_site_conf_num",
            "supplier_name", "supplier_conf_num",
            "supplier_phone", "supplier_url", "notes",
        ])

        response = _get_service().client.create({"ActivityObject": activity_data})

        if "ActivityObject" in response:
            return {"activity": response["ActivityObject"]}
        return response

    except (TripItAPIError, ValueError) as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# Write Tools - Restaurant
# ═══════════════════════════════════════════════════════════════════════


@app.tool(
    name="tripit_create_restaurant",
    description="Create a restaurant reservation in a trip.",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def tripit_create_restaurant(
    trip_id: str,
    display_name: str,
    date: str,
    time: Optional[str] = None,
    address: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    country: Optional[str] = None,
    cuisine: Optional[str] = None,
    dress_code: Optional[str] = None,
    number_patrons: Optional[int] = None,
    supplier_phone: Optional[str] = None,
    supplier_url: Optional[str] = None,
    booking_site_conf_num: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a restaurant reservation.

    Provide the restaurant name and date at minimum.
    """
    try:
        inp = CreateRestaurantInput(
            trip_id=trip_id, display_name=display_name,
            date=date, time=time,
            address=address, city=city, state=state, country=country,
            cuisine=cuisine, dress_code=dress_code,
            number_patrons=number_patrons,
            supplier_phone=supplier_phone, supplier_url=supplier_url,
            booking_site_conf_num=booking_site_conf_num,
            notes=notes,
        )

        rest_data: Dict[str, Any] = {
            "trip_id": inp.trip_id,
            "display_name": inp.display_name,
            "DateTime": {"date": inp.date},
        }
        if inp.time:
            rest_data["DateTime"]["time"] = inp.time

        addr: Dict[str, str] = {}
        if inp.address:
            addr["address"] = inp.address
        if inp.city:
            addr["city"] = inp.city
        if inp.state:
            addr["state"] = inp.state
        if inp.country:
            addr["country"] = inp.country
        if addr:
            rest_data["Address"] = addr

        _set_optional(rest_data, inp, [
            "cuisine", "dress_code", "number_patrons",
            "supplier_phone", "supplier_url",
            "booking_site_conf_num", "notes",
        ])

        response = _get_service().client.create({"RestaurantObject": rest_data})

        if "RestaurantObject" in response:
            return {"restaurant": response["RestaurantObject"]}
        return response

    except (TripItAPIError, ValueError) as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# Write Tools - Ground Transport
# ═══════════════════════════════════════════════════════════════════════


@app.tool(
    name="tripit_create_transport",
    description="Create a ground transport reservation (taxi, shuttle, limo) in a trip.",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def tripit_create_transport(
    trip_id: str,
    start_date: str,
    start_time: Optional[str] = None,
    end_date: Optional[str] = None,
    end_time: Optional[str] = None,
    start_location_name: Optional[str] = None,
    start_location_address: Optional[str] = None,
    end_location_name: Optional[str] = None,
    end_location_address: Optional[str] = None,
    supplier_name: Optional[str] = None,
    supplier_conf_num: Optional[str] = None,
    supplier_phone: Optional[str] = None,
    booking_site_name: Optional[str] = None,
    booking_site_conf_num: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a ground transport reservation (taxi, shuttle, limo, etc.).

    Provide pickup date at minimum.
    """
    try:
        inp = CreateTransportInput(
            trip_id=trip_id,
            start_date=start_date, start_time=start_time,
            end_date=end_date, end_time=end_time,
            start_location_name=start_location_name,
            start_location_address=start_location_address,
            end_location_name=end_location_name,
            end_location_address=end_location_address,
            supplier_name=supplier_name, supplier_conf_num=supplier_conf_num,
            supplier_phone=supplier_phone,
            booking_site_name=booking_site_name, booking_site_conf_num=booking_site_conf_num,
            notes=notes,
        )

        transport_data: Dict[str, Any] = {
            "trip_id": inp.trip_id,
            "StartDateTime": {"date": inp.start_date},
        }
        if inp.start_time:
            transport_data["StartDateTime"]["time"] = inp.start_time
        if inp.end_date:
            transport_data["EndDateTime"] = {"date": inp.end_date}
            if inp.end_time:
                transport_data["EndDateTime"]["time"] = inp.end_time

        _set_optional(transport_data, inp, [
            "start_location_name", "start_location_address",
            "end_location_name", "end_location_address",
            "supplier_name", "supplier_conf_num", "supplier_phone",
            "booking_site_name", "booking_site_conf_num", "notes",
        ])

        response = _get_service().client.create({"TransportObject": transport_data})

        if "TransportObject" in response:
            return {"transport": response["TransportObject"]}
        return response

    except (TripItAPIError, ValueError) as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# Write Tools - Rail
# ═══════════════════════════════════════════════════════════════════════


def _build_rail_segment_data(segment) -> Dict[str, Any]:
    """Build a TripIt rail Segment dict from a RailSegmentInput."""
    seg: Dict[str, Any] = {}
    for field_name in type(segment).model_fields:
        value = getattr(segment, field_name)
        if value is not None:
            if field_name == "start_date":
                seg.setdefault("StartDateTime", {})["date"] = value
            elif field_name == "start_time":
                seg.setdefault("StartDateTime", {})["time"] = value
            elif field_name == "end_date":
                seg.setdefault("EndDateTime", {})["date"] = value
            elif field_name == "end_time":
                seg.setdefault("EndDateTime", {})["time"] = value
            elif field_name == "notes":
                seg["notes"] = value
            else:
                seg[field_name] = value
    return seg


@app.tool(
    name="tripit_create_rail",
    description="Create a rail/train reservation with one or more segments in a trip.",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def tripit_create_rail(
    trip_id: str,
    segments: list,
    booking_site_name: Optional[str] = None,
    booking_site_conf_num: Optional[str] = None,
    supplier_name: Optional[str] = None,
    supplier_conf_num: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a rail/train reservation with one or more segments.

    Each segment needs at minimum a start_date. Provide station names, carrier,
    and train number for complete information. Segments should be provided
    as a list of objects with fields like start_date, start_time, end_date,
    end_time, start_station_name, end_station_name, carrier_name, train_number, etc.
    """
    try:
        inp = CreateRailInput(
            trip_id=trip_id, segments=segments,
            booking_site_name=booking_site_name, booking_site_conf_num=booking_site_conf_num,
            supplier_name=supplier_name, supplier_conf_num=supplier_conf_num,
            notes=notes,
        )

        segment_data = [_build_rail_segment_data(seg) for seg in inp.segments]

        rail_data: Dict[str, Any] = {
            "trip_id": inp.trip_id,
            "Segment": segment_data if len(segment_data) > 1 else segment_data[0],
        }

        _set_optional(rail_data, inp, [
            "booking_site_name", "booking_site_conf_num",
            "supplier_name", "supplier_conf_num", "notes",
        ])

        response = _get_service().client.create({"RailObject": rail_data})

        if "RailObject" in response:
            return {"rail": response["RailObject"]}
        return response

    except (TripItAPIError, ValueError) as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# Write Tools - Note
# ═══════════════════════════════════════════════════════════════════════


@app.tool(
    name="tripit_create_note",
    description="Create a note attached to a trip.",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def tripit_create_note(
    trip_id: str,
    display_name: str,
    text: Optional[str] = None,
    date: Optional[str] = None,
    url: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a note attached to a trip.

    Provide a title (display_name) at minimum. Can include text content,
    a relevant date, or a URL.
    """
    try:
        inp = CreateNoteInput(
            trip_id=trip_id, display_name=display_name,
            text=text, date=date, url=url, notes=notes,
        )

        note_data: Dict[str, Any] = {
            "trip_id": inp.trip_id,
            "display_name": inp.display_name,
        }
        if inp.date:
            note_data["DateTime"] = {"date": inp.date}

        _set_optional(note_data, inp, ["text", "url", "notes"])

        response = _get_service().client.create({"NoteObject": note_data})

        if "NoteObject" in response:
            return {"note": response["NoteObject"]}
        return response

    except (TripItAPIError, ValueError) as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# Write Tools - Generic Delete
# ═══════════════════════════════════════════════════════════════════════


@app.tool(
    name="tripit_delete_object",
    description="Delete any travel object (flight, hotel, car rental, etc.) by type and ID.",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def tripit_delete_object(
    object_type: str,
    object_id: str,
) -> Dict[str, Any]:
    """Delete a travel object.

    Supported types: 'air', 'lodging', 'car', 'activity', 'restaurant',
    'transport', 'rail', 'note'. This is destructive and cannot be undone.
    """
    try:
        inp = DeleteObjectInput(object_type=object_type, object_id=object_id)
        response = _get_service().client.delete(inp.object_type, inp.object_id)
        return {
            "success": True,
            "message": f"{inp.object_type} object {inp.object_id} deleted.",
            "response": response,
        }
    except TripItAPIError as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════


def _set_optional(target: Dict[str, Any], inp, fields: list) -> None:
    """Copy non-None fields from a Pydantic model to a target dict."""
    for field in fields:
        value = getattr(inp, field, None)
        if value is not None:
            target[field] = value if not isinstance(value, bool) else str(value).lower()


# ═══════════════════════════════════════════════════════════════════════
# Server Startup
# ═══════════════════════════════════════════════════════════════════════


def start_server(mode: str = "stdio", host: str = "0.0.0.0", port: int = 8000):
    """
    Start the MCP server in the specified mode.

    Args:
        mode: The server mode - "stdio" (default) or "http"
        host: Host to bind to when using HTTP mode
        port: Port to bind to when using HTTP mode
    """
    import logging
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )

    if mode == "stdio":
        import asyncio

        sys.stderr.write("Starting stdio mode with FastMCP\n")
        asyncio.run(app.run_stdio_async())
    else:
        import uvicorn

        uvicorn.run(
            app,
            host=host,
            port=port,
            log_config={
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "default": {
                        "()": "uvicorn.logging.DefaultFormatter",
                        "fmt": "%(levelprefix)s %(message)s",
                        "use_colors": True,
                    }
                },
                "handlers": {
                    "default": {
                        "formatter": "default",
                        "class": "logging.StreamHandler",
                        "stream": sys.stderr,
                    }
                },
                "loggers": {
                    "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
                    "uvicorn.error": {"level": "INFO"},
                    "uvicorn.access": {"handlers": ["default"], "level": "INFO", "propagate": False},
                },
            },
        )
