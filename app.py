from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import subprocess
import tempfile
import os
import requests
import re

app = Flask(__name__, static_folder=".")
CORS(app)

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"

SYSTEM_PROMPT = """You are an expert Robot Framework automation test engineer.
Generate clean, production-ready Robot Framework test cases using SeleniumLibrary.

Rules:
- Always include *** Settings ***, *** Variables ***, and *** Test Cases *** sections
- Use explicit waits (Wait Until Element Is Visible) — never use Sleep
- Store URLs and config in *** Variables ***
- Add a *** Keywords *** section for reusable steps
- Use 4-space indentation consistently
- Always end with Close Browser or Close All Browsers
- Output ONLY the Robot Framework code, no explanation, no markdown fences, no backticks
- Use 'Title Should Contain' instead of 'Title Should Be' for page title checks
- Use 'gc' as the browser name, never 'chrome'
- Use 'Wait Until Element Is Visible' with timeout=10s for all elements"""


def check_ollama():
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        return r.status_code == 200
    except:
        return False


def generate_robot_code(description, browser):
    prompt = f"{SYSTEM_PROMPT}\n\nUse {browser} as the browser. Important: use 'gc' as the browser name for Google Chrome, not 'chrome'. Important: use 'gc' as the browser name for Google Chrome, not 'chrome'.\n\nTest to generate:\n{description}"

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 1000
        }
    }

    resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    code = data.get("response", "").strip()

    # Strip markdown fences if model adds them
    code = re.sub(r"^```[a-z]*\n?", "", code, flags=re.MULTILINE)
    code = re.sub(r"```$", "", code, flags=re.MULTILINE)
    return code.strip()


def run_robot_code(robot_code):
    with tempfile.TemporaryDirectory() as tmpdir:
        robot_file = os.path.join(tmpdir, "test_generated.robot")
        output_dir = os.path.join(tmpdir, "results")
        os.makedirs(output_dir)

        with open(robot_file, "w") as f:
            f.write(robot_code)

        result = subprocess.run(
            [
                "python3", "-m", "robot",
                "--outputdir", output_dir,
                "--output", "output.xml",
                "--log", "log.html",
                "--report", "report.html",
                robot_file
            ],
            capture_output=True,
            text=True,
            timeout=120
        )

        stdout = result.stdout
        returncode = result.returncode
        tests_run = 0
        passed = 0
        failed = 0
        test_results = []

        for line in stdout.splitlines():
            if " | PASS |" in line:
                test_name = line.split(" | PASS |")[0].strip()
                test_results.append({"name": test_name, "status": "PASS", "message": ""})
                passed += 1
                tests_run += 1
            elif " | FAIL |" in line:
                parts = line.split(" | FAIL |")
                test_name = parts[0].strip()
                message = parts[1].strip() if len(parts) > 1 else ""
                test_results.append({"name": test_name, "status": "FAIL", "message": message})
                failed += 1
                tests_run += 1

        log_path = os.path.join(output_dir, "log.html")
        return {
            "returncode": returncode,
            "stdout": stdout,
            "stderr": result.stderr,
            "tests_run": tests_run,
            "passed": passed,
            "failed": failed,
            "test_results": test_results,
            "overall": "PASS" if returncode == 0 else "FAIL",
            "log_available": os.path.exists(log_path)
        }


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/status")
def status():
    ollama_ok = check_ollama()
    return jsonify({
        "ollama": ollama_ok,
        "model": OLLAMA_MODEL,
        "message": "Ollama is running" if ollama_ok else "Ollama not found — run: ollama serve"
    })


@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    description = data.get("description", "").strip()
    browser = data.get("browser", "gc")

    if not description:
        return jsonify({"error": "Description is required"}), 400
    if not check_ollama():
        return jsonify({"error": "Ollama is not running. Start it with: ollama serve"}), 503

    try:
        code = generate_robot_code(description, browser)
        return jsonify({"code": code})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/run", methods=["POST"])
def run():
    data = request.json
    robot_code = data.get("code", "").strip()

    if not robot_code:
        return jsonify({"error": "No robot code provided"}), 400

    try:
        results = run_robot_code(robot_code)
        return jsonify(results)
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Test timed out after 120 seconds"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/generate-and-run", methods=["POST"])
def generate_and_run():
    data = request.json
    description = data.get("description", "").strip()
    browser = data.get("browser", "gc")

    if not description:
        return jsonify({"error": "Description is required"}), 400
    if not check_ollama():
        return jsonify({"error": "Ollama is not running. Start it with: ollama serve"}), 503

    try:
        code = generate_robot_code(description, browser)
        results = run_robot_code(code)
        results["code"] = code
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("🤖 RF TestGen v2 running at http://localhost:5000")
    print("📡 Using Ollama with model:", OLLAMA_MODEL)
    if check_ollama():
        print("✅ Ollama is running")
    else:
        print("⚠️  Ollama not detected — start it with: ollama serve")
    app.run(debug=True, port=5000)
