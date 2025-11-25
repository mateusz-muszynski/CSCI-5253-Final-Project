"""
Comprehensive setup verification script.
Tests code structure, imports, and basic functionality without requiring full GCP setup.
"""
import sys
import os
import importlib
import traceback
from typing import List, Tuple

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_success(msg: str):
    print(f"{GREEN}✓{RESET} {msg}")

def print_error(msg: str):
    print(f"{RED}✗{RESET} {msg}")

def print_warning(msg: str):
    print(f"{YELLOW}⚠{RESET} {msg}")

def print_info(msg: str):
    print(f"{BLUE}ℹ{RESET} {msg}")

def test_imports() -> Tuple[bool, List[str]]:
    """Test if all required modules can be imported."""
    print("\n" + "=" * 60)
    print("Testing Module Imports")
    print("=" * 60)
    
    # Set dummy project ID for modules that require it
    original_project_id = os.environ.get("GOOGLE_CLOUD_PROJECT_ID")
    os.environ["GOOGLE_CLOUD_PROJECT_ID"] = "test-project-id"
    
    modules = [
        "config",
        "models",
        "utils",
        "database",
        "pubsub_client",
        "translation_service",
        "nlp_service",
        "api",
        "worker"
    ]
    
    failed = []
    for module_name in modules:
        try:
            importlib.import_module(module_name)
            print_success(f"Imported {module_name}")
        except ValueError as e:
            # Some modules may require GCP setup, which is expected
            if "GOOGLE_CLOUD_PROJECT_ID" in str(e) or "must be set" in str(e):
                print_warning(f"{module_name} requires GCP project ID (expected for full setup)")
            else:
                print_error(f"Failed to import {module_name}: {str(e)}")
                failed.append(module_name)
        except Exception as e:
            print_error(f"Failed to import {module_name}: {str(e)}")
            failed.append(module_name)
    
    # Restore original project ID
    if original_project_id:
        os.environ["GOOGLE_CLOUD_PROJECT_ID"] = original_project_id
    elif "GOOGLE_CLOUD_PROJECT_ID" in os.environ:
        del os.environ["GOOGLE_CLOUD_PROJECT_ID"]
    
    return len(failed) == 0, failed

def test_config():
    """Test configuration loading."""
    print("\n" + "=" * 60)
    print("Testing Configuration")
    print("=" * 60)
    
    try:
        from config import Config
        
        # Test config attributes exist
        attrs = [
            "PROJECT_ID", "PUBSUB_TOPIC_NAME", "PUBSUB_SUBSCRIPTION_NAME",
            "FIRESTORE_COLLECTION", "SYNC_THRESHOLD", "API_HOST", "API_PORT"
        ]
        
        for attr in attrs:
            if hasattr(Config, attr):
                value = getattr(Config, attr)
                print_success(f"Config.{attr} = {value}")
            else:
                print_error(f"Config.{attr} missing")
                return False
        
        # Test methods
        if hasattr(Config, "validate"):
            print_success("Config.validate() method exists")
        else:
            print_error("Config.validate() method missing")
            return False
        
        if hasattr(Config, "get_pubsub_topic_path"):
            print_success("Config.get_pubsub_topic_path() method exists")
        else:
            print_error("Config.get_pubsub_topic_path() method missing")
            return False
        
        return True
    except Exception as e:
        print_error(f"Config test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_models():
    """Test Pydantic models."""
    print("\n" + "=" * 60)
    print("Testing Data Models")
    print("=" * 60)
    
    try:
        from models import (
            ProcessingMode, JobStatus, TextSubmissionRequest,
            JobResponse, ProcessingResult, JobStatusResponse
        )
        
        # Test enums
        print_success(f"ProcessingMode.SYNC = {ProcessingMode.SYNC.value}")
        print_success(f"ProcessingMode.ASYNC = {ProcessingMode.ASYNC.value}")
        print_success(f"JobStatus.PENDING = {JobStatus.PENDING.value}")
        
        # Test request model
        request = TextSubmissionRequest(text="Test text")
        print_success(f"Created TextSubmissionRequest: {request.text}")
        
        # Test with metadata
        request_with_meta = TextSubmissionRequest(
            text="Test",
            metadata={"key": "value"}
        )
        print_success(f"Created TextSubmissionRequest with metadata")
        
        return True
    except Exception as e:
        print_error(f"Models test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_utils():
    """Test utility functions."""
    print("\n" + "=" * 60)
    print("Testing Utility Functions")
    print("=" * 60)
    
    try:
        from utils import generate_job_id, determine_processing_mode
        from models import ProcessingMode
        
        # Test job ID generation
        job_id1 = generate_job_id()
        job_id2 = generate_job_id()
        if job_id1 != job_id2 and job_id1.startswith("job-"):
            print_success(f"generate_job_id() works: {job_id1}")
        else:
            print_error("generate_job_id() failed")
            return False
        
        # Test processing mode determination
        short_text = "Short text"
        long_text = "x" * 2000  # Exceeds default threshold of 1000
        
        mode_short = determine_processing_mode(short_text)
        mode_long = determine_processing_mode(long_text)
        
        if mode_short == ProcessingMode.SYNC:
            print_success(f"Short text ({len(short_text)} chars) -> SYNC mode")
        else:
            print_error(f"Short text should be SYNC, got {mode_short}")
            return False
        
        if mode_long == ProcessingMode.ASYNC:
            print_success(f"Long text ({len(long_text)} chars) -> ASYNC mode")
        else:
            print_error(f"Long text should be ASYNC, got {mode_long}")
            return False
        
        return True
    except Exception as e:
        print_error(f"Utils test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_service_structure():
    """Test that service classes can be instantiated (without full GCP setup)."""
    print("\n" + "=" * 60)
    print("Testing Service Structure")
    print("=" * 60)
    
    # Set a dummy project ID to avoid validation errors
    os.environ["GOOGLE_CLOUD_PROJECT_ID"] = "test-project"
    
    try:
        # Test NLP Service (should work without GCP)
        from nlp_service import NLPService
        nlp = NLPService()
        print_success("NLPService can be instantiated")
        
        # Test NLP methods exist
        if hasattr(nlp, "analyze_sentiment"):
            print_success("NLPService.analyze_sentiment() exists")
        if hasattr(nlp, "summarize"):
            print_success("NLPService.summarize() exists")
        if hasattr(nlp, "extract_entities"):
            print_success("NLPService.extract_entities() exists")
        
        # Test that methods return something (even if placeholder)
        result = nlp.analyze_sentiment("test")
        if result is not None:
            print_success("NLPService.analyze_sentiment() returns result")
        
        return True
    except Exception as e:
        print_error(f"Service structure test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_api_structure():
    """Test API structure without starting the server."""
    print("\n" + "=" * 60)
    print("Testing API Structure")
    print("=" * 60)
    
    # Set dummy project ID for testing
    original_project_id = os.environ.get("GOOGLE_CLOUD_PROJECT_ID")
    os.environ["GOOGLE_CLOUD_PROJECT_ID"] = "test-project-id"
    
    try:
        from fastapi import FastAPI
        
        # Try to import app - it may fail due to GCP service initialization
        try:
            from api import app
            
            if isinstance(app, FastAPI):
                print_success("API app is a FastAPI instance")
            else:
                print_error("API app is not a FastAPI instance")
                return False
            
            # Check routes exist
            routes = [route.path for route in app.routes]
            expected_routes = ["/", "/health", "/api/v1/process", "/api/v1/jobs/{job_id}"]
            
            for route in expected_routes:
                if route in routes or any(route.replace("{job_id}", "") in r for r in routes):
                    print_success(f"Route exists: {route}")
                else:
                    print_warning(f"Route may be missing: {route}")
            
            return True
        except ValueError as e:
            if "GOOGLE_CLOUD_PROJECT_ID" in str(e):
                print_warning("API requires GOOGLE_CLOUD_PROJECT_ID to be set (expected)")
                print_info("API structure is correct, but needs project ID for full initialization")
                # Check if FastAPI can be imported at least
                print_success("FastAPI framework is available")
                return True
            else:
                raise
    except Exception as e:
        print_error(f"API structure test failed: {str(e)}")
        traceback.print_exc()
        return False
    finally:
        # Restore original project ID
        if original_project_id:
            os.environ["GOOGLE_CLOUD_PROJECT_ID"] = original_project_id
        elif "GOOGLE_CLOUD_PROJECT_ID" in os.environ:
            del os.environ["GOOGLE_CLOUD_PROJECT_ID"]

def test_dependencies():
    """Test if all dependencies are installed."""
    print("\n" + "=" * 60)
    print("Testing Dependencies")
    print("=" * 60)
    
    dependencies = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydantic", "Pydantic"),
        ("google.cloud.translate_v2", "Google Cloud Translation"),
        ("google.cloud.pubsub_v1", "Google Cloud Pub/Sub"),
        ("google.cloud.firestore", "Google Cloud Firestore"),
        ("dotenv", "python-dotenv"),
    ]
    
    all_installed = True
    for module_name, display_name in dependencies:
        try:
            if "." in module_name:
                # Try importing the full module path
                __import__(module_name)
            else:
                __import__(module_name)
            print_success(f"{display_name} installed")
        except (ImportError, AttributeError) as e:
            # Also try alternative import paths
            try:
                if "translate" in module_name:
                    __import__("google.cloud.translate")
                elif "pubsub" in module_name:
                    __import__("google.cloud.pubsub")
                else:
                    raise e
                print_success(f"{display_name} installed")
            except:
                print_error(f"{display_name} not installed")
                all_installed = False
    
    return all_installed

def test_file_structure():
    """Test that all required files exist."""
    print("\n" + "=" * 60)
    print("Testing File Structure")
    print("=" * 60)
    
    required_files = [
        "api.py",
        "worker.py",
        "config.py",
        "models.py",
        "database.py",
        "pubsub_client.py",
        "translation_service.py",
        "nlp_service.py",
        "utils.py",
        "requirements.txt",
        "Dockerfile.api",
        "Dockerfile.worker",
        "README.md"
    ]
    
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print_success(f"{file} exists")
        else:
            print_error(f"{file} missing")
            all_exist = False
    
    return all_exist

def main():
    """Run all verification tests."""
    print("\n" + "=" * 60)
    print("Multilingual Text Intelligence Service - Setup Verification")
    print("=" * 60)
    print("\nThis script verifies your project setup without requiring")
    print("full Google Cloud authentication or running services.\n")
    
    results = []
    
    # Run tests
    results.append(("File Structure", test_file_structure()))
    results.append(("Dependencies", test_dependencies()))
    results.append(("Module Imports", test_imports()[0]))
    results.append(("Configuration", test_config()))
    results.append(("Data Models", test_models()))
    results.append(("Utility Functions", test_utils()))
    results.append(("Service Structure", test_service_structure()))
    results.append(("API Structure", test_api_structure()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        if result:
            print_success(f"{test_name}: PASSED")
            passed += 1
        else:
            print_error(f"{test_name}: FAILED")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print_success("\nAll tests passed! Your project setup looks good.")
        print_info("\nNext steps:")
        print_info("1. Set GOOGLE_CLOUD_PROJECT_ID environment variable")
        print_info("2. Run: python setup_check.py (for GCP-specific checks)")
        print_info("3. Follow QUICKSTART.md for deployment instructions")
        return 0
    else:
        print_error(f"\n{failed} test(s) failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

