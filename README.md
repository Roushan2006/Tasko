# Tasko — AI Coding Agent

> An AI-powered software engineering agent that transforms a natural-language application request into a structured project plan, architecture, and working source code.

Tasko is an experimental AI coding agent built with **Python, LangGraph, LangChain, and OpenRouter**. It can analyze a user's software request, create an implementation plan, break the project into coding tasks, and use tools to create and modify project files.

---

## ✨ Features

* 🤖 AI-powered project planning
* 🏗️ Automatic software architecture generation
* 💻 Automated code generation
* 🛠️ Tool-based file creation and modification
* 📁 File reading and directory inspection
* 🔄 Multi-step coding workflow
* 🧠 Structured project planning with Pydantic models
* 🌐 OpenRouter-compatible LLM backend
* 🔁 Automatic retry handling for temporary API errors
* 🎨 Suitable for HTML, CSS, JavaScript and other application projects

---

## 🏛️ Architecture

Tasko follows a three-stage AI software development pipeline:

```text
                    User Request
                         │
                         ▼
                ┌─────────────────┐
                │     Planner     │
                │                 │
                │ Creates Project │
                │      Plan       │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │    Architect    │
                │                 │
                │ Creates Detailed│
                │    TaskPlan     │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │      Coder      │
                │                 │
                │ Uses Tools to   │
                │ Build the App   │
                └────────┬────────┘
                         │
                         ▼
                 Generated Project
```

---

## 🔄 How It Works

### 1. Planner

The Planner receives the user's request and creates a high-level project plan.

For example:

```text
Build a colourful modern calculator app
in HTML, CSS and JavaScript.
```

The Planner identifies:

* Project name
* Description
* Technology stack
* Features
* Required files

Example output:

```json
{
  "name": "calculator",
  "techstack": "HTML, CSS, JavaScript",
  "features": [
    "Modern UI",
    "Responsive design",
    "Calculator functionality"
  ],
  "files": [
    "index.html",
    "styles.css",
    "app.js"
  ]
}
```

---

### 2. Architect

The Architect converts the high-level Plan into a detailed implementation plan.

It determines:

* Implementation steps
* Target files
* Tasks for each file
* Project structure
* Required development sequence

The Architect output becomes the input for the Coder.

---

### 3. Coder

The Coder executes each implementation step.

It can use the following tools:

```text
read_file()
write_file()
list_files()
get_current_directory()
```

The Coder can:

1. Inspect existing files
2. Understand the current project
3. Generate code
4. Write code to files
5. Move to the next implementation task
6. Continue until the project is complete

---

## 🧰 Tech Stack

| Technology    | Purpose                             |
| ------------- | ----------------------------------- |
| Python        | Core application                    |
| LangGraph     | Agent workflow and state management |
| LangChain     | LLM integration                     |
| OpenRouter    | LLM API provider                    |
| Pydantic      | Data validation and project schemas |
| python-dotenv | Environment variable management     |
| HTML          | Frontend structure                  |
| CSS           | Styling                             |
| JavaScript    | Frontend functionality              |

---

## 📂 Project Structure

```text
Tasko/
│
├── agent/
│   └── graph.py
│
├── prompts.py
├── state.py
├── tools.py
│
├── .env
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```

### Main Files

#### `agent/graph.py`

Contains the LangGraph workflow:

```text
Planner → Architect → Coder
```

It also manages the OpenRouter model and retry handling.

#### `prompts.py`

Contains prompts used by the Planner, Architect, and Coder.

#### `state.py`

Contains the Pydantic models and state definitions used throughout the workflow.

#### `tools.py`

Contains the tools that allow the Coder to interact with the local project:

```text
read_file
write_file
list_files
get_current_directory
```

---

## 🚀 Installation

### Requirements

Make sure you have:

* Python 3.10+
* Git
* An OpenRouter API key
* `uv` package manager

---

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/Tasko.git
cd Tasko
```

---

### 2. Install dependencies

Using `uv`:

```bash
uv sync
```

Or add the required OpenRouter integration manually:

```bash
uv add langchain-openai
```

---

## 🔑 Environment Variables

Create a `.env` file in the project root:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
```

Never commit your `.env` file.

Your `.gitignore` should contain:

```gitignore
.env
.venv/
__pycache__/
*.pyc
```

---

## ▶️ Running Tasko

From the project root:

```bash
uv run python agent/graph.py
```

On Windows, you can also run:

```powershell
C:\Users\roush\.local\bin\uv.exe run C:/Users/roush/OneDrive/Desktop/Tasko/.venv/Scripts/python.exe C:\Users\roush\OneDrive\Desktop\Tasko\agent\graph.py
```

---

## 💡 Example

The current example request is:

```text
Build a colourful modern calculator app in html css and js
```

Tasko processes it as:

```text
User Request
     │
     ▼
Planner
     │
     ▼
Project Plan
     │
     ▼
Architect
     │
     ▼
Implementation Steps
     │
     ▼
Coder
     │
     ├── index.html
     ├── styles.css
     └── app.js
     │
     ▼
Completed Application
```

---

## 🛠️ Error Handling

Tasko includes retry handling for temporary API failures.

It can retry errors such as:

```text
429 Rate Limit
500 Server Error
502 Bad Gateway
503 Service Unavailable
504 Gateway Timeout
Timeout
```

The retry mechanism uses exponential backoff:

```text
1 second
2 seconds
4 seconds
8 seconds
...
```

This helps Tasko recover from temporary provider-side failures.

---

## 🔐 Security

**Never commit API keys or secrets.**

Do not add:

```text
.env
API keys
passwords
tokens
private credentials
```

to Git.

GitHub explicitly recommends avoiding committing sensitive information such as API keys and passwords.

If an API key has accidentally been pushed to GitHub, revoke/rotate it immediately.

---

## 🧪 Current Status

### Implemented

* [x] OpenRouter integration
* [x] Planner agent
* [x] Architect agent
* [x] Coder agent
* [x] LangGraph workflow
* [x] Pydantic validation
* [x] JSON extraction for LLM responses
* [x] File reading
* [x] File writing
* [x] Directory inspection
* [x] Retry handling
* [x] Multi-step implementation loop

### Future Improvements

* [ ] Web browsing / documentation search
* [ ] Automated testing agent
* [ ] Code review agent
* [ ] Git integration
* [ ] Automatic bug fixing
* [ ] Terminal execution tool
* [ ] Project preview
* [ ] Web UI
* [ ] Persistent project memory
* [ ] Human approval checkpoints
* [ ] Multiple LLM provider support

---

## 🎯 Roadmap

```text
Phase 1
│
├── Planner
├── Architect
└── Coder
        │
        ▼
Phase 2
│
├── Testing Agent
├── Code Review
└── Bug Fixing
        │
        ▼
Phase 3
│
├── Terminal Agent
├── Git Agent
└── Automated Development
        │
        ▼
Phase 4
│
└── Full AI Software Engineering Agent
```

---

## 🤝 Contributing

Contributions are welcome.

```bash
git checkout -b feature/your-feature
```

Make your changes, then:

```bash
git add .
git commit -m "Add your feature"
git push origin feature/your-feature
```

Then open a pull request.

---

## 📜 License

This project is currently intended for educational and experimental purposes.

Add an appropriate open-source license before distributing the project publicly.

---

## 👨‍💻 Author

**Roushan Kumar**

GitHub:

https://github.com/Roushan2006

---

## ⭐ Acknowledgements

Built using:

* LangGraph
* LangChain
* OpenRouter
* Pydantic
* Python

If you find this project useful, consider giving the repository a ⭐ on GitHub.
