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

## Commands

All commands use the `.` prefix (or `,` in debug mode).

### Similarity & Search Commands

- **`.sim <beatmap id/link> [filters] [page]`**
  - Find similar maps based on map structure
  - Example: `.sim 123456 ar<9 length>60`

- **`.sr <beatmap id/link> [dt] [page]`**
  - Find similar maps based on star rating
  - Example: `.sr 123456 dt`

- **`.slider <beatmap id/link> [page]`**
  - Find similar maps based on slider velocity/length
  - Example: `.slider 123456`

- **`.pp <min_pp> <max_pp> [mods_include] [mods_exclude] [filters] [page]`**
  - Find overweighted maps in a PP range
  - Example: `.pp 200 300 HDDT`
  - Example: `.pp 100 200 -EZ ar>9`

### Player Commands

- **`.rec [username]`**
  - Recommend a farm map based on user's top plays
  - Defaults to your Discord username if not specified
  - Example: `.rec mrekk`

- **`.farmer [username]`**
  - Calculate a user's farmer rating based on their top 100 plays
  - Shows most and least farm plays
  - Example: `.farmer mrekk`

### Quiz Commands

- **`.quiz_start [difficulty] [first] [guess_time] [length] [top_plays]`**
  - Start an interactive beatmap background quiz
  - `difficulty`: easy/medium/hard/impossible/iceberg (can combine)
  - `first`: first-guess scoring (true/false)
  - `guess_time`: seconds per question (default: 10)
  - `length`: number of questions (default: 10)
  - `top_plays`: comma-separated usernames to use maps from their top plays
  - Example: `.quiz_start hard 10 15`
  - Example: `.quiz_start easy true 15 20 mrekk,whitecat`

- **`.quiz_abort`**
  - Stop the currently running quiz in the channel

### Utility Commands

- **`.help`**
  - Display command list

- **`.invite`**
  - Get the bot invite link

### Available Filters

For `.sim` and `.pp` commands, you can filter results using these parameters:
- `ar`, `od`, `hp`, `cs` - Approach rate, overall difficulty, HP drain, circle size
- `length` - Map length in seconds
- `sr`, `star`, `stars` - Star rating
- `aim`, `aimsr` - Aim difficulty
- `tap`, `tapsr` - Tap/speed difficulty
- `id` - Beatmap ID
- `max_bpm` - Maximum BPM

**Operators:** `=`, `!=`, `>`, `<`, `>=`, `<=`

**Examples:**
- `ar<9` - AR less than 9
- `length>180` - Maps longer than 3 minutes
- `sr>=6.5` - 6.5+ star rating
- `ar>9.5 od>10` - Multiple filters

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
├── osu-tools/            # osu-tools submodule for star rating calculations
└── various similarity_*.py files  # Analysis modules
```

## Data Updates

To update the beatmap data and analysis files, run these scripts in order:

### Main Data Update Scripts:

1. **`python3 getmapids.py`** - Fetches beatmap IDs from osu! API
   - Outputs: `mapids_nodup.txt`
   - Use `--fast` flag for incremental updates (only new maps)

2. **`python3 getmaps.py`** - Downloads .osu beatmap files
   - Reads: `mapids_nodup.txt`
   - Outputs: `.osu` files in `maps/` directory
   - Use `--retry-failed` to retry failed downloads

3. **`python3 getstats.py`** - Extracts statistics from beatmap files
   - Reads: `.osu` files from `maps/`
   - Outputs: `stats.json`

4. **`python3 getdists.py`** - Calculates distance distributions
   - Reads: `.osu` files from `maps/`
   - Outputs: `.dist` files in `dists/` directory

### Optional Analysis Scripts:

- **`python3 getbuckets.py`** - Generate bucket analysis data
- **`python3 getmeans.py`** - Calculate mean values from distributions
- **`python3 getmedians.py`** - Calculate median values from distributions
- **`python3 getsrs.py`** - Extract star ratings (requires osu-tools setup)
- **`python3 getsliders.py`** - Extract slider patterns
- **`python3 getsliderstats.py`** - Calculate slider statistics

### Quick Update Commands:

```bash
# Full update
python3 getmapids.py
python3 getmaps.py
python3 getstats.py
python3 getdists.py

# Fast incremental update (new maps only)
python3 getmapids.py --fast
python3 getmaps.py
python3 getstats.py
python3 getdists.py
```

## osu-tools Setup (for Star Rating Calculations)

The project includes osu-tools as a submodule for calculating star ratings. Follow these steps to set it up:

### 1. Initialize and Update the Submodule

```bash
git submodule init
git submodule update
```

### 2. Install .NET SDK

osu-tools requires .NET SDK to build and run. Install .NET SDK 8.0 and .NET 5.0 runtime:

```bash
# Download and run the .NET install script
wget https://dot.net/v1/dotnet-install.sh -O dotnet-install.sh
chmod +x dotnet-install.sh

# Install .NET SDK 8.0
./dotnet-install.sh --channel 8.0

# Install .NET 5.0 runtime (required by osu-tools)
./dotnet-install.sh --channel 5.0 --runtime dotnet

# Add to PATH (add these lines to your ~/.bashrc or ~/.profile)
export PATH="$PATH:$HOME/.dotnet"
export DOTNET_ROOT="$HOME/.dotnet"

# Reload your shell configuration
source ~/.bashrc
```

### 3. Build osu-tools PerformanceCalculator

```bash
cd osu-tools/PerformanceCalculator
dotnet build -c Release
cd ../..
```

### 4. Verify Installation

Test that osu-tools is working correctly:

```bash
# Test with a beatmap file
cd osu-tools/PerformanceCalculator
dotnet run -- difficulty ../../maps/[beatmap_id].osu
```

You should see output showing star rating, aim rating, speed rating, and other difficulty statistics.

### 5. Generate Star Ratings (Optional)

Once osu-tools is set up, you can generate star ratings for all beatmaps. Note that this process can take a very long time for large beatmap collections:

```bash
# Generate star ratings using osu-tools
# This requires creating srs_raw_nm.txt first using osu-tools batch processing
# Consult osu-tools documentation for batch processing instructions
python3 getsrs.py
```

**Note:** The existing `srs.json`, `srs_dt.json`, and `srs_hr.json` files contain pre-calculated star ratings. You only need to regenerate these if you add many new beatmaps or if the star rating algorithm changes.

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