# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-tenant SaaS platform that enables small businesses to deploy AI chat agents. The platform allows each business to create their own dedicated AI chat agent that can answer customer queries based on custom business data, handle bookings via Google Calendar, and communicate through a web chat interface with optional WhatsApp integration.

## Architecture

- **Backend**: FastAPI
- **Database & Auth**: Supabase
- **AI**: MCP (Multi-provider Client Platform) or OpenAI for LLM integration
- **Frontend**: HTML/JS for admin dashboard and embeddable chat widget

## Development Setup

### Backend

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (copy from .env.example)
cp .env.example .env
# Edit .env with your API keys and credentials

# Run development server
uvicorn app.main:app --reload
```

### Frontend

The frontend is a simple HTML/JS application that can be served by any web server.

### Using Docker

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## API Structure

- **/api/v1/auth**: Authentication endpoints
- **/api/v1/tenants**: Tenant management
- **/api/v1/documents**: Document upload and management
- **/api/v1/chat**: Chat conversations and messages
- **/api/v1/widget**: Chat widget embedding and configuration

## Database Schema

The application uses Supabase with the following tables:
- users: User accounts
- tenants: Business tenants
- documents: Uploaded documents
- document_embeddings: Vector embeddings of document chunks
- conversations: Chat conversations
- messages: Individual chat messages

## Project Structure

```
.
├── backend/                     # FastAPI backend
│   ├── app/                     # Application code
│   │   ├── api/                 # API routes
│   │   ├── core/                # Core functionality
│   │   ├── db/                  # Database connectivity
│   │   ├── models/              # Pydantic models
│   │   ├── services/            # Business logic services
│   │   └── utils/               # Utility functions
│   ├── migrations/              # Database migrations
│   └── tests/                   # Test suite
├── frontend/                    # Frontend code
│   ├── index.html               # Admin dashboard
│   ├── js/                      # JavaScript files
│   └── chat-widget.js           # Embeddable chat widget
└── README.md                    # Project documentation
```

## Common Development Tasks

### Running Tests

```bash
# From the backend directory
pytest
```

### Database Migrations

Apply the SQL migrations in `backend/migrations/create_tables.sql` to your Supabase database.

### Building and Deployment

The project includes Docker setup for containerized deployment:

```bash
# Build and run containers
docker-compose up -d
```