# Telegram Agent

A Python-based Telegram bot for controlling and managing your Windows computer remotely. Monitor system status, run commands, and manage files—all from Telegram on your phone.

## Features

- **Remote Command Execution**: Run predefined commands on your Windows machine via Telegram
- **AI-Powered Chat**: Ask questions and get responses using OpenRouter LLM integration
- **Safe File Editing**: Edit files with built-in diff preview and approval workflow
- **System Monitoring**: Check git status, run tests, list packages, and more
- **User-Restricted Access**: Only authorized user (via Telegram User ID) can access the bot

## Requirements

- Python 3.8+
- Windows OS with PowerShell
- Telegram Bot Token (create via [@BotFather](https://t.me/botfather))
- OpenRouter API Key (optional, for `/ask` command)

## Installation

### 1. Clone or Download the Project

```bash
git clone https://github.com/yourusername/telegram-agent.git
cd telegram-agent
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Set Environment Variables

Configure the following environment variables in PowerShell:

```powershell
[System.Environment]::SetEnvironmentVariable("TELEGRAM_BOT_TOKEN","<your-bot-token>","User")
[System.Environment]::SetEnvironmentVariable("TELEGRAM_USER_ID","<your-telegram-user-id>","User")
[System.Environment]::SetEnvironmentVariable("TELEGRAM_WORKSPACE","C:\Users\YourUsername\Projects","User")
[System.Environment]::SetEnvironmentVariable("OPENROUTER_API_KEY","<your-api-key>","User")
```

**Replace:**
- `<your-bot-token>`: Your Telegram Bot Token from [@BotFather](https://t.me/botfather)
- `<your-telegram-user-id>`: Your personal Telegram User ID (find it using [@userinfobot](https://t.me/userinfobot))
- `C:\Users\YourUsername\Projects`: Path to your workspace directory
- `<your-api-key>`: OpenRouter API key (optional)

### 4. Restart PowerShell

After setting environment variables, close and reopen PowerShell for changes to take effect.

## Usage

### Run the Bot

**Option 1: Direct Python**
```powershell
python telegram_agent.py
```

**Option 2: Using Batch File**
```powershell
start_telegram.bat
```

**Option 3: Silent Mode (Hidden Window)**
```powershell
cscript.exe start_telegram_silent.vbs
```

## Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/help` | Show all available commands | `/help` |
| `/ask <question>` | Ask the AI (OpenRouter LLM) | `/ask what is Python?` |
| `/run status` | Get git status | `/run status` |
| `/run tests` | Run pytest | `/run tests` |
| `/run pip_list` | List installed packages | `/run pip_list` |
| `/run pwd` | Get current directory | `/run pwd` |
| `/run workspace` | Get workspace path | `/run workspace` |

## File Editing

Edit files safely with built-in approval workflow:

1. Send a message to the bot in this format:

```
edit path/to/file.json
<<<
{
  "new": "content",
  "here": true
}
>>>
```

2. The bot will:
   - Show you a **diff** of the changes
   - Display "Approve" and "Cancel" buttons
   - Only apply changes after your approval

3. Approve or cancel the edit via the buttons

## File Structure

```
telegram-agent/
├── telegram_agent.py          # Main bot logic
├── requirements.txt           # Python dependencies
├── start_telegram.bat         # Windows batch launcher
├── start_telegram_silent.vbs  # Silent mode launcher
└── README.md                  # This file
```

## Configuration

The bot reads the following environment variables:

- `TELEGRAM_BOT_TOKEN` - Your Telegram Bot Token (required)
- `TELEGRAM_USER_ID` - Your Telegram User ID (required)
- `TELEGRAM_WORKSPACE` - Working directory for commands (defaults to current directory)
- `OPENROUTER_API_KEY` - API key for `/ask` command (optional)

## Security Considerations

- **User-Restricted**: Only your Telegram User ID can access the bot
- **Command Whitelist**: Only predefined commands can be executed
- **Approval Required**: File edits require explicit approval before applying
- **Output Limits**: Large command outputs are truncated for safety (3500 characters max)
- **Timeout Protection**: Commands timeout after 5 minutes

## Troubleshooting

### Bot doesn't respond
- Verify `TELEGRAM_BOT_TOKEN` is correct
- Verify bot is running (`python telegram_agent.py`)
- Ensure firewall allows outbound connections

### Commands fail
- Check `TELEGRAM_WORKSPACE` exists
- Verify PowerShell can execute commands in that directory
- Check command timeout (5 minutes max)

### "User not allowed" error
- Verify `TELEGRAM_USER_ID` matches your actual Telegram ID
- Use [@userinfobot](https://t.me/userinfobot) to find your ID

## Dependencies

- `python-telegram-bot>=20.6` - Telegram Bot API wrapper
- `requests>=2.31.0` - HTTP library for API calls

## Future Enhancements

- [ ] Support for file uploads through Telegram
- [ ] Scheduled tasks and notifications
- [ ] Multi-user support
- [ ] Command output streaming for long-running tasks
- [ ] Database for command history

## License

This project is provided as-is. Feel free to modify and distribute.

## Author

Created as a utility for remote Windows management via Telegram.

---

**For questions or issues**, feel free to open an issue on GitHub.
