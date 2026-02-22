# TripIt MCP Server

A Model Context Protocol (MCP) server that provides full CRUD access to your TripIt trip data through a standardized interface. This server allows AI assistants and other MCP clients to manage your trips, flights, hotels, car rentals, activities, restaurants, ground transport, trains, and notes on TripIt.

## Features

- **Full CRUD access** to TripIt trips and travel objects
- **16 MCP tools** covering trips, flights, hotels, car rentals, activities, restaurants, ground transport, rail, notes, and user profile
- List trips with filters (past/future, traveler, pagination)
- Create, update, and delete trips
- Create and delete travel objects (flights, hotels, car rentals, etc.)
- Get detailed information about any travel object
- OAuth 1.0a authenticated access to the TripIt API
- Pydantic input validation on all tools
- MCP tool annotations (readOnlyHint, destructiveHint, idempotentHint)
- Built using FastMCP for MCP protocol implementation
- Docker and Docker Compose support for easy deployment

## Prerequisites

- Python 3.10+ (for local installation)
- [uv](https://github.com/astral-sh/uv) - Python package manager (for local installation)
- Docker and Docker Compose (for containerized deployment)
- TripIt account with API access (Consumer Key and Secret)
- OAuth token credentials (for authenticated access)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/tripit-mcp.git
cd tripit-mcp
```

### 2. Create and activate a virtual environment using uv

```bash
uv venv
source .venv/bin/activate  # On macOS/Linux
# Or on Windows: .venv\Scripts\activate
```

### 3. Install using uv

```bash
uv pip install -e .
```

This will install the package in development mode with all required dependencies.

## Configuration

### TripIt API Authentication

This server supports both 2-legged and 3-legged OAuth authentication with the TripIt API:

1. **Two-legged OAuth**: Uses only the Consumer Key and Secret (basic access)
2. **Three-legged OAuth**: Uses Consumer Key/Secret and user OAuth tokens (full access)

#### Generating OAuth Tokens

For full access to a user's TripIt account, you'll need to generate OAuth tokens. The package includes several utility scripts to help with this process:

##### Option 1: Using the simplified OAuth script (Recommended)

```bash
# Set your TripIt API credentials as environment variables
export TRIPIT_CONSUMER_KEY=your_consumer_key
export TRIPIT_CONSUMER_SECRET=your_consumer_secret

# Run the script
./get_oauth_tokens.py
```

##### Option 2: Using the built-in OAuth module

```bash
# Using environmental variables for credentials
export TRIPIT_CONSUMER_KEY=your_consumer_key
export TRIPIT_CONSUMER_SECRET=your_consumer_secret
python -m tripit_mcp.oauth

# Or directly within Python
from tripit_mcp.oauth import TripItOAuth
oauth = TripItOAuth(consumer_key, consumer_secret)
access_token, access_token_secret = oauth.authorize_app()
```

Either script will:
1. Get a request token from TripIt
2. Open a browser window asking you to authorize the application
3. After authorization, exchange the request token for access tokens
4. Display the tokens to add to your environment variables
5. Optionally verify the tokens with a test API call

### Environment Variables

Set the following environment variables before running the server:

```bash
# Required
export TRIPIT_CONSUMER_KEY="your_consumer_key"
export TRIPIT_CONSUMER_SECRET="your_consumer_secret"

# Optional - For authenticated access
export TRIPIT_OAUTH_TOKEN="your_oauth_token"
export TRIPIT_OAUTH_TOKEN_SECRET="your_oauth_token_secret"
```

### Getting TripIt API Credentials

1. Register for a developer account at [TripIt for Developers](https://www.tripit.com/developer)
2. Create a new application to get your Consumer Key and Consumer Secret
3. For OAuth tokens, you'll need to implement the OAuth flow or use the TripIt API to generate tokens

## Usage

### Starting the server

#### Option 1: Running directly

The server supports two modes of operation:

##### STDIO Mode (Default)

STDIO mode is perfect for integrating with other tools as a subprocess:

```bash
# Make sure your virtual environment is activated, then run:
python -m tripit_mcp  # Runs in stdio mode by default

# Explicitly specify stdio mode
python -m tripit_mcp --mode stdio
```

In this mode, the server communicates through stdin/stdout using the MCP protocol.

##### HTTP Mode

HTTP mode provides a web server interface to access the MCP functions:

```bash
# Start in HTTP mode with default host/port (0.0.0.0:8000)
python -m tripit_mcp --mode http

# Customize host and port
python -m tripit_mcp --mode http --host 127.0.0.1 --port 8080
```

The server uses FastMCP v2, which provides a modern, asyncio-based implementation of the Model Context Protocol.

#### Option 2: Using Docker Compose (recommended)

1. Copy the example environment file and fill in your TripIt API credentials:
```bash
cp .env.example .env
# Edit .env with your credentials
```

2. Build and start the container (runs in HTTP mode):
```bash
docker-compose up -d
```

3. Check the logs:
```bash
docker-compose logs -f
```

4. Stop the container:
```bash
docker-compose down
```

### MCP Tools

The server provides 16 MCP tools organized into read and write operations. All tool names use the `tripit_` prefix.

#### Read Tools

| Tool | Description |
|------|-------------|
| `tripit_list_trips` | List trips with filters for past/future, traveler, pagination |
| `tripit_get_trip` | Get full details for a specific trip by ID |
| `tripit_list_objects` | List travel objects within a trip, optionally filtered by type |
| `tripit_get_object` | Get a specific travel object by type and ID |
| `tripit_get_profile` | Get the authenticated user's profile |

#### Write Tools — Trips

| Tool | Description |
|------|-------------|
| `tripit_create_trip` | Create a new trip with location, dates, and privacy settings |
| `tripit_update_trip` | Update an existing trip's details |
| `tripit_delete_trip` | Delete a trip and all its travel objects |

#### Write Tools — Travel Objects

| Tool | Description |
|------|-------------|
| `tripit_create_flight` | Create a flight with one or more segments |
| `tripit_create_lodging` | Create a hotel/lodging reservation |
| `tripit_create_car_rental` | Create a car rental reservation |
| `tripit_create_activity` | Create an activity (tour, excursion, event) |
| `tripit_create_restaurant` | Create a restaurant reservation |
| `tripit_create_transport` | Create a ground transport reservation |
| `tripit_create_rail` | Create a rail/train reservation with segments |
| `tripit_create_note` | Create a note attached to a trip |
| `tripit_delete_object` | Delete any travel object by type and ID |

#### Tool Details

##### `tripit_list_trips`

List trips with optional filters.

**Parameters:**
- `past` (bool, default: false) — Return past trips instead of current/future
- `traveler` (string, optional) — Filter: 'true' (yours), 'false' (not yours), 'all'
- `include_objects` (bool, default: false) — Include travel objects within each trip
- `page_num` (int, optional) — Page number (1-based)
- `page_size` (int, optional) — Items per page (1-25)

**Example response:**
```json
{
  "trips": [
    {
      "id": "123456789",
      "name": "Business Trip to New York",
      "start_date": "2026-03-15",
      "end_date": "2026-03-20",
      "primary_location": "New York, NY",
      "is_private": false
    }
  ],
  "pagination": {"page_num": 1, "page_size": 5, "max_page": 1}
}
```

##### `tripit_get_trip`

Get full details for a specific trip.

**Parameters:**
- `trip_id` (string, required) — The TripIt trip ID
- `include_objects` (bool, default: true) — Include travel objects

##### `tripit_list_objects`

List travel objects within a trip.

**Parameters:**
- `trip_id` (string, required) — The trip ID
- `object_type` (string, optional) — Filter by type: 'air', 'lodging', 'car', 'activity', 'restaurant', 'transport', 'rail', 'note'
- `page_num` / `page_size` — Pagination

##### `tripit_create_trip`

Create a new trip.

**Parameters:**
- `primary_location` (string, required) — Destination (e.g., "New York, NY")
- `start_date` (string, required) — Start date (YYYY-MM-DD)
- `end_date` (string, required) — End date (YYYY-MM-DD)
- `display_name` (string, optional) — Custom trip name
- `is_private` (bool, default: false) — Privacy setting

##### `tripit_create_flight`

Create a flight with one or more segments.

**Parameters:**
- `trip_id` (string, required) — Trip to add flight to
- `segments` (list, required) — Flight segments, each with:
  - `start_date` (required), `start_time`, `end_date`, `end_time`
  - `start_airport_code`, `end_airport_code`
  - `marketing_airline`, `marketing_flight_number`
  - `seats`, `service_class`, etc.
- `supplier_name`, `supplier_conf_num` — Airline and confirmation number
- `booking_site_name`, `booking_site_conf_num` — Booking details

##### `tripit_create_lodging`

Create a hotel reservation.

**Parameters:**
- `trip_id`, `start_date`, `end_date` (required)
- `supplier_name` — Hotel name
- `address`, `city`, `state`, `country` — Location
- `room_type`, `number_guests`, `number_rooms`
- `supplier_conf_num`, `booking_site_conf_num`

##### `tripit_delete_object`

Delete any travel object.

**Parameters:**
- `object_type` (string, required) — 'air', 'lodging', 'car', 'activity', 'restaurant', 'transport', 'rail', 'note'
- `object_id` (string, required) — The object ID

## Object Types

| Type | API Name | Description |
|------|----------|-------------|
| `air` | AirObject | Flights |
| `lodging` | LodgingObject | Hotels |
| `car` | CarObject | Car rentals |
| `activity` | ActivityObject | Tours, excursions |
| `restaurant` | RestaurantObject | Restaurant reservations |
| `transport` | TransportObject | Ground transport (taxi, shuttle) |
| `rail` | RailObject | Train travel |
| `note` | NoteObject | Trip notes |

## OAuth Troubleshooting

If you're experiencing issues with TripIt API authentication:

### Common OAuth Issues

1. **"Access Request Failed"** when opening the authorization URL:
   - This usually means there's an issue with the OAuth request token request
   - Make sure your consumer key and secret are correct
   - Try using the `fixed_oauth.py` script which has stricter RFC 3986 encoding

2. **"Invalid oauth_verifier"** errors:
   - TripIt uses 'oob' (out-of-band) for the OAuth callback
   - Make sure 'oauth_callback=oob' is included correctly in the request

3. **Empty or unexpected responses from TripIt API**:
   - Check that your API application is approved and active in TripIt
   - Verify network connectivity to api.tripit.com

### OAuth Debugging Tools

Several debugging tools are available to help diagnose OAuth issues:

1. **Standalone OAuth script**:
   ```bash
   ./get_oauth_tokens.py
   ```

2. **Debug OAuth utility** (shows detailed request/response information):
   ```bash
   python scripts/debug_oauth.py
   ```

3. **Alternative OAuth implementations** to isolate issues:
   - `scripts/alt_oauth.py` - Uses `requests` library instead of `httpx`
   - `scripts/minimal_oauth.py` - Uses only standard library modules

For a detailed explanation of the OAuth fixes implemented in this project, see the [OAUTH_FIX.md](OAUTH_FIX.md) document.

## Using with MCP Clients

This MCP server can be used with any MCP-compatible client, including:

- Large Language Models (LLMs) that support the MCP protocol
- MCP client libraries in various programming languages
- Applications that can connect to MCP servers

To connect, point your MCP client to the server URL:

```
http://your-server-address:8000
```

## Development

### Running tests

```bash
# Make sure your virtual environment is activated
uv pip install -e ".[dev]"
pytest
```

### Building the package

```bash
# Make sure your virtual environment is activated
uv pip build
```

## License

MIT License

## Acknowledgments

- [FastMCP](https://github.com/shishirkh/fast-mcp) library for MCP implementation
- [TripIt API](https://tripit.github.io/api/doc/v1/) for providing travel data access
