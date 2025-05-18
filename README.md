# LocalVoiceAI - AI Chat Agent Platform

A multi-tenant SaaS platform that enables small businesses to deploy AI chat agents capable of:

- Answering customer queries based on custom business data.
- Handling bookings via Google Calendar.
- Communicating through a web chat interface and optional WhatsApp integration.

## Architecture

- **Backend**: FastAPI
- **Database & Auth**: SQLite database (replacing Supabase)
- **AI**: OpenAI's GPT-4.1-nano-2025-04-14 model for LLM integration
- **Frontend**: HTML/JS with Neobrutalism design

## Core Capabilities

Each business (tenant) can spin up its own dedicated AI chat agent that can:

- Handle general customer support queries.
- Retrieve answers based on the business's uploaded documents (PDFs, text files, etc.).
- Perform actions like scheduling bookings using Google Calendar.

## User Flow

1. Business owner registers and logs in
2. Business owner uploads their documents
3. Business owner gets a link to integrate the chat widget into their website
4. Once the chat widget is deployed on their website, a customer can interact with the chat widget
5. Questions are processed by the LLM, which finds the intent and retrieves relevant information from the business's documents

## Project Structure

```
.
├── backend/                     # FastAPI backend
│   ├── app/                     # Application code
│   │   ├── api/                 # API routes
│   │   ├── core/                # Core functionality (config, etc.)
│   │   ├── db/                  # Database connectivity
│   │   ├── models/              # Pydantic models
│   │   ├── services/            # Business logic services
│   │   └── utils/               # Utility functions
│   ├── migrations/              # Database migrations
│   └── tests/                   # Test suite
├── frontend/                    # Frontend code (chat widget, admin interface)
│   ├── index.html               # Admin dashboard
│   ├── js/                      # JavaScript files
│   └── chat-widget.js           # Embeddable chat widget
└── README.md                    # Project documentation
```

## Setup & Installation

### Prerequisites

- Python 3.9+
- Supabase account
- MCP API Key (or OpenAI API key)

### Backend Setup

1. Create a virtual environment:
   ```
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file based on `.env.example`:
   ```
   cp .env.example .env
   ```

4. Set up your Supabase database:
   - Create a new project in Supabase
   - Run the SQL migrations in `migrations/create_tables.sql`
   - Update the `.env` file with your Supabase credentials

5. Start the backend server:
   ```
   uvicorn app.main:app --reload
   ```

### Frontend Setup

The frontend is a simple HTML/JS application that can be served by any web server.

1. Update the API URL in `frontend/js/app.js` if needed
2. Serve the frontend files (using a local server for development)

## API Documentation

Once the server is running, access the API documentation at:

```
http://localhost:8000/docs
```

## Features

- **Multi-tenant Architecture**: Each business has its own isolated environment
- **Document Processing**: Upload and process business documents for AI context
- **Chat Widget**: Easily embeddable chat widget for business websites
- **Admin Dashboard**: Manage tenants, documents, and view conversation history
- **Google Calendar Integration**: Schedule appointments through the chat interface
- **Optional WhatsApp Integration**: Extend the chat capabilities to WhatsApp

## License

MIT