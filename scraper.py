import os
import json
from datetime import datetime
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
from discord_webhook import DiscordWebhook, DiscordEmbed
import deepseek

# Load environment variables
load_dotenv()

# Constants
FORUM_URL = "https://forum.sky.money/c/governance/5/l/latest.json"
PROPOSAL_BASE_URL = "https://forum.sky.money/t/"
CACHE_FILE = "processed_proposals.json"

class MakerDAOScraper:
    def __init__(self):
        self.discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.processed_proposals = self.load_processed_proposals()

    def load_processed_proposals(self):
        """Load previously processed proposals from cache file."""
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        return []

    def save_processed_proposals(self):
        """Save processed proposals to cache file."""
        with open(CACHE_FILE, 'w') as f:
            json.dump(self.processed_proposals, f)

    def fetch_proposals(self):
        """Fetch new governance proposals from MakerDAO forum."""
        try:
            response = requests.get(FORUM_URL)
            response.raise_for_status()
            data = response.json()
            
            # Filter for governance proposals
            topics = data.get('topic_list', {}).get('topics', [])
            governance_proposals = [
                topic for topic in topics
                if "Executive Vote" in topic.get('title', '') or 
                   "Poll" in topic.get('title', '')
            ]
            
            return governance_proposals
        except requests.RequestException as e:
            print(f"Error fetching proposals: {e}")
            return []

    def get_proposal_content(self, topic_id):
        """Fetch the full content of a proposal."""
        url = f"{PROPOSAL_BASE_URL}{topic_id}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract the main post content
            post_content = soup.find('div', class_='post')
            if post_content:
                return post_content.get_text(strip=True)
            return ""
        except requests.RequestException as e:
            print(f"Error fetching proposal content: {e}")
            return ""

    def summarize_proposal(self, content):
        """Generate an AI summary of the proposal using DeepSeek."""
        try:
            client = deepseek.Client(api_key=self.deepseek_api_key)
            prompt = f"""Please provide a concise summary of the following MakerDAO governance proposal. 
            Focus on the key points, impact, and any voting details:

            {content[:4000]}  # Limit content length for API
            """
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "Error generating summary"

    def send_discord_notification(self, proposal, summary):
        """Send a notification to Discord with the proposal summary."""
        try:
            webhook = DiscordWebhook(url=self.discord_webhook_url)
            
            embed = DiscordEmbed(
                title=proposal['title'],
                description=summary,
                color=0x00ff00
            )
            
            embed.add_embed_field(
                name="Link",
                value=f"{PROPOSAL_BASE_URL}{proposal['id']}"
            )
            embed.add_embed_field(
                name="Posted",
                value=datetime.fromtimestamp(proposal['created_at']).strftime('%Y-%m-%d %H:%M:%S')
            )
            
            webhook.add_embed(embed)
            webhook.execute()
        except Exception as e:
            print(f"Error sending Discord notification: {e}")

    def run(self):
        """Main execution flow."""
        print("Fetching new proposals...")
        proposals = self.fetch_proposals()
        
        for proposal in proposals:
            if proposal['id'] not in self.processed_proposals:
                print(f"Processing new proposal: {proposal['title']}")
                
                # Fetch full content
                content = self.get_proposal_content(proposal['id'])
                
                # Generate summary
                summary = self.summarize_proposal(content)
                
                # Send Discord notification
                self.send_discord_notification(proposal, summary)
                
                # Mark as processed
                self.processed_proposals.append(proposal['id'])
                self.save_processed_proposals()
                
                print(f"Processed proposal {proposal['id']}")

if __name__ == "__main__":
    scraper = MakerDAOScraper()
    scraper.run() 