# Quasar

**An AI-powered Discord server assistant built around intelligent automation, controlled server actions, and modular AI systems.**

Quasar is a modular Discord assistant that combines AI-powered reasoning with deterministic server management. It is designed to separate AI-generated decisions from the execution of sensitive Discord actions, providing a foundation for safer automation, policy enforcement, and human oversight.

The project is actively evolving, with ongoing development in analytics, multilingual language detection, conflict detection, provider reliability, and persistent state.

## Features

### 1. AI Provider Management

Quasar integrates with multiple AI providers to support flexible model access.

Configured provider integrations include:

* Google Gemini
* OpenAI
* Groq
* Anthropic Claude

The AI subsystem includes provider routing, health tracking, and assistant management modules. Actual provider availability depends on configuration, API access, and implementation status.

### 2. Automated Moderation

Quasar includes a modular moderation system designed to detect inappropriate messages and manage repeated violations.

Its moderation components include:

* Message detection
* Moderation handling
* Violation tracking
* Warning and escalation logic

Moderation behavior should be tested in a controlled Discord server before being relied on in a production community.

### 3. Analytics and Reporting

Quasar includes an analytics subsystem for processing server activity and producing reports.

Its modules cover:

* Message observation
* Analytics analysis
* Database management
* Report generation
* Scheduled analytics
* Objective-related workflows

### 4. Multilingual Language Detection

Quasar includes a language engine and a separate conflict-detection module.

The language engine is being developed around English, Filipino, Bisaya, and mixed-language messages, including Taglish and code-switching.

The conflict detector analyzes messages for patterns associated with:

* Possible conflict escalation
* De-escalation
* Past conflict
* Conflict avoidance

These classifications are heuristic signals, not definitive judgments about a person's intentions. Context, sarcasm, slang, and mixed-language expressions can affect accuracy.

### 5. Controlled Server Actions

Quasar includes modules for planning actions, executing actions, enforcing security policies, and requesting approval.

The intended architecture separates action planning from execution so that sensitive operations can be checked against permissions and approval requirements.

The effectiveness of these safeguards depends on the actual enforcement logic and must be verified through testing.

### 6. Learning Components

Quasar contains modules for learning candidates and vocabulary learning.

These components provide a foundation for improving language recognition over time. Any learned data should be validated before it is allowed to influence important moderation or security decisions.

### 7. Discord Commands

The project includes command modules for features such as:

* AI status
* Server information and statistics
* Channel management
* Server organization
* Cleanup
* Analytics
* Objectives
* Approval testing

The available commands depend on successful loading, configuration, Discord permissions, and application behavior.

## Project Structure

```text
Quasar/
├── ai/
│   ├── action_executor.py
│   ├── action_planner.py
│   ├── assistant.py
│   ├── health.py
│   ├── learning_candidates.py
│   ├── manager.py
│   ├── providers.py
│   ├── provider_router.py
│   └── vocabulary_learner.py
├── analytics/
│   ├── analyzer.py
│   ├── database.py
│   ├── display.py
│   ├── objectives.py
│   ├── observer.py
│   ├── proposals.py
│   ├── reporter.py
│   └── scheduler.py
├── commands/
├── conflict_detection/
├── language_engine/
├── moderation/
├── security/
├── utils/
├── main.py
├── requirements.txt
└── README.md
```

## Technology Stack

* Python
* discord.py
* Google Gemini API
* OpenAI API
* Groq API
* Anthropic API
* SQLite or another database backend, depending on the database implementation
* Python dotenv for environment configuration

The repository also contains a C++ language-engine component under development. Its build process and integration requirements may differ from those of the Python application.

## Requirements

* Python compatible with the installed dependencies
* A Discord bot application and token
* API credentials for whichever AI providers you intend to use
* Git for version control

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/aceyen0969-new/AI-Server-Assistant.git
cd AI-Server-Assistant
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root.

Example:

```dotenv
DISCORD_TOKEN=your_discord_bot_token
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

Use the exact variable names expected by the current provider implementation. Not every provider needs to be configured.

**Security:** Never commit `.env`, API keys, bot tokens, or other secrets to GitHub.

### 5. Configure Discord permissions

Enable the privileged gateway intents required by your bot in the Discord Developer Portal, including Message Content Intent and Server Members Intent when needed.

Grant only the Discord permissions required by the features you intend to use.

### 6. Start Quasar

```bash
python main.py
```

Review the console output for startup errors, provider issues, command synchronization problems, and analytics scheduler status.

## Development and Testing

Run the conflict detector's existing test script:

```bash
python test_conflict_detector.py
```

Check Python syntax for the main application and conflict detector:

```bash
python -m py_compile main.py conflict_detection\detector.py test_conflict_detector.py
```

These checks help identify syntax problems, but passing them does not prove that every feature works correctly. Integration tests and controlled Discord testing are still necessary.

## Development Roadmap

Potential development priorities include:

* Improve English, Filipino, Bisaya, and Taglish detection.
* Connect language detection and conflict signals through a consistent analysis pipeline.
* Reduce false positives in conflict classification.
* Audit AI provider fallback and health tracking.
* Verify security policies and approval workflows.
* Improve persistence and lifecycle management for objectives.
* Expand automated testing and error handling.
* Document verified behavior and known limitations.

## Project Status

**Quasar is a work in progress.**

The repository contains multiple AI, moderation, analytics, language-processing, and security modules. Their individual features and integration points are being audited and tested as development continues.

## Author

Developed by **aceyen0969-new**.

GitHub repository: https://github.com/aceyen0969-new/AI-Server-Assistant

## License

No license has been specified in this README. Check the repository for an existing license before choosing or adding one.
