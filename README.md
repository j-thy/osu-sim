# osu-sim Discord Bot

A Discord bot for osu! beatmap similarity created by SourMongoose.

## Setup

### Prerequisites
- Python 3.8+
- osu! API credentials
- Discord Bot token

### Installation

1. Clone the repository:
```bash
git clone https://github.com/j-thy/osu-sim.git
cd osu-sim
```

2. Create a virtual environment:
```bash
python3 -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Configuration

#### 1. osu! API Credentials

Create a `secret.py` file with your osu! API credentials:

```python
# osu! API credentials
client_id = 'YOUR_CLIENT_ID_HERE'
client_secret = 'YOUR_CLIENT_SECRET_HERE'
```

To get these credentials:
1. Go to https://osu.ppy.sh/home/account/edit#oauth
2. Create a new OAuth application
3. Copy the Client ID and Client Secret

#### 2. Discord Bot Token

Create a `tokens.py` file with your Discord bot token:

```python
# Discord bot token
token = 'YOUR_DISCORD_BOT_TOKEN_HERE'
beta_token = 'YOUR_DISCORD_BOT_TOKEN_HERE'  # Can be same as token for testing
```

To get a Discord bot token:
1. Go to https://discord.com/developers/applications
2. Create a new application or select existing one
3. Go to the Bot section
4. Copy the token

#### 3. Discord Bot Permissions

When adding the bot to your server, ensure these permissions are enabled:

**Required Permissions:**
- Send Messages (2048)
- Embed Links (16384)

**Required Intents:**
- Message Content Intent (enable in Discord Developer Portal under Bot settings)

Use this invite link format:
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_CLIENT_ID&permissions=18432&scope=bot
```

## Running the Bot

```bash
python3 bot.py
```

For background execution:
```bash
python3 bot.py &
# Or use screen/tmux for persistent sessions
```

## Features

- Player statistics lookup
- PP (Performance Points) map recommendations
- Similarity analysis for:
  - Beatmap buckets
  - Slider patterns
  - Star ratings
- Interactive quizzes and games

## Project Structure

```
osu-sim/
├── bot.py                  # Main Discord bot file
├── api.py                  # osu! API interface
├── secret.py              # osu! API credentials (not in git)
├── tokens.py              # Discord bot tokens (not in git)
├── requirements.txt       # Python dependencies
├── maps/                  # Beatmap data storage
├── buckets/              # Bucket analysis data
├── sliders/              # Slider pattern data
├── dists/                # Distribution data
└── various similarity_*.py files  # Analysis modules
```

## Troubleshooting

### ModuleNotFoundError: No module named 'discord'
Make sure you have py-cord installed, not discord.py:
```bash
pip uninstall discord discord.py -y
pip install py-cord==2.6.1
```

### Bot not responding to commands
- Check that Message Content Intent is enabled in Discord Developer Portal
- Verify the bot has proper permissions in your server
- Check that the bot is online (green status in Discord)

### API rate limiting
The osu! API has rate limits. If you encounter issues, check your API usage at https://osu.ppy.sh/home/account/edit#oauth

## Debug Mode

To run in debug mode, set `DEBUG = True` in bot.py line 20. This will use the beta_token instead of the main token.

## License

[Add your license here]

## Contributing

[Add contribution guidelines if applicable]