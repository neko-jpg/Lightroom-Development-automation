import requests
import json
import time

BASE_URL = "http://127.0.0.1:5100"

def run_test():
    """Runs a sequence of API tests."""

    # --- Step 1: Create a new job ---
    print("--- Testing POST /job ---")
    prompt_data = {"prompt": "Test prompt for a sunny day portrait."}
    try:
        response = requests.post(f"{BASE_URL}/job", json=prompt_data)
        response.raise_for_status()

        job_data = response.json()
        job_id = job_data.get("jobId")

        if not job_id:
            print("  [FAIL] No jobId returned.")
            return

        print(f"  [SUCCESS] Job '{job_id}' created successfully.")
    except requests.exceptions.RequestException as e:
        print(f"  [FAIL] Request failed: {e}")
        return

    # Give the server a moment
    time.sleep(1)

    # --- Step 2: Get the next job ---
    print("\n--- Testing GET /job/next ---")
    try:
        response = requests.get(f"{BASE_URL}/job/next")

        if response.status_code == 404:
            print("  [FAIL] No job found in the queue.")
            return

        response.raise_for_status()

        next_job_data = response.json()
        next_job_id = next_job_data.get("jobId")

        if next_job_id == job_id:
            print(f"  [SUCCESS] Retrieved job '{next_job_id}' correctly.")
        else:
            print(f"  [FAIL] Retrieved job '{next_job_id}' but expected '{job_id}'.")
            return

    except requests.exceptions.RequestException as e:
        print(f"  [FAIL] Request failed: {e}")
        return

    # Give the server a moment
    time.sleep(1)

    # --- Step 3: Report job success ---
    print(f"\n--- Testing POST /job/{job_id}/result (success) ---")
    try:
        result_data = {"status": "success"}
        response = requests.post(f"{BASE_URL}/job/{job_id}/result", json=result_data)
        response.raise_for_status()

        print(f"  [SUCCESS] Reported success for job '{job_id}'.")

    except requests.exceptions.RequestException as e:
        print(f"  [FAIL] Request failed: {e}")
        return

    print("\n--- All tests completed successfully! ---")

if __name__ == "__main__":
    run_test()
