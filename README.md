# RF TestGen v2 🤖

An AI-powered Robot Framework test case generator **and runner**. Describe your test in plain English — the app scrapes the real page, understands your intent, matches real locators, and executes the test automatically.

Runs completely **free and offline** using [Ollama](https://ollama.com) with Llama 3. No API key needed.

---

## ✨ How It Works

```
You describe test in plain English
           ↓
Selenium scrapes the real page (handles JS sites)
           ↓
Llama 3 parses your intent → returns JSON steps
           ↓
Llama 3 matches each step to real scraped locators
           ↓
Our code builds 100% valid Robot Framework
           ↓
Robot Framework runs the test in Chrome
           ↓
Pass/Fail results shown in the UI
```

No guessed locators. No invented keywords. Works on any website.

---

## ✨ Features

- **Plain English → Robot Framework** — no syntax knowledge needed
- **Real page scraping** — uses headless Chrome to handle JavaScript sites
- **Smart locator matching** — Llama matches your intent to real page elements
- **Actually runs the tests** — executes and shows pass/fail results
- **100% free and offline** — powered by Ollama + Llama 3
- **Works on any website** — scrapes locators dynamically
- **Known sites support** — Google, the-internet, demoqa work out of the box

---

## 🚀 Setup

### 1. Clone the repo
```bash
git clone https://github.com/tanishq2905/rf-testgen-v2.git
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

### 5. Install Chrome
```bash
sudo apt install google-chrome-stable -y
```

### 6. Run the backend
```bash
python3 app.py
```

### 7. Open the app
Go to **http://localhost:5000**

---

## 📖 Usage

1. Describe your test in plain English — include the URL
2. Choose your browser
3. Click **⚡ Generate & Run**
4. Watch the terminal as it scrapes, parses and builds
5. See pass/fail results in the UI

### Example prompts

```
Go to https://www.google.com, search for Robot Framework tutorial,
wait for results to load, then close the browser.
```

```
Go to https://the-internet.herokuapp.com/login, log in with
username tomsmith and password SuperSecretPassword!,
verify the success message appears, then close.
```

```
Open https://demoqa.com/text-box, fill Full Name with Test User,
Email with test@example.com, click Submit,
verify the output section appears, then close.
```

---

## 🗂️ Project Structure

```
rf-testgen-v2/
├── app.py              # Flask backend
│                         - Selenium page scraper
│                         - Llama intent parser
│                         - Llama locator matcher
│                         - Robot Framework builder
│                         - Test runner
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
| `/status` | GET | Check if Ollama is running |

---

## ⚙️ Requirements

- Python 3.8+
- Ollama with Llama 3 (~4GB)
- Robot Framework 6+
- SeleniumLibrary
- Google Chrome
- 8GB RAM minimum

---

## 🤝 Contributing

Pull requests welcome! Ideas:
- [ ] Add more known sites to KNOWN_SITES dict
- [ ] Support Firefox and Edge scraping
- [ ] Save and replay test history
- [ ] Export results as PDF report
- [ ] Add credentials input form in UI
- [ ] Support Playwright library

## 📄 License

MIT
