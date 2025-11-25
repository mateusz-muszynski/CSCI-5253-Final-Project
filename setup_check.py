"""
Setup verification script to check if all prerequisites are met.
"""
import os
import sys
import subprocess

def check_python_version():
    """Check if Python version is 3.11+."""
    print("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 11:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} (requires 3.11+)")
        return False


def check_gcloud():
    """Check if gcloud is installed and configured."""
    print("\nChecking Google Cloud SDK...")
    try:
        result = subprocess.run(
            ["gcloud", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✓ gcloud installed: {result.stdout.split()[0]}")
            
            # Check if project is set
            project_result = subprocess.run(
                ["gcloud", "config", "get-value", "project"],
                capture_output=True,
                text=True
            )
            if project_result.returncode == 0 and project_result.stdout.strip():
                print(f"✓ Project configured: {project_result.stdout.strip()}")
            else:
                print("⚠ No project configured. Run: gcloud config set project YOUR_PROJECT_ID")
            
            return True
        else:
            print("✗ gcloud not found")
            return False
    except FileNotFoundError:
        print("✗ gcloud not found. Install from: https://cloud.google.com/sdk/docs/install")
        return False


def check_environment_variables():
    """Check if required environment variables are set."""
    print("\nChecking environment variables...")
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
    if project_id:
        print(f"✓ GOOGLE_CLOUD_PROJECT_ID: {project_id}")
        return True
    else:
        print("⚠ GOOGLE_CLOUD_PROJECT_ID not set")
        print("  Set it with: export GOOGLE_CLOUD_PROJECT_ID=your-project-id")
        return False


def check_dependencies():
    """Check if required Python packages are installed."""
    print("\nChecking Python dependencies...")
    try:
        import fastapi
        import google.cloud.translate
        import google.cloud.pubsub
        import google.cloud.firestore
        print("✓ Required packages are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing package: {e}")
        print("  Install with: pip install -r requirements.txt")
        return False


def check_apis_enabled():
    """Check if required Google Cloud APIs are enabled."""
    print("\nChecking Google Cloud APIs...")
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
    if not project_id:
        print("⚠ Skipping API check (GOOGLE_CLOUD_PROJECT_ID not set)")
        return False
    
    required_apis = [
        "cloudbuild.googleapis.com",
        "run.googleapis.com",
        "pubsub.googleapis.com",
        "translate.googleapis.com",
        "firestore.googleapis.com"
    ]
    
    try:
        result = subprocess.run(
            ["gcloud", "services", "list", "--enabled", "--project", project_id],
            capture_output=True,
            text=True
        )
        
        enabled_apis = result.stdout.lower()
        all_enabled = True
        
        for api in required_apis:
            api_name = api.split(".")[0]
            if api_name in enabled_apis or api in enabled_apis:
                print(f"✓ {api_name} API enabled")
            else:
                print(f"✗ {api_name} API not enabled")
                all_enabled = False
        
        if not all_enabled:
            print("\n  Enable APIs with:")
            print(f"  gcloud services enable {' '.join(required_apis)}")
        
        return all_enabled
    except Exception as e:
        print(f"⚠ Could not check APIs: {e}")
        return False


def main():
    """Run all checks."""
    print("=" * 60)
    print("Multilingual Text Intelligence Service - Setup Check")
    print("=" * 60)
    
    checks = [
        check_python_version(),
        check_gcloud(),
        check_environment_variables(),
        check_dependencies(),
        check_apis_enabled()
    ]
    
    print("\n" + "=" * 60)
    if all(checks):
        print("✓ All checks passed! You're ready to go.")
        return 0
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

