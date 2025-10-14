#!/bin/bash
# Load environment from root .env file
set -a
source ../.env
set +a

# Start the frontend development server
npm start