# Multilingual Text Intelligence Cloud Service

A cloud-native microservices application for automatic language detection, translation, and NLP analysis of multilingual text. Built with Google Cloud Platform services including Cloud Run, Pub/Sub, Firestore, and Translation API.

## Project Overview

This service accepts user-submitted text in any supported language and produces standardized outputs in English, including:
- **Sentiment Analysis**: Determines if the text expresses positive, negative, or neutral sentiment
- **Text Summarization**: Generates concise summaries of the input text
- **Named Entity Recognition (NER)**: Extracts key names, places, products, and other entities

The system supports both synchronous (real-time) and asynchronous (queued) processing modes based on text length.

## Architecture

The system follows a microservices-based cloud architecture with event-driven design:

- **API Service** (`api.py`): FastAPI-based REST API that handles text submission and result retrieval
- **Worker Service** (`worker.py`): Background service that processes jobs from Pub/Sub queue
- **Translation Service** (`translation_service.py`): Integrates with Google Cloud Translation API
- **NLP Service** (`nlp_service.py`): Placeholder for sentiment, summarization, and NER models (to be implemented by team)
- **Database** (`database.py`): Firestore integration for job storage and retrieval
- **Pub/Sub Client** (`pubsub_client.py`): Message queue integration for async processing

## Prerequisites

- Python 3.11+
- Google Cloud Project with billing enabled
- Google Cloud SDK (`gcloud`) installed and configured
- Docker (for local testing, optional)

## Setup Instructions

### 1. Clone and Navigate to Project

```bash
cd CSCI-5253-Final-Project
```

### 2. Set Up Google Cloud Project

```bash
# Set your project ID
export GOOGLE_CLOUD_PROJECT_ID=your-project-id-here

# Set the project in gcloud
gcloud config set project $GOOGLE_CLOUD_PROJECT_ID
```

### 3. Enable Required APIs

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

### 4. Set Up Authentication

```bash
# Authenticate with Google Cloud
gcloud auth login

# Set up application default credentials
gcloud auth application-default login
```

### 5. Initialize Firestore Database

1. Go to [Firestore Console](https://console.cloud.google.com/firestore)
2. Select your project
3. Choose "Native mode" (recommended) or "Datastore mode"
4. Select a location for your database
5. Click "Create Database"

### 6. Create Pub/Sub Topic and Subscription

The code will attempt to create these automatically, but you can also create them manually:

```bash
# Create topic
gcloud pubsub topics create text-processing-queue

# Create subscription
gcloud pubsub subscriptions create text-processing-subscription \
    --topic=text-processing-queue
```

### 7. Install Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 8. Configure Environment Variables

Copy the example environment file and update with your values:

```bash
cp env.example .env
```

Edit `.env` and set:
- `GOOGLE_CLOUD_PROJECT_ID`: Your Google Cloud project ID

Other variables have sensible defaults but can be customized.

## Local Development

### Running the API Service

```bash
# Set environment variable
export GOOGLE_CLOUD_PROJECT_ID=your-project-id

# Run the API
python api.py
```

Or using uvicorn directly:

```bash
uvicorn api:app --host 0.0.0.0 --port 8080 --reload
```

The API will be available at `http://localhost:8080`

### Running the Worker Service

In a separate terminal:

```bash
export GOOGLE_CLOUD_PROJECT_ID=your-project-id
python worker.py
```

### Testing the API

```bash
# Health check
curl http://localhost:8080/health

# Submit text for processing
curl -X POST http://localhost:8080/api/v1/process \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a test message in English."}'

# Check job status (replace JOB_ID with actual job ID from response)
curl http://localhost:8080/api/v1/jobs/JOB_ID
```

## Deployment to Google Cloud Run

### Option 1: Using the Deployment Script

```bash
# Make script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### Option 2: Manual Deployment

#### Deploy API Service

```bash
# Build and push image
gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT_ID/text-intelligence-api

# Deploy to Cloud Run
gcloud run deploy text-intelligence-api \
    --image gcr.io/$GOOGLE_CLOUD_PROJECT_ID/text-intelligence-api \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars GOOGLE_CLOUD_PROJECT_ID=$GOOGLE_CLOUD_PROJECT_ID \
    --memory 512Mi \
    --cpu 1
```

#### Deploy Worker Service

```bash
# Build and push image
gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT_ID/text-intelligence-worker

# Deploy to Cloud Run
gcloud run deploy text-intelligence-worker \
    --image gcr.io/$GOOGLE_CLOUD_PROJECT_ID/text-intelligence-worker \
    --platform managed \
    --region us-central1 \
    --no-allow-unauthenticated \
    --set-env-vars GOOGLE_CLOUD_PROJECT_ID=$GOOGLE_CLOUD_PROJECT_ID \
    --memory 1Gi \
    --cpu 1
```

### Option 3: Using Cloud Build

```bash
gcloud builds submit --config cloudbuild.yaml
```

## API Endpoints

### POST `/api/v1/process`

Submit text for processing.

**Request:**
```json
{
  "text": "Your text here in any language",
  "metadata": {
    "source": "optional metadata"
  }
}
```

**Response:**
```json
{
  "job_id": "job-abc123",
  "status": "completed",
  "mode": "sync",
  "created_at": "2024-01-01T12:00:00",
  "message": "Text processed successfully"
}
```

### GET `/api/v1/jobs/{job_id}`

Retrieve job status and results.

**Response:**
```json
{
  "job_id": "job-abc123",
  "status": "completed",
  "created_at": "2024-01-01T12:00:00",
  "completed_at": "2024-01-01T12:00:05",
  "result": {
    "original_text": "...",
    "detected_language": "fr",
    "translated_text": "...",
    "sentiment": {...},
    "summary": "...",
    "entities": [...]
  }
}
```

### GET `/health`

Health check endpoint.

## Project Structure

```
.
├── api.py                 # Main FastAPI application
├── worker.py              # Background worker service
├── config.py              # Configuration management
├── models.py              # Pydantic data models
├── database.py            # Firestore integration
├── pubsub_client.py       # Pub/Sub integration
├── translation_service.py # Translation API integration
├── nlp_service.py         # NLP service (placeholder for implementation)
├── utils.py               # Utility functions
├── Dockerfile.api         # Dockerfile for API service
├── Dockerfile.worker      # Dockerfile for worker service
├── requirements.txt       # Python dependencies
├── deploy.sh             # Deployment script
├── cloudbuild.yaml       # Cloud Build configuration
└── README.md             # This file
```

## Next Steps for Team

The following components are placeholders and need to be implemented:

1. **NLP Service** (`nlp_service.py`):
   - Integrate Vertex AI models OR
   - Deploy Hugging Face models via Cloud Run
   - Implement `analyze_sentiment()`, `summarize()`, and `extract_entities()`

2. **Testing**:
   - Unit tests for API endpoints
   - Integration tests for end-to-end flow
   - Load testing with Locust

3. **Monitoring**:
   - Set up Cloud Monitoring dashboards
   - Configure alerting for errors and latency

4. **Model Evaluation**:
   - Test with multilingual datasets
   - Calculate F1-scores and ROUGE metrics

## Configuration

Key configuration options in `config.py` or environment variables:

- `SYNC_THRESHOLD`: Character threshold for sync vs async processing (default: 1000)
- `PUBSUB_TOPIC_NAME`: Pub/Sub topic name (default: "text-processing-queue")
- `FIRESTORE_COLLECTION`: Firestore collection name (default: "text_jobs")
- `TRANSLATION_API_ENABLED`: Enable/disable translation API (default: true)

## Troubleshooting

### Authentication Errors

Ensure you have set up application default credentials:
```bash
gcloud auth application-default login
```

### Pub/Sub Topic Not Found

The code will attempt to create topics automatically, but you may need to create them manually or ensure proper IAM permissions.

### Firestore Connection Issues

Verify:
1. Firestore database is initialized in your project
2. You have proper IAM permissions (Firestore User role)
3. The project ID is correctly set

## License

See LICENSE file for details.

## Authors

- Deep Shukla
- Kendall Ahern
- Mateusz Muszynski
