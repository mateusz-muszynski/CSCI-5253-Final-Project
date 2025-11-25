# Quick Start Guide

This guide will help you get the Multilingual Text Intelligence Service up and running quickly.

## Prerequisites Check

Run the setup check script to verify everything is configured:

```bash
python setup_check.py
```

## Step 1: Set Google Cloud Project ID

```bash
export GOOGLE_CLOUD_PROJECT_ID=your-project-id-here
```

## Step 2: Enable Google Cloud APIs

```bash
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    pubsub.googleapis.com \
    translate.googleapis.com \
    firestore.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com
```

## Step 3: Set Up Authentication

```bash
gcloud auth application-default login
```

## Step 4: Initialize Firestore

1. Go to https://console.cloud.google.com/firestore
2. Select your project
3. Click "Create Database"
4. Choose "Native mode"
5. Select a location (e.g., `us-central`)
6. Click "Create"

## Step 5: Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 6: Run Locally (Optional)

### Start the API:

```bash
export GOOGLE_CLOUD_PROJECT_ID=your-project-id
python api.py
```

The API will be available at `http://localhost:8080`

### In another terminal, start the worker:

```bash
export GOOGLE_CLOUD_PROJECT_ID=your-project-id
python worker.py
```

### Test the API:

```bash
python test_api.py
```

## Step 7: Deploy to Cloud Run

### Option A: Use the deployment script

```bash
export GOOGLE_CLOUD_PROJECT_ID=your-project-id
./deploy.sh
```

### Option B: Manual deployment

```bash
# Deploy API
gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT_ID/text-intelligence-api
gcloud run deploy text-intelligence-api \
    --image gcr.io/$GOOGLE_CLOUD_PROJECT_ID/text-intelligence-api \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars GOOGLE_CLOUD_PROJECT_ID=$GOOGLE_CLOUD_PROJECT_ID

# Deploy Worker
gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT_ID/text-intelligence-worker
gcloud run deploy text-intelligence-worker \
    --image gcr.io/$GOOGLE_CLOUD_PROJECT_ID/text-intelligence-worker \
    --platform managed \
    --region us-central1 \
    --no-allow-unauthenticated \
    --set-env-vars GOOGLE_CLOUD_PROJECT_ID=$GOOGLE_CLOUD_PROJECT_ID
```

## Step 8: Get Your API URL

After deployment, get your API URL:

```bash
gcloud run services describe text-intelligence-api \
    --region us-central1 \
    --format 'value(status.url)'
```

## Next Steps

1. **Implement NLP Service**: Update `nlp_service.py` with actual models (Vertex AI or Hugging Face)
2. **Add Tests**: Create unit and integration tests
3. **Set Up Monitoring**: Configure Cloud Monitoring dashboards
4. **Load Testing**: Use Locust or similar tools for performance testing

## Troubleshooting

### "Project not found" errors
- Verify your project ID is correct
- Run: `gcloud config set project YOUR_PROJECT_ID`

### "Permission denied" errors
- Ensure you have the necessary IAM roles
- Run: `gcloud auth application-default login`

### Pub/Sub topic not found
- The code will try to create it automatically
- Or create manually: `gcloud pubsub topics create text-processing-queue`

### Firestore connection issues
- Verify Firestore is initialized in your project
- Check IAM permissions for Firestore

## Need Help?

See the full [README.md](README.md) for detailed documentation.

