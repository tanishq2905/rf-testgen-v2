# RF TestGen v2 🤖

An AI-powered Robot Framework test case generator **and runner**. Describe your test in plain English — get production-ready `.robot` code generated and executed instantly.

Runs completely **free and offline** using [Ollama](https://ollama.com) with Llama 3. No API key needed.

---

## ✨ Features

- **Plain English → Robot Framework** — no syntax knowledge needed
- **Actually runs the tests** — not just generates them, executes them and shows pass/fail
- **Live results panel** — see individual test pass/fail with error messages
- **100% free** — powered by Ollama running locally, no API costs
- **Works offline** — no internet required after setup
- **Syntax highlighted output** — colour-coded Robot Framework code
- **Multiple browsers** — Chrome, Firefox, Edge

---

## 🏗️ Architecture

```
Browser UI (index.html)
      ↓
Flask Backend (app.py)
      ↓
Ollama (local LLM — Llama 3)
      ↓
Generates .robot file
      ↓
Runs via robot command
      ↓
Returns pass/fail results to UI
```

---

## 🚀 Setup

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/rf-testgen-v2.git
cd rf-testgen-v2
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Install Ollama
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 4. Pull Llama 3
```bash
ollama pull llama3
```
This downloads the model (~4GB) once. Free forever after.

### 5. Install ChromeDriver
Make sure ChromeDriver matches your Chrome version and is in your PATH:
```bash
# Ubuntu/Debian
sudo apt install chromium-chromedriver

# Or use webdriver-manager
pip install webdriver-manager
```

### 6. Run the backend
```bash
python3 app.py
```

### 7. Open the app
Go to **http://localhost:5000** in your browser.

---

## 📖 Usage

1. Describe your test in plain English
2. Choose your browser
3. Click **⚡ Generate & Run**
4. Watch the code get generated and executed in real time
5. See pass/fail results in the results panel

### Example prompts

```
Open Google, search for "Robot Framework", wait for results to load, then close the browser.
```

```
Go to https://the-internet.herokuapp.com/login, log in with username tomsmith
and password SuperSecretPassword!, verify the success message appears, then close.
```

---

## 🗂️ Project Structure

```
rf-testgen-v2/
├── app.py              # Flask backend — generates and runs tests
├── index.html          # Frontend UI
├── requirements.txt    # Python dependencies
├── .gitignore
└── README.md
```

---

## 🛠️ API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/generate` | POST | Generate .robot code from description |
| `/run` | POST | Run existing .robot code |
| `/generate-and-run` | POST | Generate and run in one step |

---

## ⚙️ Requirements

- Python 3.8+
- Ollama with Llama 3
- Robot Framework 6+
- SeleniumLibrary
- Chrome + ChromeDriver (or Firefox + GeckoDriver)
- 8GB RAM minimum

---

## 🤝 Contributing

Pull requests welcome! Ideas:
- [ ] Support more Ollama models (Mistral, Gemma, Phi3)
- [ ] Save and replay test history
- [ ] Export results as PDF report
- [ ] Page Object Model output option
- [ ] Support Playwright library

## 📄 License

MIT
