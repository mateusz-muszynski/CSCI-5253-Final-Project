#!/bin/bash
# Deployment script for Google Cloud Run

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Deploying Multilingual Text Intelligence Service${NC}"

# Check if PROJECT_ID is set
if [ -z "$GOOGLE_CLOUD_PROJECT_ID" ]; then
    echo -e "${RED}Error: GOOGLE_CLOUD_PROJECT_ID environment variable is not set${NC}"
    echo "Please set it with: export GOOGLE_CLOUD_PROJECT_ID=your-project-id"
    exit 1
fi

PROJECT_ID=$GOOGLE_CLOUD_PROJECT_ID
REGION=${REGION:-us-central1}

echo -e "${YELLOW}Using project: $PROJECT_ID${NC}"
echo -e "${YELLOW}Using region: $REGION${NC}"

# Set the project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${YELLOW}Enabling required Google Cloud APIs...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    pubsub.googleapis.com \
    translate.googleapis.com \
    firestore.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com

# Build and deploy API service
echo -e "${YELLOW}Building API service...${NC}"
gcloud builds submit --tag gcr.io/$PROJECT_ID/text-intelligence-api --file Dockerfile.api .

echo -e "${YELLOW}Deploying API service to Cloud Run...${NC}"
gcloud run deploy text-intelligence-api \
    --image gcr.io/$PROJECT_ID/text-intelligence-api \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars GOOGLE_CLOUD_PROJECT_ID=$PROJECT_ID \
    --memory 512Mi \
    --cpu 1

# Build and deploy worker service
echo -e "${YELLOW}Building worker service...${NC}"
gcloud builds submit --tag gcr.io/$PROJECT_ID/text-intelligence-worker --file Dockerfile.worker .

echo -e "${YELLOW}Deploying worker service to Cloud Run...${NC}"
gcloud run deploy text-intelligence-worker \
    --image gcr.io/$PROJECT_ID/text-intelligence-worker \
    --platform managed \
    --region $REGION \
    --no-allow-unauthenticated \
    --set-env-vars GOOGLE_CLOUD_PROJECT_ID=$PROJECT_ID \
    --memory 1Gi \
    --cpu 1 \
    --timeout 3600 \
    --max-instances 10

# Get API URL
API_URL=$(gcloud run services describe text-intelligence-api --region $REGION --format 'value(status.url)')

echo -e "${GREEN}Deployment complete!${NC}"
echo -e "${GREEN}API URL: $API_URL${NC}"
echo -e "${YELLOW}Note: Make sure Pub/Sub topics and subscriptions are created${NC}"
echo -e "${YELLOW}Note: Make sure Firestore database is initialized${NC}"

