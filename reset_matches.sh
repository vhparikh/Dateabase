#!/bin/bash

# This script resets only the matches-related tables in the database
# It will truncate the Match and UserSwipe tables

echo "This script will reset all Match and UserSwipe data in the database"
echo "Make sure you have the Heroku CLI installed and are logged in"
echo "------------------------------------------------------------"

# Get the database URL from Heroku
DATABASE_URL=$(heroku config:get DATABASE_URL)

if [ -z "$DATABASE_URL" ]; then
  echo "Error: Could not retrieve DATABASE_URL from Heroku"
  echo "Make sure you're logged in to Heroku CLI and have access to the app"
  exit 1
fi

echo "Retrieved DATABASE_URL from Heroku"
echo "Connecting to the database..."

# Connect to the database and truncate the tables
cat <<EOF | PGPASSWORD=${DATABASE_URL#*:*@*:*\/} psql ${DATABASE_URL}
-- Truncate the match-related tables
TRUNCATE TABLE "match" CASCADE;
TRUNCATE TABLE "user_swipe" CASCADE;

-- Verify the tables are empty
SELECT COUNT(*) AS match_count FROM "match";
SELECT COUNT(*) AS swipe_count FROM "user_swipe";

-- Output confirmation
SELECT 'Reset complete.' AS message;
EOF

echo "------------------------------------------------------------"
echo "Match and UserSwipe tables have been reset!"
echo "Users can now start fresh with new swipes and matches" 