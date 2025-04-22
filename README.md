# DateABase - Princeton's Experience-Based Dating App

DateABase is a modern dating application focused on matching people through shared experiences instead of profile swiping.

## Features

- Experience-based matching: Connect with people who share interest in the same activities
- Clean, modern UI with responsive design
- Swipe interaction to like or pass on experiences
- Match notifications when two users like the same experience
- User profiles with personalized experience recommendations
- Location-based experiences with Google Maps integration

## Tech Stack

- **Frontend**: React, Tailwind CSS, Framer Motion for animations, Google Maps API
- **Backend**: Flask, SQLAlchemy, JWT for authentication
- **Database**: SQLite (development), PostgreSQL (production)

## Getting Started

### Prerequisites

- Node.js (v14+)
- Python 3.8+
- npm or yarn
- pip

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/username/dateabase.git
   cd dateabase
   ```

2. Install dependencies:
   ```
   npm install
   ```

   This will install both frontend and backend dependencies.

3. Create a `.env` file in the frontend directory:
   ```
   # API URLs
   REACT_APP_API_URL=http://localhost:5001
   REACT_APP_GOOGLE_MAPS_API_KEY=YOUR_GOOGLE_MAPS_API_KEY
   
   # Other configs
   REACT_APP_JWT_AUDIENCE=dating_app_users
   REACT_APP_JWT_ISSUER=dateabase
   ```

4. Start the development servers:
   ```
   npm start
   ```

   This will start both the frontend and backend servers concurrently.

## Usage

1. Register a new account or use the demo account
2. Explore experiences on the home page
3. Swipe right to like an experience, left to pass
4. Check matches when you connect with someone
5. Create your own experiences to find like-minded people

## Troubleshooting

- If you encounter CORS issues, make sure both frontend and backend servers are running
- For authentication problems, try clearing local storage and logging in again
- If maps aren't loading, check that your Google Maps API key is correct in the .env file

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Princeton University for inspiration
- The open source community for the amazing tools and libraries

## Google Maps API Integration

The app now integrates Google Maps API for enhanced location features:

### Setup

1. Get a Google Maps API key from the [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the following APIs in your project:
   - Maps JavaScript API
   - Places API
   - Geocoding API
   - Static Maps API
3. Add your API key to the `.env` file in the frontend directory:
   ```
   REACT_APP_GOOGLE_MAPS_API_KEY=your_api_key_here
   ```

### Features

- **Location Autocomplete**: When creating or editing experiences, users can search for locations with Google Places Autocomplete
- **Map Preview**: After selecting a location, a map preview shows the exact spot with a marker
- **Directions**: Experience cards include a "Get Directions" button that opens Google Maps navigation
- **Static Maps**: Experiences with coordinates show a small static map image
- **Coordinates Storage**: The app properly stores latitude, longitude, and place_id for precise location data 

## Personalized Recommendations

The app supports personalized experience recommendations using Pinecone vector search with Cohere embeddings:

### Setup

1. Create a Pinecone account and create an index with dimension 1024
2. Create a Cohere account and get an API key from [Cohere Dashboard](https://dashboard.cohere.com/api-keys)
3. Set the required environment variables:
   
   **Local Development:**
   ```
   PINECONE_API_KEY=your_pinecone_api_key
   PINECONE_INDEX=your_pinecone_index_name
   COHERE_API_KEY=your_cohere_api_key
   ```

   **Heroku Deployment:**
   ```
   heroku config:set PINECONE_API_KEY=your_pinecone_api_key
   heroku config:set PINECONE_INDEX_NAME=your_pinecone_index_name
   heroku config:set COHERE_API_KEY=your_cohere_api_key
   ```

4. Run the indexing script to populate Pinecone with existing experiences:
   
   **Local:**
   ```
   cd backend
   python index_experiences.py
   ```
   
   **Heroku:**
   ```
   heroku run python backend/index_experiences.py
   ```

### Testing Pinecone Connectivity

If you're having issues with Pinecone integration, you can run the test script:

```
cd backend
python pinecone_test.py
```

This script will:
1. Verify your environment variables are set correctly
2. Attempt to connect to your Pinecone index
3. Perform a test upsert, query, and delete operation
4. Report detailed error messages if any step fails

### Features

- **Preference-Based Matching**: Users get experience recommendations based on their preferences
- **Semantic Search**: Uses vector similarity to find experiences that match user preferences
- **Automatic Indexing**: New experiences are automatically indexed for recommendations
- **Fallback Mechanism**: If no personalized matches found, shows recent experiences 