import requests
import json
import time

# Test the API endpoints
def test_api():
    base_url = "http://localhost:8000"
    
    # Test root endpoint
    print("Testing root endpoint...")
    response = requests.get(f"{base_url}/")
    print(f"Root response: {response.json()}")
    
    # Test health endpoint
    print("\nTesting health endpoint...")
    response = requests.get(f"{base_url}/health")
    print(f"Health response: {response.json()}")
    
    # Test models endpoint
    print("\nTesting models endpoint...")
    response = requests.get(f"{base_url}/models")
    models = response.json()
    print(f"Available models: {[model['model'] for model in models['models']]}")
    
    # Test prompt processing
    print("\nTesting prompt processing...")
    prompt_data = {
        "prompt": "Create a Python function to calculate the factorial of a number"
    }
    
    response = requests.post(f"{base_url}/process-prompt", json=prompt_data)
    print(f"Prompt processing response: {response.json()}")
    
    # Get the session ID
    session_id = response.json()["session_id"]
    print(f"Session ID: {session_id}")
    
    # Wait a bit and check session status
    print("\nWaiting for workflow to complete...")
    time.sleep(10)
    
    # Check session status
    response = requests.get(f"{base_url}/session/{session_id}")
    session_status = response.json()
    print(f"Session status: {session_status['status']}")
    
    if session_status['status'] == 'completed':
        print("Workflow completed successfully!")
        print(f"Result: {session_status['result']}")
    else:
        print("Workflow still processing or encountered an error.")
        print(f"Logs: {session_status['logs']}")

if __name__ == "__main__":
    test_api()