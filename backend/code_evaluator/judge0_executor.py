#judge0_executor.py

import requests
import time
import base64
import os

JUDGE0_API_URL = "https://judge0-ce.p.rapidapi.com"
JUDGE0_API_HOST = "judge0-ce.p.rapidapi.com"
JUDGE0_API_KEY = os.getenv("JUDGE0_API_KEY")
  # secure this later

HEADERS = {
    "X-RapidAPI-Key": JUDGE0_API_KEY,
    "X-RapidAPI-Host": JUDGE0_API_HOST,
    "Content-Type": "application/json"
}


def submit_code(source_code: str, language_id: int) -> dict:
    """
    Submits full code (with main() or input()) to Judge0 and returns the execution result.
    """
    payload = {
        "source_code": base64.b64encode(source_code.encode()).decode(),
        "language_id": language_id,
        "redirect_stderr_to_stdout": True
    }

    # Step 1: Submit the code
    response = requests.post(
        f"{JUDGE0_API_URL}/submissions?base64_encoded=true&wait=false",
        headers=HEADERS,
        json=payload
    )
    response.raise_for_status()
    token = response.json().get("token")

    if not token:
        return {"error": "No token received from Judge0"}

    # Step 2: Poll for results
    for _ in range(20):
        result = requests.get(
            f"{JUDGE0_API_URL}/submissions/{token}?base64_encoded=true&fields=*",
            headers=HEADERS
        )
        result.raise_for_status()
        data = result.json()

        if data["status"]["id"] not in [1, 2]:  # not "In Queue" or "Processing"
            def decode(field):
                return base64.b64decode(field).decode() if field else None

            return {
                "stdout": decode(data.get("stdout")),
                "stderr": decode(data.get("stderr")),
                "compile_output": decode(data.get("compile_output")),
                "status": data["status"]["description"]
            }

        time.sleep(1)

    return {"error": "Execution timed out"}