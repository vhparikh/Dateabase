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