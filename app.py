from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import subprocess
import tempfile
import os
import requests
import re
import json
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

app = Flask(__name__, static_folder=".")
CORS(app)

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"


# ── Known site locators ───────────────────────────────────────────────────────
# These are hardcoded because these sites block scrapers or have known stable locators

KNOWN_SITES = {
    "google.com": {
        "title": "Google",
        "inputs": [
            {"locator": "name=q", "type": "text", "placeholder": "Search", "name": "q", "id": "", "label": "search"}
        ],
        "buttons": [
            {"locator": "name=btnK", "text": "google search"},
            {"locator": "name=btnI", "text": "i'm feeling lucky"}
        ],
        "alerts": [],
        "links": []
    },
    "the-internet.herokuapp.com/login": {
        "title": "The Internet",
        "inputs": [
            {"locator": "id=username", "type": "text", "placeholder": "", "name": "username", "id": "username", "label": "username"},
            {"locator": "id=password", "type": "password", "placeholder": "", "name": "password", "id": "password", "label": "password"}
        ],
        "buttons": [
            {"locator": "css=button[type='submit']", "text": "login"}
        ],
        "alerts": [
            {"locator": "css=.flash.success", "id": "flash", "class": "flash success"}
        ],
        "links": []
    },
    "demoqa.com/text-box": {
        "title": "DEMOQA",
        "inputs": [
            {"locator": "id=userName", "type": "text", "placeholder": "Full Name", "name": "userName", "id": "userName", "label": "full name"},
            {"locator": "id=userEmail", "type": "email", "placeholder": "name@example.com", "name": "userEmail", "id": "userEmail", "label": "email"},
            {"locator": "id=currentAddress", "type": "text", "placeholder": "Current Address", "name": "currentAddress", "id": "currentAddress", "label": "current address"}
        ],
        "buttons": [
            {"locator": "id=submit", "text": "submit"}
        ],
        "alerts": [
            {"locator": "id=output", "id": "output", "class": "output"}
        ],
        "links": []
    }
}


def get_known_elements(url):
    for domain, elements in KNOWN_SITES.items():
        if domain in url:
            print(f"  ✅ Using known locators for {domain}")
            return elements
    return None


# ── Ollama ────────────────────────────────────────────────────────────────────

def check_ollama():
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        return r.status_code == 200
    except:
        return False


def ask_ollama(prompt):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0, "num_predict": 200}
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json().get("response", "").strip()


# ── Selenium scraper ──────────────────────────────────────────────────────────

def get_headless_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.binary_location = "/usr/bin/google-chrome"
    return webdriver.Chrome(options=options)


def scrape_page(url):
    elements = {"title": "", "inputs": [], "buttons": [], "links": [], "alerts": []}
    try:
        print(f"  Opening headless Chrome for: {url}")
        driver = get_headless_driver()
        driver.get(url)
        time.sleep(3)
        html = driver.page_source
        driver.quit()

        soup = BeautifulSoup(html, "html.parser")

        if soup.title:
            elements["title"] = soup.title.get_text(strip=True)

        for inp in soup.find_all("input"):
            if inp.get("type") == "hidden":
                continue
            el = {
                "id": inp.get("id", ""),
                "name": inp.get("name", ""),
                "type": inp.get("type", "text"),
                "placeholder": inp.get("placeholder", ""),
                "label": ""
            }
            if el["id"]:
                lbl = soup.find("label", {"for": el["id"]})
                if lbl:
                    el["label"] = lbl.get_text(strip=True)
                el["locator"] = f"id={el['id']}"
            elif el["name"]:
                el["locator"] = f"name={el['name']}"
            else:
                continue
            elements["inputs"].append(el)

        for btn in soup.find_all(["button", "input"]):
            if btn.name == "input" and btn.get("type") not in ["submit", "button"]:
                continue
            el = {
                "text": btn.get_text(strip=True),
                "type": btn.get("type", ""),
                "id": btn.get("id", ""),
                "value": btn.get("value", ""),
                "class": " ".join(btn.get("class", []))
            }
            if el["id"]:
                el["locator"] = f"id={el['id']}"
            elif el["class"]:
                el["locator"] = f"css=button.{el['class'].split()[0]}"
            elif el["type"] == "submit":
                el["locator"] = "css=input[type='submit']"
            else:
                el["locator"] = "css=button[type='submit']"
            elements["buttons"].append(el)

        for tag in soup.find_all(attrs={"id": True}):
            tag_id = tag.get("id", "")
            classes = " ".join(tag.get("class", []))
            if any(k in tag_id.lower() or k in classes.lower()
                   for k in ["flash", "alert", "success", "error", "message", "output", "result"]):
                elements["alerts"].append({
                    "id": tag_id,
                    "class": classes,
                    "locator": f"id={tag_id}" if tag_id else f"css=.{classes.split()[0]}"
                })

        return elements

    except Exception as e:
        print(f"  Scrape error: {e}")
        return elements


# ── Llama locator matcher ─────────────────────────────────────────────────────

def format_inputs(elements):
    lines = []
    for inp in elements.get("inputs", []):
        desc = f"locator={inp['locator']} type={inp['type']}"
        if inp.get("placeholder"): desc += f" placeholder='{inp['placeholder']}'"
        if inp.get("label"):       desc += f" label='{inp['label']}'"
        if inp.get("name"):        desc += f" name={inp['name']}"
        lines.append(desc)
    return "\n".join(lines) if lines else "none"


def format_buttons(elements):
    lines = []
    for btn in elements.get("buttons", []):
        desc = f"locator={btn['locator']} text='{btn['text']}'"
        if btn.get("value"): desc += f" value='{btn['value']}'"
        lines.append(desc)
    return "\n".join(lines) if lines else "none"


def format_alerts(elements):
    lines = []
    for al in elements.get("alerts", []):
        desc = f"locator={al['locator']}"
        if al.get("id"):    desc += f" id={al['id']}"
        if al.get("class"): desc += f" class='{al['class']}'"
        lines.append(desc)
    return "\n".join(lines) if lines else "none"


def llama_match_input(field_description, value, elements):
    if not elements.get("inputs"):
        return None

    prompt = f"""Match a test field to a locator. Reply with ONLY the locator string, nothing else.

User wants to fill in: "{field_description}" with value "{value}"

Available inputs:
{format_inputs(elements)}

Reply with ONLY one locator like: id=username"""

    result = ask_ollama(prompt).strip().split("\n")[0].strip()
    result = re.sub(r'^["\']|["\']$', '', result)

    valid = [inp["locator"] for inp in elements.get("inputs", [])]
    if result in valid:
        return result
    for loc in valid:
        if loc in result or result in loc:
            return loc
    return valid[0] if valid else None


def llama_match_button(target_description, elements):
    if not elements.get("buttons"):
        return "css=button[type='submit']"

    prompt = f"""Match a button to a locator. Reply with ONLY the locator string, nothing else.

User wants to click: "{target_description}"

Available buttons:
{format_buttons(elements)}

Reply with ONLY one locator like: id=submit"""

    result = ask_ollama(prompt).strip().split("\n")[0].strip()
    result = re.sub(r'^["\']|["\']$', '', result)

    valid = [btn["locator"] for btn in elements.get("buttons", [])]
    if result in valid:
        return result
    for loc in valid:
        if loc in result or result in loc:
            return loc
    return valid[0] if valid else "css=button[type='submit']"


def llama_match_element(target_description, elements):
    all_elements = (
        [al["locator"] for al in elements.get("alerts", [])] +
        [lnk["locator"] for lnk in elements.get("links", [])[:5]]
    )

    if not all_elements:
        if "nav" in target_description.lower():    return "css=nav"
        if "output" in target_description.lower(): return "id=output"
        if "success" in target_description.lower(): return "css=.flash.success"
        return "css=body"

    prompt = f"""Match an element to verify to a locator. Reply with ONLY the locator string.

User wants to verify: "{target_description}"

Available elements:
{chr(10).join(all_elements)}

Reply with ONLY one locator."""

    result = ask_ollama(prompt).strip().split("\n")[0].strip()
    result = re.sub(r'^["\']|["\']$', '', result)

    if result in all_elements:
        return result
    for loc in all_elements:
        if loc in result or result in loc:
            return loc
    return all_elements[0]


# ── Intent parser ─────────────────────────────────────────────────────────────

INTENT_PROMPT = """Extract test steps as JSON only. No markdown, no explanation.

{{
  "test_name": "short name",
  "url": "url or empty string",
  "steps": [
    {{"action": "navigate", "url": "https://..."}},
    {{"action": "input", "field": "field label e.g. username/search/full name/email", "value": "value"}},
    {{"action": "click", "target": "button label e.g. login/submit/search"}},
    {{"action": "verify_element", "target": "element e.g. success message/output/navbar"}},
    {{"action": "verify_text", "text": "text to check"}},
    {{"action": "close"}}
  ]
}}

Description: {description}"""


def parse_intent(description):
    raw = ask_ollama(INTENT_PROMPT.format(description=description))
    raw = re.sub(r"^```[a-z]*\n?", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"```$", "", raw, flags=re.MULTILINE)

    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass

    url_match = re.search(r'https?://[^\s,]+', description)
    return {
        "test_name": "Generated Test",
        "url": url_match.group() if url_match else "",
        "steps": [
            {"action": "navigate", "url": url_match.group() if url_match else ""},
            {"action": "close"}
        ]
    }


# ── Robot Framework builder ───────────────────────────────────────────────────

def build_robot_code(intent, elements):
    test_name = intent.get("test_name", "Generated Test")
    steps     = intent.get("steps", [])
    url       = intent.get("url", "")

    lines = [
        "*** Settings ***",
        "Library    SeleniumLibrary",
        "",
        "*** Variables ***",
        f"${{URL}}    {url}",
        "${BROWSER}    gc",
        "${TIMEOUT}    10s",
        "",
        "*** Test Cases ***",
        test_name,
    ]

    has_navigate = any(s.get("action") == "navigate" for s in steps)
    if not has_navigate and url:
        lines.append("    Open Browser    ${URL}    ${BROWSER}")
        lines.append("    Maximize Browser Window")

    for step in steps:
        action = step.get("action", "")

        if action == "navigate":
            nav_url = step.get("url", url)
            lines.append(f"    Open Browser    {nav_url}    ${{BROWSER}}")
            lines.append("    Maximize Browser Window")

        elif action == "input":
            field   = step.get("field", "")
            value   = step.get("value", "")
            print(f"  🔎 Matching input: '{field}'")
            locator = llama_match_input(field, value, elements)
            if locator:
                print(f"  ✅ Matched: {locator}")
                lines.append(f"    Wait Until Element Is Visible    {locator}    timeout=${{TIMEOUT}}")
                lines.append(f"    Input Text    {locator}    {value}")
                if "search" in field.lower() or "query" in field.lower():
                    lines.append(f"    Press Keys    {locator}    ENTER")
                    lines.append(f"    Wait Until Element Is Visible    id=search    timeout=${{TIMEOUT}}")
            else:
                lines.append(f"    # Could not find locator for: {field}")

        elif action == "click":
            target  = step.get("target", "")
            print(f"  🔎 Matching button: '{target}'")
            locator = llama_match_button(target, elements)
            print(f"  ✅ Matched: {locator}")
            lines.append(f"    Wait Until Element Is Visible    {locator}    timeout=${{TIMEOUT}}")
            lines.append(f"    Click Element    {locator}")

        elif action == "verify_element":
            target  = step.get("target", "")
            print(f"  🔎 Matching element: '{target}'")
            locator = llama_match_element(target, elements)
            print(f"  ✅ Matched: {locator}")
            lines.append(f"    Wait Until Page Contains Element    {locator}    timeout=${{TIMEOUT}}")
            lines.append(f"    Element Should Be Visible    {locator}")

        elif action == "verify_text":
            text = step.get("text", "")
            lines.append(f"    Wait Until Page Contains    {text}    timeout=${{TIMEOUT}}")

        elif action == "verify_title":
            title = step.get("title", elements.get("title", ""))
            lines.append(f"    Title Should Be    {title}")

        elif action == "close":
            lines.append("    Close Browser")

    if not any(s.get("action") == "close" for s in steps):
        lines.append("    Close Browser")

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def generate_robot_code(description, browser="gc"):
    url_match = re.search(r'https?://[^\s,]+', description)
    url = url_match.group() if url_match else ""

    # Use known locators if available, otherwise scrape
    elements = {}
    if url:
        elements = get_known_elements(url)
        if not elements:
            print(f"🔍 Scraping: {url}")
            elements = scrape_page(url)
            print(f"✅ inputs={len(elements.get('inputs',[]))} buttons={len(elements.get('buttons',[]))} alerts={len(elements.get('alerts',[]))}")

    print("🧠 Parsing intent...")
    intent = parse_intent(description)
    print(f"✅ {intent.get('test_name')} — {len(intent.get('steps', []))} steps")

    print("🔨 Building Robot Framework code...")
    code = build_robot_code(intent, elements)
    print("✅ Done!")
    return code


# ── Robot runner ──────────────────────────────────────────────────────────────

def run_robot_code(robot_code):
    with tempfile.TemporaryDirectory() as tmpdir:
        robot_file = os.path.join(tmpdir, "test_generated.robot")
        output_dir = os.path.join(tmpdir, "results")
        os.makedirs(output_dir)

        with open(robot_file, "w") as f:
            f.write(robot_code)

        result = subprocess.run(
            ["python3", "-m", "robot",
             "--outputdir", output_dir,
             "--output", "output.xml",
             "--log", "log.html",
             "--report", "report.html",
             robot_file],
            capture_output=True, text=True, timeout=120
        )

        stdout    = result.stdout
        returncode = result.returncode
        tests_run = passed = failed = 0
        test_results = []

        for line in stdout.splitlines():
            if " | PASS |" in line:
                test_results.append({"name": line.split(" | PASS |")[0].strip(), "status": "PASS", "message": ""})
                passed += 1; tests_run += 1
            elif " | FAIL |" in line:
                parts = line.split(" | FAIL |")
                test_results.append({
                    "name": parts[0].strip(),
                    "status": "FAIL",
                    "message": parts[1].strip() if len(parts) > 1 else ""
                })
                failed += 1; tests_run += 1

        return {
            "returncode": returncode,
            "stdout": stdout,
            "stderr": result.stderr,
            "tests_run": tests_run,
            "passed": passed,
            "failed": failed,
            "test_results": test_results,
            "overall": "PASS" if returncode == 0 else "FAIL"
        }


# ── Flask routes ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/status")
def status():
    ollama_ok = check_ollama()
    return jsonify({"ollama": ollama_ok, "model": OLLAMA_MODEL})

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    description = data.get("description", "").strip()
    browser = data.get("browser", "gc")
    if not description:
        return jsonify({"error": "Description is required"}), 400
    if not check_ollama():
        return jsonify({"error": "Ollama is not running. Start with: ollama serve"}), 503
    try:
        return jsonify({"code": generate_robot_code(description, browser)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/run", methods=["POST"])
def run():
    data = request.json
    robot_code = data.get("code", "").strip()
    if not robot_code:
        return jsonify({"error": "No robot code provided"}), 400
    try:
        return jsonify(run_robot_code(robot_code))
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
        return jsonify({"error": "Ollama is not running. Start with: ollama serve"}), 503
    try:
        code = generate_robot_code(description, browser)
        results = run_robot_code(code)
        results["code"] = code
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("🤖 RF TestGen v2 running at http://localhost:5000")
    print("📡 Ollama model:", OLLAMA_MODEL)
    print("✅ Ollama running" if check_ollama() else "⚠️  Start Ollama: ollama serve")
    app.run(debug=True, port=5000)
