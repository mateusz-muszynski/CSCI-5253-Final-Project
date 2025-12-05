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
# Create temporary build config for API
cat > /tmp/cloudbuild-api.yaml <<EOF
steps:
- name: 'gcr.io/cloud-builders/docker'
  args:
    - 'build'
    - '-t'
    - 'gcr.io/$PROJECT_ID/text-intelligence-api:latest'
    - '-f'
    - 'Dockerfile.api'
    - '.'
images:
- 'gcr.io/$PROJECT_ID/text-intelligence-api:latest'
EOF

gcloud builds submit --config /tmp/cloudbuild-api.yaml .

echo -e "${YELLOW}Deploying API service to Cloud Run...${NC}"
gcloud run deploy text-intelligence-api \
    --image gcr.io/$PROJECT_ID/text-intelligence-api:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars GOOGLE_CLOUD_PROJECT_ID=$PROJECT_ID \
    --memory 512Mi \
    --cpu 1

# Build and deploy worker service
echo -e "${YELLOW}Building worker service...${NC}"
# Create temporary build config for worker
cat > /tmp/cloudbuild-worker.yaml <<EOF
steps:
- name: 'gcr.io/cloud-builders/docker'
  args:
    - 'build'
    - '-t'
    - 'gcr.io/$PROJECT_ID/text-intelligence-worker:latest'
    - '-f'
    - 'Dockerfile.worker'
    - '.'
images:
- 'gcr.io/$PROJECT_ID/text-intelligence-worker:latest'
EOF

gcloud builds submit --config /tmp/cloudbuild-worker.yaml .

echo -e "${YELLOW}Deploying worker service to Cloud Run...${NC}"
gcloud run deploy text-intelligence-worker \
    --image gcr.io/$PROJECT_ID/text-intelligence-worker:latest \
    --platform managed \
    --region $REGION \
    --no-allow-unauthenticated \
    --set-env-vars GOOGLE_CLOUD_PROJECT_ID=$PROJECT_ID \
    --memory 1Gi \
    --cpu 1 \
    --timeout 3600 \
    --max-instances 10

# Clean up temporary build configs
rm -f /tmp/cloudbuild-api.yaml /tmp/cloudbuild-worker.yaml

# Get API URL
API_URL=$(gcloud run services describe text-intelligence-api --region $REGION --format 'value(status.url)')

echo -e "${GREEN}Deployment complete!${NC}"
echo -e "${GREEN}API URL: $API_URL${NC}"
echo -e "${YELLOW}Note: Make sure Pub/Sub topics and subscriptions are created${NC}"
echo -e "${YELLOW}Note: Make sure Firestore database is initialized${NC}"

