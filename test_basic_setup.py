"""
Basic setup test - verifies core functionality without requiring GCP authentication.
This is a simpler test that focuses on what can be verified locally.
"""
import sys
import os

# Set dummy project ID to avoid validation errors
os.environ["GOOGLE_CLOUD_PROJECT_ID"] = "test-project"

def test_core_components():
    """Test core components that don't require GCP."""
    print("=" * 60)
    print("Basic Setup Verification")
    print("=" * 60)
    print()
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Imports
    print("1. Testing module imports...")
    tests_total += 1
    try:
        from config import Config
        from models import ProcessingMode, JobStatus, TextSubmissionRequest
        from utils import generate_job_id, determine_processing_mode
        from nlp_service import NLPService
        print("   ✓ All core modules imported successfully")
        tests_passed += 1
    except Exception as e:
        print(f"   ✗ Import failed: {e}")
        return False
    
    # Test 2: Configuration
    print("\n2. Testing configuration...")
    tests_total += 1
    try:
        assert hasattr(Config, "SYNC_THRESHOLD")
        assert Config.SYNC_THRESHOLD == 1000
        print(f"   ✓ Configuration loaded (SYNC_THRESHOLD = {Config.SYNC_THRESHOLD})")
        tests_passed += 1
    except Exception as e:
        print(f"   ✗ Configuration test failed: {e}")
    
    # Test 3: Data Models
    print("\n3. Testing data models...")
    tests_total += 1
    try:
        request = TextSubmissionRequest(text="Test")
        assert request.text == "Test"
        assert ProcessingMode.SYNC.value == "sync"
        assert ProcessingMode.ASYNC.value == "async"
        print("   ✓ Data models work correctly")
        tests_passed += 1
    except Exception as e:
        print(f"   ✗ Data models test failed: {e}")
    
    # Test 4: Utility Functions
    print("\n4. Testing utility functions...")
    tests_total += 1
    try:
        job_id = generate_job_id()
        assert job_id.startswith("job-")
        assert len(job_id) > 10
        
        short_text = "Short"
        long_text = "x" * 2000
        
        mode1 = determine_processing_mode(short_text)
        mode2 = determine_processing_mode(long_text)
        
        assert mode1 == ProcessingMode.SYNC
        assert mode2 == ProcessingMode.ASYNC
        
        print(f"   ✓ Utilities work (job_id: {job_id}, modes: {mode1.value}/{mode2.value})")
        tests_passed += 1
    except Exception as e:
        print(f"   ✗ Utility functions test failed: {e}")
    
    # Test 5: NLP Service
    print("\n5. Testing NLP service structure...")
    tests_total += 1
    try:
        nlp = NLPService()
        assert hasattr(nlp, "analyze_sentiment")
        assert hasattr(nlp, "summarize")
        assert hasattr(nlp, "extract_entities")
        
        result = nlp.analyze_sentiment("test")
        assert result is not None
        
        print("   ✓ NLP service structure is correct (ready for team implementation)")
        tests_passed += 1
    except Exception as e:
        print(f"   ✗ NLP service test failed: {e}")
    
    # Test 6: File Structure
    print("\n6. Testing file structure...")
    tests_total += 1
    required_files = [
        "api.py", "worker.py", "config.py", "models.py",
        "database.py", "pubsub_client.py", "translation_service.py",
        "nlp_service.py", "utils.py", "requirements.txt",
        "Dockerfile.api", "Dockerfile.worker", "README.md"
    ]
    
    missing = [f for f in required_files if not os.path.exists(f)]
    if not missing:
        print(f"   ✓ All {len(required_files)} required files exist")
        tests_passed += 1
    else:
        print(f"   ✗ Missing files: {', '.join(missing)}")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Results: {tests_passed}/{tests_total} tests passed")
    print("=" * 60)
    
    if tests_passed == tests_total:
        print("\n✓ All basic tests passed! Your project setup is correct.")
        print("\nNext steps:")
        print("  1. Set GOOGLE_CLOUD_PROJECT_ID environment variable")
        print("  2. Run: python setup_check.py (for GCP-specific checks)")
        print("  3. Follow QUICKSTART.md for deployment")
        return True
    else:
        print(f"\n✗ {tests_total - tests_passed} test(s) failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    success = test_core_components()
    sys.exit(0 if success else 1)

