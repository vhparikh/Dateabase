#!/bin/bash

# Script to delete a user and all associated data from the Dateabase application
# Usage: ./delete_user.sh [netid]

# Check if argument is provided
if [ $# -eq 0 ]; then
  echo "Error: Please provide a Princeton NetID"
  echo "Usage: ./delete_user.sh [netid]"
  exit 1
fi

# Get the database URL from the .env file if it exists
if [ -f ".env" ]; then
  source ".env"
fi

# Use the DATABASE_URL from environment or default to the one from database.py
DB_URL=${DATABASE_URL:-"postgresql://ueaqcj622ro270:pf6999e838eb1f1f2e5af5b4b9d17b2fcdc2475e46597ea2d0dcdbd6bdb1e13af@ceqbglof0h8enj.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/dc26u3dpl6nepd"}

# Extract connection parameters from DATABASE_URL
if [[ $DB_URL == postgresql://* ]]; then
  # Parse the URL to extract components
  DB_USER=$(echo $DB_URL | sed -n 's/^postgresql:\/\/\([^:]*\):.*/\1/p')
  DB_PASS=$(echo $DB_URL | sed -n 's/^postgresql:\/\/[^:]*:\([^@]*\)@.*/\1/p')
  DB_HOST=$(echo $DB_URL | sed -n 's/^postgresql:\/\/[^@]*@\([^:]*\):.*/\1/p')
  DB_PORT=$(echo $DB_URL | sed -n 's/^postgresql:\/\/[^@]*@[^:]*:\([^\/]*\)\/.*/\1/p')
  DB_NAME=$(echo $DB_URL | sed -n 's/^postgresql:\/\/[^@]*@[^\/]*\/\(.*\)$/\1/p')
else
  echo "Error: Invalid database URL format"
  exit 1
fi

# Use the parameter as netid
USER_CONDITION="netid = '$1'"

# Confirmation prompt
echo "WARNING: This will permanently delete the user and all associated data."
read -p "Are you sure you want to continue? (y/n): " confirm
if [[ $confirm != [yY] ]]; then
  echo "Operation cancelled."
  exit 0
fi

# Create temporary SQL file
TMP_SQL=$(mktemp)

# Write SQL commands to file
cat > $TMP_SQL << EOF
-- Start a transaction
BEGIN;

-- Get user ID if we're searching by username
DO \$\$
DECLARE
  target_user_id INTEGER;
BEGIN
  -- Get the user ID
  SELECT id INTO target_user_id FROM "user" WHERE $USER_CONDITION;
  
  IF target_user_id IS NULL THEN
    RAISE EXCEPTION 'User not found';
  END IF;
  
  -- Delete matches where user is involved
  DELETE FROM "match" WHERE user1_id = target_user_id OR user2_id = target_user_id;
  
  -- Delete user swipes
  DELETE FROM "user_swipe" WHERE user_id = target_user_id;
  
  -- Delete experiences
  DELETE FROM "experience" WHERE user_id = target_user_id;
  
  -- Delete user images
  DELETE FROM "user_image" WHERE user_id = target_user_id;
  
  -- Finally delete the user
  DELETE FROM "user" WHERE id = target_user_id;
  
  RAISE NOTICE 'User with ID % has been deleted along with all associated data', target_user_id;
END \$\$;

-- Commit the transaction
COMMIT;
EOF

# Execute the SQL file
echo "Connecting to database and executing deletion..."
export PGPASSWORD="$DB_PASS"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$TMP_SQL"

# Remove temporary SQL file
rm $TMP_SQL

echo "Operation completed."
