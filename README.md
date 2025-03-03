# AAVE Governance Proposal Scraper

A Python-based scraper that monitors AAVE's governance forum for new development proposals and sends notifications to Discord.

## Features

- Scrapes AAVE's development forum for governance proposals
- Identifies proposals using key terms (ARFC, AIP, temp check, etc.)
- Generates AI-powered summaries of proposals using DeepSeek
- Sends formatted notifications to Discord with proposal details
- Caches processed proposals to avoid duplicates
- Configurable limit on number of proposals to fetch (default: 5)

## Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`
- Discord webhook URL for notifications
- DeepSeek API key for proposal summarization

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/governance-proposal-scraper.git
cd governance-proposal-scraper
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your configuration:
```env
DISCORD_WEBHOOK_URL=your_discord_webhook_url
DEEPSEEK_API_KEY=your_deepseek_api_key
```

## Usage

Run the scraper in test mode:
```bash
python scraper.py
```

The scraper will:
1. Fetch the latest topics from AAVE's development forum
2. Identify governance proposals based on content
3. Generate summaries using DeepSeek's AI
4. Send notifications to Discord (if configured)
5. Cache processed proposals to avoid duplicates

## Configuration

- `FORUM_BASE_URL`: Base URL of the AAVE governance forum
- `GOVERNANCE_PATH`: Path to the development category
- `CACHE_FILE`: Location of the processed proposals cache
- Environment variables in `.env`:
  - `DISCORD_WEBHOOK_URL`: Discord webhook for notifications
  - `DEEPSEEK_API_KEY`: DeepSeek API key for AI summaries

## Output Format

Discord notifications include:
- Proposal title and summary
- Proposal ID
- Creation timestamp
- Forum link
- AAVE purple branding

## Development

The scraper uses:
- `requests` and `BeautifulSoup4` for web scraping
- `discord-webhook` for Discord integration
- `openai` SDK configured for DeepSeek API
- `python-dotenv` for configuration management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - feel free to use and modify as needed.

## Acknowledgments

- AAVE Governance Forum
- DeepSeek API for AI summaries
- Discord for notifications 