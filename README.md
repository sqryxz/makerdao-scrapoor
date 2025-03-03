# MakerDAO Governance Proposal Scraper

This tool scrapes MakerDAO's forum for new governance proposals, summarizes them using AI (DeepSeek), and posts updates to Discord.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Unix/macOS
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your configuration:
```
DEEPSEEK_API_KEY=your_api_key_here
DISCORD_WEBHOOK_URL=your_webhook_url_here
```

## Usage

Run the scraper:
```bash
python scraper.py
```

The tool will:
1. Scrape MakerDAO's forum for new governance proposals
2. Generate AI summaries using DeepSeek
3. Post updates to Discord via webhook 