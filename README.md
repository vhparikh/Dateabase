# DateABase - Princeton's Experience-Based Dating App

DateABase connects people through shared experiences rather than traditional profile swiping.

## Key Features

- Experience-based matching with personalized recommendations
- Swipe interaction to like or pass on experiences
- Location-based experiences with Google Maps integration
- Modern UI with responsive design

## Tech Stack

- **Frontend**: React, Tailwind CSS, Framer Motion
- **Backend**: Flask, SQLAlchemy, Python3
- **Database**: SQLite (dev), PostgreSQL (prod)
- **APIs**: Google Maps, Pinecone, Cohere, Gemini

## Quick Start

### Prerequisites
- Node.js (v14+), Python 3.13+
- npm/yarn, pip

### Setup
1. Clone and install:
   ```
   git clone https://github.com/username/dateabase.git
   cd dateabase
   npm install
   ```

2. Environment configuration:
   ```
   # In frontend/.env
   REACT_APP_API_URL=http://localhost:5001
   REACT_APP_GOOGLE_MAPS_API_KEY=YOUR_KEY
   ```

3. Start development:
   ```
   npm start
   ```

## Core Components

### Google Maps Integration
- Location autocomplete and map previews
- Directions and static maps for experiences
- Precise location data storage

### Recommendation Engine
- Pinecone vector search with Cohere embeddings
- Preference-based experience matching
- Semantic search for relevant experiences

### Experience Image Management
- Automated image fetching from Google Places API

## License

MIT License - see LICENSE file for details. 