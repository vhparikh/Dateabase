#!/bin/bash

# Deploy script for Dateabase app to Heroku

# Set colors for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting Heroku deployment process...${NC}"

# Check if heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo -e "${RED}Error: Heroku CLI is not installed. Please install it first.${NC}"
    echo "You can install it by following instructions at: https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Check if user is logged in to Heroku
echo -e "${YELLOW}Checking Heroku login status...${NC}"
heroku whoami &> /dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}You need to log in to Heroku first.${NC}"
    heroku login
fi

# Reset onboarding status for all users
echo -e "${YELLOW}Resetting onboarding status for all users...${NC}"
python backend/migrations/reset_onboarding.py

# Add new fields to the database
echo -e "${YELLOW}Adding new Hinge-like fields to the database...${NC}"
python backend/migrations/add_hinge_like_fields.py

# Add experience_name field to the database
echo -e "${YELLOW}Adding experience_name field to the Experience table...${NC}"
python backend/migrations/add_experience_name_field.py

# Commit the changes
echo -e "${YELLOW}Committing changes...${NC}"
git add .
git commit -m "Add experience_name field for custom experience names"

# Push to Heroku
echo -e "${YELLOW}Pushing to Heroku...${NC}"
git push heroku main

# Run migrations on Heroku
echo -e "${YELLOW}Running migrations on Heroku...${NC}"
heroku run python backend/migrations/reset_onboarding.py
heroku run python backend/migrations/add_hinge_like_fields.py
heroku run python backend/migrations/add_experience_name_field.py

echo -e "${GREEN}Deployment completed! The app should be live with the new changes.${NC}"
echo -e "${YELLOW}You can check the app at:${NC} $(heroku info -s | grep web_url | cut -d= -f2)" 