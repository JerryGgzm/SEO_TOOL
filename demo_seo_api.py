"""
API-Level Demo for the SEO Module

This script acts as a client to test the API endpoints of a running
SEO service. It does NOT import any of the service's internal modules.

Prerequisites:
1. The main FastAPI application must be running.
   You can start it with:
   uvicorn main:app --host 0.0.0.0 --port 8000

2. This script should be run in a separate terminal.

It will test the following endpoints:
- GET /api/seo/health
- POST /api/seo/optimize
- POST /api/seo/batch/optimize
"""
import requests
import json
import time
import sys

# --- Configuration ---
BASE_URL = "http://localhost:8000"
# Note: In a real application, this token would be acquired through an
# OAuth2 login flow. For this demo, we use a static test token.
# The backend's `get_current_user` dependency would need to be adjusted
# to accept this for testing purposes.
DEMO_AUTH_TOKEN = "test-token-for-demo"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {DEMO_AUTH_TOKEN}"
}

def print_header(title: str):
    """Prints a formatted header."""
    print("\n" + "=" * 60)
    print(f"🚀 {title}")
    print("=" * 60)

def check_server_health():
    """Checks if the API server is running and healthy."""
    print_header("Step 1: Checking Server Health")
    health_url = f"{BASE_URL}/api/seo/health"
    try:
        response = requests.get(health_url, timeout=3)
        if response.status_code == 200 and response.json().get("status") == "ok":
            print(f"✅ Health check successful. Server is running at {BASE_URL}")
            return True
        else:
            print(f"❌ Server responded with status {response.status_code}: {response.text}")
            return False
    except requests.ConnectionError:
        print(f"❌ Connection Error: Could not connect to the server at {BASE_URL}.")
        print("   Please ensure the FastAPI server is running in a separate terminal.")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred during health check: {e}")
        return False

def run_optimize_demo():
    """Tests the /api/seo/optimize endpoint."""
    print_header("Step 2: Testing Single Content Optimization Endpoint")
    optimize_url = f"{BASE_URL}/api/seo/optimize"

    payload = {
        "content": "Our new AI tool for Unity is designed to accelerate development by automating repetitive tasks. It helps developers focus on creativity.",
        "content_type": "tweet",
        "optimization_level": "aggressive",
        "target_keywords": ["AI", "Unity", "GameDev", "Asset Pipeline"]
    }

    print("▶️  Sending POST request to /api/seo/optimize with payload:")
    print(json.dumps(payload, indent=2))

    try:
        response = requests.post(optimize_url, headers=HEADERS, json=payload, timeout=30)

        print(f"\n◀️  Received response (Status: {response.status_code})")
        if response.status_code == 200:
            print("✅ Optimization successful!")
            print("Response JSON:")
            print(json.dumps(response.json(), indent=2))
        else:
            print("❌ Optimization failed.")
            print("Response Content:")
            print(response.text)

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

def run_batch_optimize_demo():
    """Tests the /api/seo/batch/optimize endpoint."""
    print_header("Step 3: Testing Batch Content Optimization Endpoint")
    batch_url = f"{BASE_URL}/api/seo/batch/optimize"

    payload = {
        "content_list": [
            {
                "content": "First tweet: exploring AI in game development.",
                "content_type": "tweet",
                "keywords": ["AI", "gamedev"]
            },
            {
                "content": "Second post: A deep dive into our new SEO tools and how they help founders.",
                "content_type": "blog_post",
                "keywords": ["SEO", "SaaS", "startups"]
            }
        ],
        "optimization_level": "moderate"
    }

    print("▶️  Sending POST request to /api/seo/batch/optimize with payload:")
    print(json.dumps(payload, indent=2))

    try:
        response = requests.post(batch_url, headers=HEADERS, json=payload, timeout=60)

        print(f"\n◀️  Received response (Status: {response.status_code})")
        if response.status_code == 200:
            print("✅ Batch optimization successful!")
            print("Response JSON:")
            print(json.dumps(response.json(), indent=2))
        else:
            print("❌ Batch optimization failed.")
            print("Response Content:")
            print(response.text)

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")


def main():
    """Main function to run all API demos."""
    if not check_server_health():
        sys.exit(1)

    run_optimize_demo()
    run_batch_optimize_demo()

    print("\n" + "=" * 60)
    print("🎉 API Demo Finished!")
    print("=" * 60)

if __name__ == "__main__":
    main() 