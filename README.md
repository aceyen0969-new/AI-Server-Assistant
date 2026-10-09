# Quasar

**An AI-powered Discord server assistant built around intelligent automation, controlled server actions, and modular AI systems.**

Quasar is a modular Discord assistant that combines AI-powered reasoning with deterministic server management. Its architecture is designed to keep AI-generated decisions separate from the execution of sensitive Discord actions, providing a foundation for safer automation and human oversight.

The project is actively evolving, with ongoing work on analytics, multilingual conflict detection, reliability, and persistent state.

## ✨ Features

### 🤖 AI Provider Management

Quasar integrates with multiple AI providers to support flexible model access and provider failover.

Providers configured in the project include:

* Google Gemini
* Anthropic Claude
* OpenRouter
* Groq
* OpenAI integration code

The project includes provider-management functionality such as:

* Multi-provider support
* Automatic provider fallback
* Provider health tracking
* Provider-specific timeouts
* Conversation memory
* Long-response handling

**Provider availability and fallback behavior depend on configuration and successful integration.** Not every provider or capability has been independently verified in the current development state.

### 🛡️ Automated Moderation

Quasar includes rule-based moderation designed to detect spam and escalate repeated violations.

The documented escalation policy is:

| Violation                     | Action                             |
| ----------------------------- | ---------------------------------- |
| First violation               | Delete message                     |
| Second violation              | Delete message and issue a warning |
| Third or subsequent violation | Apply a timeout                    |

The moderation system also includes violation decay, allowing older violations to stop contributing to a user's escalation level over time.

Actual enforcement depends on Discord permissions, bot configuration, and the relevant implementation.

### 📊 Analytics Scheduler

Quasar includes an analytics scheduler that can run analysis through an AI provider.

A recent development test completed an analytics operation using Groq.

Current development focuses on making analytics more reliable, improving observability, and connecting analysis outputs to the wider assistant architecture.

### 🌐 Multilingual Conflict Detection

Quasar is developing a lightweight conflict-language detection component for English, Filipino, and Bisaya.

The detector currently recognizes patterns associated with four categories:

* **Possible escalation:** language that may indicate escalating conflict.
* **De-escalation:** language intended to calm a disagreement or stop a conflict.
* **Past conflict:** references to conflicts that have already occurred.
* **Conflict avoidance:** language expressing a desire not to engage in conflict.

Example inputs include:

| Example                     | Detected category   |
| --------------------------- | ------------------- |
| `Come fight me.`            | Possible escalation |
| `Wag kayong mag-away.`      | De-escalation       |
| `Nag-away sila kahapon.`    | Past conflict       |
| `Ayoko makipag-away.`       | Conflict avoidance  |
| `Dili ko gusto makig-away.` | Conflict avoidance  |

These examples demonstrate initial pattern detection, not comprehensive language understanding. The component is still being tested for ambiguous wording, mixed-language messages, contextual meaning, and false positives.

A detected signal is not proof of a person's intent or that a real conflict is occurring.

## 🏗️ Architecture and Design Principles

Quasar is designed around modular components that separate responsibilities.

Its core design goals include:

* **Modularity:** Keep AI providers and functional components organized into separate modules.
* **Controlled execution:** Separate AI-generated decisions from sensitive server actions.
* **Reliability:** Support provider fallback and timeout handling.
* **Deterministic moderation:** Use explicit rules for moderation and escalation.
* **Observability:** Improve logging and visibility into system behavior.
* **Extensibility:** Make it easier to introduce new analysis components and server-management capabilities.

The architecture and individual integrations are evolving as development progresses.

## 🧰 Technology Stack

* Python
* discord.py
* Google Gemini
* Anthropic Claude
* OpenRouter
* Groq
* OpenAI API integration
* python-dotenv
* Discord interactions and slash commands

Some dependencies and integrations may be optional depending on the configured features.

## 🚀 Getting Started

### Prerequisites

* Python installed on your system
* A Discord application and bot token
* Access to any AI providers you intend to use
* Git

### 1. Clone the repository

```bash
git clone https://github.com/aceyen0969-new/AI-Server-Assistant.git
cd AI-Server-Assistant
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root and add the credentials required by your configuration.

```dotenv
DISCORD_TOKEN=your_discord_bot_token

GEMINI_API_KEY=your_gemini_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key
```

Only configure the credentials required by the providers you intend to use. Check the source code for the exact environment-variable names and any additional configuration requirements.

### 4. Start Quasar

```bash
python main.py
```

The application will start according to the configured entry point and available credentials.

### 5. Run the conflict detector tests

The initial conflict detector tests can be run with:

```bash
python -m py_compile main.py conflict_detection/detector.py test_conflict_detector.py

python test_conflict_detector.py
```

These commands check Python syntax and execute the current detector test cases. They do not constitute a complete test suite for the entire project.

## 🔐 Security

Security is a core design consideration for Quasar.

* Never commit `.env` files, API keys, bot tokens, or other secrets.
* Store credentials in environment variables.
* Give the Discord bot only the permissions it needs.
* Validate and constrain sensitive server actions.
* Keep AI-generated recommendations separate from privileged operations.
* Review logs to ensure they do not expose credentials or sensitive information.

Before publishing changes, inspect staged files for accidentally included secrets.

## 🗺️ Roadmap

Planned and ongoing development includes:

* [ ] Improve AI provider reliability and monitoring.
* [ ] Expand analytics and scheduling capabilities.
* [ ] Improve multilingual conflict detection.
* [ ] Handle contextual meaning and mixed-language messages.
* [ ] Integrate conflict analysis with the broader assistant architecture.
* [ ] Develop and verify persistent objective tracking.
* [ ] Improve audit logging and observability.
* [ ] Expand configurable moderation policies.
* [ ] Strengthen approval workflows for sensitive actions.
* [ ] Investigate persistent database storage.
* [ ] Explore a web dashboard and additional Discord management tools.
* [ ] Evaluate cloud deployment options.

Roadmap items may change as the project develops.

## 📌 Project Status

Quasar is an actively developed learning and portfolio project.

Existing modules cover AI provider integration, Discord moderation, and analytics. Multilingual conflict detection is undergoing initial testing, while broader integration, reliability, and persistence remain areas for continued development.

Feature availability should be assessed against the current source code and tests rather than the roadmap alone.

## 👨‍💻 Author

Built by **aceyen0969** as a learning and portfolio project focused on:

* Python development
* AI systems and provider integration
* Discord bot development
* Automation and analytics
* Security-conscious software architecture
* Multilingual text analysis

## 📄 License

No license has been specified in this README. Check the repository for an existing license before choosing or adding one.

---

*Quasar is a work in progress. Contributions, testing, and architectural improvements are part of its ongoing development.*
