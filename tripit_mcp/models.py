"""
Pydantic models for TripIt MCP server tool inputs.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Trip models ──────────────────────────────────────────────────────


class ListTripsInput(BaseModel):
    """Input for listing trips."""

    model_config = ConfigDict(str_strip_whitespace=True)

    past: bool = Field(default=False, description="If true, return past trips. If false, return current and future trips.")
    traveler: Optional[str] = Field(default=None, description="Filter by traveler: 'true' (only yours), 'false' (not yours), or 'all'.")
    include_objects: bool = Field(default=False, description="If true, include all travel objects (flights, hotels, etc.) within each trip.")
    page_num: Optional[int] = Field(default=None, description="Page number for pagination (1-based).", ge=1)
    page_size: Optional[int] = Field(default=None, description="Number of trips per page.", ge=1, le=25)


class GetTripInput(BaseModel):
    """Input for getting a single trip."""

    model_config = ConfigDict(str_strip_whitespace=True)

    trip_id: str = Field(..., description="The TripIt trip ID.", min_length=1)
    include_objects: bool = Field(default=True, description="If true, include all travel objects within the trip.")


class CreateTripInput(BaseModel):
    """Input for creating a new trip."""

    model_config = ConfigDict(str_strip_whitespace=True)

    primary_location: str = Field(..., description="Primary destination (e.g., 'New York, NY').", min_length=1)
    start_date: str = Field(..., description="Trip start date in YYYY-MM-DD format.", pattern=r'^\d{4}-\d{2}-\d{2}$')
    end_date: str = Field(..., description="Trip end date in YYYY-MM-DD format.", pattern=r'^\d{4}-\d{2}-\d{2}$')
    display_name: Optional[str] = Field(default=None, description="Custom display name for the trip.")
    is_private: bool = Field(default=False, description="Whether the trip is private.")


class UpdateTripInput(BaseModel):
    """Input for updating an existing trip."""

    model_config = ConfigDict(str_strip_whitespace=True)

    trip_id: str = Field(..., description="The TripIt trip ID to update.", min_length=1)
    primary_location: Optional[str] = Field(default=None, description="Primary destination.")
    start_date: Optional[str] = Field(default=None, description="Trip start date in YYYY-MM-DD format.", pattern=r'^\d{4}-\d{2}-\d{2}$')
    end_date: Optional[str] = Field(default=None, description="Trip end date in YYYY-MM-DD format.", pattern=r'^\d{4}-\d{2}-\d{2}$')
    display_name: Optional[str] = Field(default=None, description="Custom display name for the trip.")
    is_private: Optional[bool] = Field(default=None, description="Whether the trip is private.")


class DeleteTripInput(BaseModel):
    """Input for deleting a trip."""

    model_config = ConfigDict(str_strip_whitespace=True)

    trip_id: str = Field(..., description="The TripIt trip ID to delete.", min_length=1)


# ── Object list/get models ───────────────────────────────────────────


OBJECT_TYPE_DESCRIPTION = (
    "Object type: 'air' (flights), 'lodging' (hotels), 'car' (car rentals), "
    "'activity', 'restaurant', 'transport' (ground transport), 'rail' (trains), or 'note'."
)


class ListObjectsInput(BaseModel):
    """Input for listing travel objects within a trip."""

    model_config = ConfigDict(str_strip_whitespace=True)

    trip_id: str = Field(..., description="The trip ID to list objects for.", min_length=1)
    object_type: Optional[str] = Field(default=None, description=OBJECT_TYPE_DESCRIPTION)
    page_num: Optional[int] = Field(default=None, description="Page number for pagination (1-based).", ge=1)
    page_size: Optional[int] = Field(default=None, description="Number of items per page.", ge=1, le=25)


class GetObjectInput(BaseModel):
    """Input for getting a specific travel object."""

    model_config = ConfigDict(str_strip_whitespace=True)

    object_type: str = Field(..., description=OBJECT_TYPE_DESCRIPTION, min_length=1)
    object_id: str = Field(..., description="The object ID.", min_length=1)


class DeleteObjectInput(BaseModel):
    """Input for deleting any travel object."""

    model_config = ConfigDict(str_strip_whitespace=True)

    object_type: str = Field(..., description=OBJECT_TYPE_DESCRIPTION, min_length=1)
    object_id: str = Field(..., description="The object ID to delete.", min_length=1)


# ── Flight (Air) models ─────────────────────────────────────────────


class FlightSegmentInput(BaseModel):
    """A single flight segment."""

    model_config = ConfigDict(str_strip_whitespace=True)

    start_date: str = Field(..., description="Departure date in YYYY-MM-DD format.", pattern=r'^\d{4}-\d{2}-\d{2}$')
    start_time: Optional[str] = Field(default=None, description="Departure time in HH:MM:SS format (24-hour).", pattern=r'^\d{2}:\d{2}(:\d{2})?$')
    end_date: Optional[str] = Field(default=None, description="Arrival date in YYYY-MM-DD format.", pattern=r'^\d{4}-\d{2}-\d{2}$')
    end_time: Optional[str] = Field(default=None, description="Arrival time in HH:MM:SS format (24-hour).", pattern=r'^\d{2}:\d{2}(:\d{2})?$')
    start_airport_code: Optional[str] = Field(default=None, description="IATA departure airport code (e.g., 'SFO').", max_length=4)
    start_city_name: Optional[str] = Field(default=None, description="Departure city name.")
    end_airport_code: Optional[str] = Field(default=None, description="IATA arrival airport code (e.g., 'JFK').", max_length=4)
    end_city_name: Optional[str] = Field(default=None, description="Arrival city name.")
    marketing_airline: Optional[str] = Field(default=None, description="Airline name or code (e.g., 'United Airlines' or 'UA').")
    marketing_flight_number: Optional[str] = Field(default=None, description="Flight number (e.g., '137').")
    operating_airline: Optional[str] = Field(default=None, description="Operating airline if different from marketing airline.")
    operating_flight_number: Optional[str] = Field(default=None, description="Operating flight number.")
    aircraft: Optional[str] = Field(default=None, description="Aircraft type (e.g., 'Boeing 737-800').")
    seats: Optional[str] = Field(default=None, description="Seat assignment (e.g., '23A').")
    service_class: Optional[str] = Field(default=None, description="Service class (e.g., 'Economy', 'Business', 'First').")
    meal: Optional[str] = Field(default=None, description="Meal description.")
    notes: Optional[str] = Field(default=None, description="Additional notes for this segment.")


class CreateFlightInput(BaseModel):
    """Input for creating a flight (AirObject)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    trip_id: str = Field(..., description="The trip ID to add this flight to.", min_length=1)
    segments: List[FlightSegmentInput] = Field(..., description="One or more flight segments.", min_length=1)
    booking_site_name: Optional[str] = Field(default=None, description="Booking site name (e.g., 'Expedia').")
    booking_site_conf_num: Optional[str] = Field(default=None, description="Booking confirmation number.")
    supplier_name: Optional[str] = Field(default=None, description="Airline supplier name.")
    supplier_conf_num: Optional[str] = Field(default=None, description="Airline confirmation number.")
    notes: Optional[str] = Field(default=None, description="General notes about this flight.")


# ── Lodging models ───────────────────────────────────────────────────


class CreateLodgingInput(BaseModel):
    """Input for creating a hotel/lodging reservation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    trip_id: str = Field(..., description="The trip ID to add this lodging to.", min_length=1)
    supplier_name: Optional[str] = Field(default=None, description="Hotel or property name.")
    start_date: str = Field(..., description="Check-in date in YYYY-MM-DD format.", pattern=r'^\d{4}-\d{2}-\d{2}$')
    end_date: str = Field(..., description="Check-out date in YYYY-MM-DD format.", pattern=r'^\d{4}-\d{2}-\d{2}$')
    start_time: Optional[str] = Field(default=None, description="Check-in time in HH:MM:SS format.", pattern=r'^\d{2}:\d{2}(:\d{2})?$')
    end_time: Optional[str] = Field(default=None, description="Check-out time in HH:MM:SS format.", pattern=r'^\d{2}:\d{2}(:\d{2})?$')
    address: Optional[str] = Field(default=None, description="Hotel address.")
    city: Optional[str] = Field(default=None, description="Hotel city.")
    state: Optional[str] = Field(default=None, description="Hotel state/province.")
    country: Optional[str] = Field(default=None, description="Hotel country.")
    room_type: Optional[str] = Field(default=None, description="Room type (e.g., 'King Suite').")
    number_guests: Optional[int] = Field(default=None, description="Number of guests.", ge=1)
    number_rooms: Optional[int] = Field(default=None, description="Number of rooms.", ge=1)
    booking_site_name: Optional[str] = Field(default=None, description="Booking site name.")
    booking_site_conf_num: Optional[str] = Field(default=None, description="Booking confirmation number.")
    supplier_conf_num: Optional[str] = Field(default=None, description="Hotel confirmation number.")
    supplier_phone: Optional[str] = Field(default=None, description="Hotel phone number.")
    notes: Optional[str] = Field(default=None, description="Additional notes.")


# ── Car rental models ────────────────────────────────────────────────


class CreateCarRentalInput(BaseModel):
    """Input for creating a car rental reservation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    trip_id: str = Field(..., description="The trip ID to add this car rental to.", min_length=1)
    supplier_name: Optional[str] = Field(default=None, description="Car rental company name (e.g., 'Hertz').")
    start_date: str = Field(..., description="Pickup date in YYYY-MM-DD format.", pattern=r'^\d{4}-\d{2}-\d{2}$')
    end_date: str = Field(..., description="Dropoff date in YYYY-MM-DD format.", pattern=r'^\d{4}-\d{2}-\d{2}$')
    start_time: Optional[str] = Field(default=None, description="Pickup time in HH:MM:SS format.", pattern=r'^\d{2}:\d{2}(:\d{2})?$')
    end_time: Optional[str] = Field(default=None, description="Dropoff time in HH:MM:SS format.", pattern=r'^\d{2}:\d{2}(:\d{2})?$')
    start_location_name: Optional[str] = Field(default=None, description="Pickup location name.")
    start_location_address: Optional[str] = Field(default=None, description="Pickup address.")
    end_location_name: Optional[str] = Field(default=None, description="Dropoff location name.")
    end_location_address: Optional[str] = Field(default=None, description="Dropoff address.")
    car_type: Optional[str] = Field(default=None, description="Car type/class (e.g., 'Compact', 'SUV').")
    booking_site_name: Optional[str] = Field(default=None, description="Booking site name.")
    booking_site_conf_num: Optional[str] = Field(default=None, description="Booking confirmation number.")
    supplier_conf_num: Optional[str] = Field(default=None, description="Rental company confirmation number.")
    supplier_phone: Optional[str] = Field(default=None, description="Rental company phone number.")
    notes: Optional[str] = Field(default=None, description="Additional notes.")


# ── Activity models ──────────────────────────────────────────────────


class CreateActivityInput(BaseModel):
    """Input for creating an activity."""

    model_config = ConfigDict(str_strip_whitespace=True)

    trip_id: str = Field(..., description="The trip ID to add this activity to.", min_length=1)
    display_name: str = Field(..., description="Activity name (e.g., 'Guided City Tour').", min_length=1)
    start_date: str = Field(..., description="Activity date in YYYY-MM-DD format.", pattern=r'^\d{4}-\d{2}-\d{2}$')
    start_time: Optional[str] = Field(default=None, description="Start time in HH:MM:SS format.", pattern=r'^\d{2}:\d{2}(:\d{2})?$')
    end_date: Optional[str] = Field(default=None, description="End date in YYYY-MM-DD format.", pattern=r'^\d{4}-\d{2}-\d{2}$')
    end_time: Optional[str] = Field(default=None, description="End time in HH:MM:SS format.", pattern=r'^\d{2}:\d{2}(:\d{2})?$')
    address: Optional[str] = Field(default=None, description="Activity address.")
    city: Optional[str] = Field(default=None, description="City.")
    state: Optional[str] = Field(default=None, description="State/province.")
    country: Optional[str] = Field(default=None, description="Country.")
    booking_site_name: Optional[str] = Field(default=None, description="Booking site name.")
    booking_site_conf_num: Optional[str] = Field(default=None, description="Booking confirmation number.")
    supplier_name: Optional[str] = Field(default=None, description="Activity provider name.")
    supplier_conf_num: Optional[str] = Field(default=None, description="Provider confirmation number.")
    supplier_phone: Optional[str] = Field(default=None, description="Provider phone number.")
    supplier_url: Optional[str] = Field(default=None, description="Provider website URL.")
    notes: Optional[str] = Field(default=None, description="Additional notes.")


# ── Restaurant models ────────────────────────────────────────────────


class CreateRestaurantInput(BaseModel):
    """Input for creating a restaurant reservation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    trip_id: str = Field(..., description="The trip ID to add this reservation to.", min_length=1)
    display_name: str = Field(..., description="Restaurant name.", min_length=1)
    date: str = Field(..., description="Reservation date in YYYY-MM-DD format.", pattern=r'^\d{4}-\d{2}-\d{2}$')
    time: Optional[str] = Field(default=None, description="Reservation time in HH:MM:SS format.", pattern=r'^\d{2}:\d{2}(:\d{2})?$')
    address: Optional[str] = Field(default=None, description="Restaurant address.")
    city: Optional[str] = Field(default=None, description="City.")
    state: Optional[str] = Field(default=None, description="State/province.")
    country: Optional[str] = Field(default=None, description="Country.")
    cuisine: Optional[str] = Field(default=None, description="Cuisine type (e.g., 'Italian', 'Japanese').")
    dress_code: Optional[str] = Field(default=None, description="Dress code.")
    number_patrons: Optional[int] = Field(default=None, description="Number of diners.", ge=1)
    supplier_phone: Optional[str] = Field(default=None, description="Restaurant phone number.")
    supplier_url: Optional[str] = Field(default=None, description="Restaurant website URL.")
    booking_site_conf_num: Optional[str] = Field(default=None, description="Reservation confirmation number.")
    notes: Optional[str] = Field(default=None, description="Additional notes.")


# ── Transport models ─────────────────────────────────────────────────


class CreateTransportInput(BaseModel):
    """Input for creating a ground transport reservation (taxi, shuttle, limo, etc.)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    trip_id: str = Field(..., description="The trip ID to add this transport to.", min_length=1)
    start_date: str = Field(..., description="Pickup date in YYYY-MM-DD format.", pattern=r'^\d{4}-\d{2}-\d{2}$')
    start_time: Optional[str] = Field(default=None, description="Pickup time in HH:MM:SS format.", pattern=r'^\d{2}:\d{2}(:\d{2})?$')
    end_date: Optional[str] = Field(default=None, description="Dropoff date in YYYY-MM-DD format.", pattern=r'^\d{4}-\d{2}-\d{2}$')
    end_time: Optional[str] = Field(default=None, description="Dropoff time in HH:MM:SS format.", pattern=r'^\d{2}:\d{2}(:\d{2})?$')
    start_location_name: Optional[str] = Field(default=None, description="Pickup location name.")
    start_location_address: Optional[str] = Field(default=None, description="Pickup address.")
    end_location_name: Optional[str] = Field(default=None, description="Dropoff location name.")
    end_location_address: Optional[str] = Field(default=None, description="Dropoff address.")
    supplier_name: Optional[str] = Field(default=None, description="Transport company name.")
    supplier_conf_num: Optional[str] = Field(default=None, description="Confirmation number.")
    supplier_phone: Optional[str] = Field(default=None, description="Company phone number.")
    booking_site_name: Optional[str] = Field(default=None, description="Booking site name.")
    booking_site_conf_num: Optional[str] = Field(default=None, description="Booking confirmation number.")
    notes: Optional[str] = Field(default=None, description="Additional notes.")


# ── Rail models ──────────────────────────────────────────────────────


class RailSegmentInput(BaseModel):
    """A single rail/train segment."""

    model_config = ConfigDict(str_strip_whitespace=True)

    start_date: str = Field(..., description="Departure date in YYYY-MM-DD format.", pattern=r'^\d{4}-\d{2}-\d{2}$')
    start_time: Optional[str] = Field(default=None, description="Departure time in HH:MM:SS format.", pattern=r'^\d{2}:\d{2}(:\d{2})?$')
    end_date: Optional[str] = Field(default=None, description="Arrival date in YYYY-MM-DD format.", pattern=r'^\d{4}-\d{2}-\d{2}$')
    end_time: Optional[str] = Field(default=None, description="Arrival time in HH:MM:SS format.", pattern=r'^\d{2}:\d{2}(:\d{2})?$')
    start_station_name: Optional[str] = Field(default=None, description="Departure station name.")
    start_city_name: Optional[str] = Field(default=None, description="Departure city.")
    end_station_name: Optional[str] = Field(default=None, description="Arrival station name.")
    end_city_name: Optional[str] = Field(default=None, description="Arrival city.")
    carrier_name: Optional[str] = Field(default=None, description="Rail carrier name (e.g., 'Amtrak').")
    train_number: Optional[str] = Field(default=None, description="Train number.")
    service_class: Optional[str] = Field(default=None, description="Service class (e.g., 'First Class', 'Business').")
    seats: Optional[str] = Field(default=None, description="Seat assignment.")
    coach_number: Optional[str] = Field(default=None, description="Coach/car number.")
    notes: Optional[str] = Field(default=None, description="Additional notes for this segment.")


class CreateRailInput(BaseModel):
    """Input for creating a rail/train reservation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    trip_id: str = Field(..., description="The trip ID to add this rail journey to.", min_length=1)
    segments: List[RailSegmentInput] = Field(..., description="One or more rail segments.", min_length=1)
    booking_site_name: Optional[str] = Field(default=None, description="Booking site name.")
    booking_site_conf_num: Optional[str] = Field(default=None, description="Booking confirmation number.")
    supplier_name: Optional[str] = Field(default=None, description="Rail operator name.")
    supplier_conf_num: Optional[str] = Field(default=None, description="Operator confirmation number.")
    notes: Optional[str] = Field(default=None, description="General notes about this rail journey.")


# ── Note models ──────────────────────────────────────────────────────


class CreateNoteInput(BaseModel):
    """Input for creating a trip note."""

    model_config = ConfigDict(str_strip_whitespace=True)

    trip_id: str = Field(..., description="The trip ID to add this note to.", min_length=1)
    display_name: str = Field(..., description="Note title.", min_length=1)
    text: Optional[str] = Field(default=None, description="Note text content.")
    date: Optional[str] = Field(default=None, description="Relevant date in YYYY-MM-DD format.", pattern=r'^\d{4}-\d{2}-\d{2}$')
    url: Optional[str] = Field(default=None, description="Related URL.")
    notes: Optional[str] = Field(default=None, description="Additional notes.")
