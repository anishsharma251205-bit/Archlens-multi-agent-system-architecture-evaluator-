# 🏛️ ArchLens – Multi-Agent System Architecture Evaluator

> **An AI-powered system that evaluates software architectures using multiple specialized AI agents and provides intelligent feedback and architectural insights.**

---

## 📌 Overview

ArchLens is a Multi-Agent AI application that analyzes software system architectures using Large Language Models (LLMs). Instead of relying on a single AI response, the system employs multiple specialized agents, each focusing on a specific aspect of the architecture.

The agents collaborate to generate a comprehensive evaluation, helping developers identify design flaws, scalability concerns, security risks, and opportunities for improvement.

---

## ✨ Features

* 🤖 Multi-Agent Architecture Evaluation
* 🧠 LLM-powered Analysis
* 📊 Comprehensive Architecture Review
* 🏗️ Software Design Recommendations
* ⚡ Fast Response with Groq API
* 📋 Structured Evaluation Reports
* 🔍 Modular Agent-Based Design

---

## 🛠️ Tech Stack

* Python
* Streamlit
* Groq API
* Large Language Models (LLMs)
* Agent-Based Architecture
* Environment Variables (`.env`)

---

## 📂 Project Structure

```text
ArchLens/
│
├── archlens/
├── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/anishsharma251205-bit/Archlens-multi-agent-system-architecture-evaluator-.git

cd Archlens-multi-agent-system-architecture-evaluator-
```

### 2. Create a Virtual Environment

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root.

```env
GROQ_API_KEY=your_groq_api_key_here
```

> **Never commit your `.env` file to GitHub.**

### 5. Run the Application

```bash
streamlit run app.py
```

---

## ⚙️ How It Works

1. The user submits a software architecture or system design.
2. The input is sent to multiple specialized AI agents.
3. Each agent evaluates a different architectural aspect.
4. The responses are combined into a unified evaluation.
5. The application presents actionable insights and recommendations.

---

## 👨‍💻 Author

**Anish Sharma**

B.Tech Computer Science Engineering

GitHub: https://github.com/anishsharma251205-bit
