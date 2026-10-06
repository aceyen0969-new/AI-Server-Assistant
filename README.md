Quasar

«AI-powered Discord server assistant with automated moderation, secure server actions, AI provider fallback, and human approval workflows.»

Quasar is a modular Discord bot designed to combine AI assistance with traditional deterministic server management.

Instead of allowing an AI model to directly control a Discord server, Quasar places a security and policy layer between AI decisions and real Discord actions.

✨ Features

🤖 AI Assistant

- Multi-provider AI support
- Automatic provider fallback
- Provider health tracking
- Provider-specific timeouts
- Conversation memory
- Long-response handling

Current provider chain:

Gemini
   ↓
Claude
   ↓
OpenRouter
   ↓
Groq

If a provider becomes unavailable, Quasar can automatically move to the next available provider.

🛡️ Automatic Moderation

Quasar includes a rule-based spam detection and escalation system.

Current escalation:

1st violation → Delete message
2nd violation → Delete + Warning
3rd+ violation → Timeout

The system also includes violation decay, allowing old violations to eventually stop affecting a user's escalation level.

🔐 Security & Approval System

AI-generated actions never directly execute against the server.

Quasar uses:

AI Decision
     ↓
Security Policy
     ↓
Automatic Action
     OR
Owner Approval
     ↓
Discord Action

Sensitive actions such as:

- Moving channels
- Creating channels
- Renaming channels
- Kicking members
- Banning members
- Deleting channels
- Managing roles
- Changing permissions

require approval.

Lower-risk actions can be executed automatically when permitted by the security policy.

🧹 Channel Cleanup

Quasar provides a "/cleanup" command with:

- Delete a specified number of recent messages
- Delete all accessible messages
- Permission checks
- Confirmation before deletion
- Confirmation timeout
- Cancellation support
- Error handling

Example:

/cleanup amount:50

or:

/cleanup delete_all:true

📊 Server Tools

Quasar also provides server information and management utilities, including:

- Server information
- Server statistics
- Channel information
- AI provider status
- Server organization

🧠 Architecture

Quasar is designed around separate modules instead of putting all functionality inside one large bot file.

AI-Server-Assistant/
│
├── main.py
│
├── ai/
│   ├── assistant.py
│   ├── manager.py
│   ├── providers.py
│   └── health.py
│
├── commands/
│   ├── ping.py
│   ├── serverinfo.py
│   ├── serverstats.py
│   ├── channels.py
│   ├── organize.py
│   ├── cleanup.py
│   └── aistatus.py
│
├── security/
│   ├── policies.py
│   ├── actions.py
│   ├── approval.py
│   └── approval_view.py
│
├── moderation/
│   ├── detector.py
│   ├── moderator.py
│   └── violations.py
│
└── utils/

The goal is to keep individual systems isolated so they can be tested, improved, and extended independently.

🔒 Security Philosophy

Quasar follows a simple principle:

«The AI can suggest an action. It does not get to decide whether that action is safe.»

The AI layer produces decisions, while Python-controlled policies determine what Quasar is actually allowed to execute.

This prevents the language model from directly controlling sensitive Discord operations.

🔄 AI Provider Fallback

AI providers can fail for many reasons, including:

- Rate limits
- API errors
- Timeouts
- Temporary outages
- Account limitations

Quasar tracks provider health and uses fallback providers when necessary.

Example:

User
 ↓
Quasar AI Manager
 ↓
Gemini
 ↓ failure
Claude
 ↓ failure
OpenRouter
 ↓
Response

Provider-specific timeouts prevent one slow provider from blocking the entire AI system.

🛠️ Technology

- Python
- discord.py
- Google Gemini
- Anthropic Claude
- OpenRouter
- Groq
- python-dotenv
- Discord Interactions / Slash Commands

🚀 Running Locally

Clone the repository:

git clone https://github.com/aceyen0969-new/AI-Server-Assistant.git
cd AI-Server-Assistant

Install dependencies:

pip install -r requirements.txt

Create a ".env" file containing your required credentials:

DISCORD_TOKEN=your_discord_token

Add the API keys for the AI providers you intend to use.

Then start Quasar:

python main.py

⚠️ Security

Never commit ".env" files, Discord bot tokens, or AI API keys to GitHub.

Keep credentials in environment variables.

📌 Project Status

Quasar is an actively developed project.

Current development focuses on:

- Cloud deployment
- Reliability
- Security improvements
- AI provider management
- Moderation improvements
- Server management automation
- Better logging and observability

🎯 Future Goals

Planned improvements include:

- Persistent database storage
- Persistent approval requests
- More advanced audit logging
- Configurable moderation policies
- Better AI action planning
- Dashboard / web interface
- More Discord management tools
- Improved provider monitoring
- Cloud deployment

👨‍💻 Author

Built by aceyen0969 as a learning and portfolio project focused on:

- Python development
- AI systems
- Discord bot development
- API integration
- Security architecture
- Automation
- Software architecture

---

⭐ If you find the project interesting, consider starring the repository.