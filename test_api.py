"""
Simple test script to verify API functionality.
Run this after starting the API service locally.
"""
import requests
import json
import time
import sys

API_BASE_URL = "http://localhost:8080"


def test_health_check():
    """Test the health check endpoint."""
    print("Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        response.raise_for_status()
        print(f"✓ Health check passed: {response.json()}")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False


def test_sync_processing():
    """Test synchronous text processing."""
    print("\nTesting synchronous processing (short text)...")
    try:
        payload = {
            "text": "This is a test message. I am very happy with this service!",
            "metadata": {"test": True}
        }
        response = requests.post(
            f"{API_BASE_URL}/api/v1/process",
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        print(f"✓ Sync processing response: {json.dumps(result, indent=2)}")
        
        if result.get("status") == "completed":
            print("✓ Job completed synchronously")
            return result.get("job_id")
        else:
            print(f"⚠ Job status: {result.get('status')}")
            return result.get("job_id")
    except Exception as e:
        print(f"✗ Sync processing failed: {e}")
        return None


def test_async_processing():
    """Test asynchronous text processing."""
    print("\nTesting asynchronous processing (long text)...")
    try:
        # Create a long text to trigger async mode
        long_text = "This is a long text. " * 100  # Should exceed default threshold
        payload = {
            "text": long_text,
            "metadata": {"test": True, "mode": "async"}
        }
        response = requests.post(
            f"{API_BASE_URL}/api/v1/process",
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        print(f"✓ Async processing response: {json.dumps(result, indent=2)}")
        
        if result.get("mode") == "async":
            print("✓ Job queued for async processing")
            return result.get("job_id")
        else:
            print(f"⚠ Unexpected mode: {result.get('mode')}")
            return result.get("job_id")
    except Exception as e:
        print(f"✗ Async processing failed: {e}")
        return None


def test_job_status(job_id):
    """Test retrieving job status."""
    if not job_id:
        print("\n⚠ Skipping job status test (no job_id)")
        return False
    
    print(f"\nTesting job status retrieval for {job_id}...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/jobs/{job_id}")
        response.raise_for_status()
        result = response.json()
        print(f"✓ Job status: {json.dumps(result, indent=2)}")
        return True
    except Exception as e:
        print(f"✗ Job status retrieval failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Multilingual Text Intelligence Service - API Tests")
    print("=" * 60)
    
    # Test health check
    if not test_health_check():
        print("\n✗ Health check failed. Is the API running?")
        sys.exit(1)
    
    # Test sync processing
    sync_job_id = test_sync_processing()
    
    # Wait a bit for sync processing
    if sync_job_id:
        time.sleep(2)
        test_job_status(sync_job_id)
    
    # Test async processing
    async_job_id = test_async_processing()
    
    # Wait for async processing (may take longer)
    if async_job_id:
        print("\nWaiting 10 seconds for async processing...")
        time.sleep(10)
        test_job_status(async_job_id)
    
    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

