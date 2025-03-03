import os
import json
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
from discord_webhook import DiscordWebhook, DiscordEmbed
from openai import OpenAI

# Load environment variables
load_dotenv()

# Constants
FORUM_BASE_URL = "https://governance.aave.com"
GOVERNANCE_PATH = "/c/development/26"
FORUM_URL = urljoin(FORUM_BASE_URL, GOVERNANCE_PATH)
PROPOSAL_BASE_URL = urljoin(FORUM_BASE_URL, "/t/")
CACHE_FILE = "processed_proposals.json"

# Browser-like headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Host': urlparse(FORUM_BASE_URL).netloc,
    'Origin': FORUM_BASE_URL,
    'Referer': FORUM_BASE_URL,
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
}

# Test data
TEST_PROPOSAL = {
    'id': 'test-1',
    'title': 'Test Governance Proposal: Treasury Allocation',
    'created_at': datetime.now().timestamp()
}

TEST_CONTENT = """
Governance Proposal: Treasury Allocation for Q1 2024

Executive Summary:
This proposal suggests allocating 1,000,000 SKY tokens from the treasury for ecosystem development in Q1 2024.

Background:
The Sky Money ecosystem requires continuous development and growth initiatives. The current treasury holds 5,000,000 SKY tokens available for ecosystem development.

Proposal Details:
1. Allocate 400,000 SKY for developer grants
2. Allocate 300,000 SKY for liquidity mining programs
3. Allocate 200,000 SKY for marketing initiatives
4. Reserve 100,000 SKY for emergency operations

Implementation Timeline:
- Immediate release upon proposal approval
- Programs to run through Q1 2024 (January - March)

Voting Details:
- Voting Period: 7 days
- Quorum Required: 10% of total SKY staked
- Approval Threshold: 66% majority

Please cast your vote and provide any feedback in the comments section.
"""

class AaveForumScraper:
    def __init__(self):
        self.discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.processed_proposals = self.load_processed_proposals()
        
        # Initialize OpenAI client with DeepSeek configuration
        self.ai_client = OpenAI(
            api_key=self.deepseek_api_key,
            base_url="https://api.deepseek.com/v1"
        )

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
        """Fetch new governance proposals from forum."""
        try:
            print(f"Fetching proposals from: {FORUM_URL}")
            print(f"Using headers: {HEADERS}")
            
            response = requests.get(FORUM_URL, headers=HEADERS, allow_redirects=True)
            print(f"Initial request URL: {response.request.url}")
            if response.history:
                print("Redirect history:")
                for r in response.history:
                    print(f"  {r.status_code}: {r.url} -> {r.headers.get('Location')}")
            print(f"Final URL: {response.url}\n")
            
            response.raise_for_status()
            print("Response received successfully")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all topic rows - use a more general selector
            topics = soup.select('tr.topic-list-item')
            print(f"\nFound {len(topics)} total topics")
            
            governance_proposals = []
            for topic in topics:
                try:
                    # Stop if we've found 5 proposals
                    if len(governance_proposals) >= 5:
                        print("\nReached 5 proposals limit, stopping...")
                        break
                        
                    # Extract title and link - use more general selectors
                    title_elem = topic.select_one('a.title')
                    if not title_elem:
                        print("No title element found for topic")
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    topic_url = title_elem.get('href')
                    if not topic_url:
                        print(f"No URL found for topic: {title}")
                        continue
                    
                    print(f"\nProcessing topic: {title}")
                    print(f"Topic URL: {topic_url}")
                    
                    # Get the full topic content to check first post
                    full_url = urljoin(FORUM_BASE_URL, topic_url)
                    print(f"Fetching full topic from: {full_url}")
                    topic_response = requests.get(full_url, headers=HEADERS)
                    topic_response.raise_for_status()
                    topic_soup = BeautifulSoup(topic_response.text, 'html.parser')
                    
                    # Get the first post content - use crawler-specific selectors
                    first_post = topic_soup.select_one('#post_1 .post')
                    if not first_post:
                        print("No first post content found")
                        continue
                        
                    first_post_text = first_post.get_text(strip=True)
                    print(f"First post length: {len(first_post_text)} chars")
                    
                    # Check if this is a proposal by looking for key terms in the first post
                    proposal_terms = ['proposal', 'arfc', 'aip', 'temp check', 'temperature check', 'simple summary']
                    if not any(term in first_post_text.lower() for term in proposal_terms):
                        print(f"No proposal terms found in: {title}")
                        continue
                    
                    # Extract topic ID from URL
                    topic_id = topic_url.split('/')[-1].split('-')[0]  # Get numeric ID
                    print(f"Extracted topic ID: {topic_id}")
                    
                    # Extract timestamp
                    created_at = topic.get('data-created-at')
                    if created_at:
                        try:
                            created_at = int(datetime.strptime(created_at, '%Y-%m-%dT%H:%M:%S.%fZ').timestamp())
                        except (ValueError, TypeError):
                            created_at = int(datetime.now().timestamp())
                    else:
                        created_at = int(datetime.now().timestamp())
                    
                    proposal = {
                        'id': topic_id,
                        'title': title,
                        'created_at': created_at,
                        'url': full_url,
                        'content': first_post_text[:500]  # Store preview of content
                    }
                    governance_proposals.append(proposal)
                    print(f"Added proposal: {title} ({len(governance_proposals)}/5)")
                    
                except Exception as e:
                    print(f"Error processing topic: {str(e)}")
                    continue
            
            print(f"\nFound {len(governance_proposals)} proposals")
            
            # Print first few proposals for debugging
            for proposal in governance_proposals:
                print(f"\nProposal found:")
                print(f"Title: {proposal['title']}")
                print(f"ID: {proposal['id']}")
                print(f"URL: {proposal['url']}")
                print(f"Created: {datetime.fromtimestamp(proposal['created_at'])}")
                print(f"Content preview: {proposal['content'][:200]}...")
            
            return governance_proposals
        except requests.RequestException as e:
            print(f"Error fetching proposals: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response headers: {dict(e.response.headers)}")
                print(f"Response content: {e.response.text[:500]}...")
            return []

    def get_proposal_content(self, topic_id):
        """Fetch the full content of a proposal."""
        url = urljoin(PROPOSAL_BASE_URL, str(topic_id))
        try:
            print(f"Fetching proposal content from: {url}")
            print(f"Using headers: {HEADERS}")
            
            response = requests.get(url, headers=HEADERS, allow_redirects=True)
            print(f"Request URL: {response.request.url}")
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract the first post content using crawler-specific selector
            post_content = soup.select_one('#post_1 .post')
            if post_content:
                # Remove unnecessary elements
                for element in post_content.select('style, script'):
                    element.decompose()
                return post_content.get_text(strip=True)
            return ""
        except requests.RequestException as e:
            print(f"Error fetching proposal content: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response headers: {dict(e.response.headers)}")
            return ""

    def summarize_proposal(self, content):
        """Generate an AI summary of the proposal using DeepSeek via OpenAI SDK."""
        try:
            prompt = f"""Please provide a concise summary of the following AAVE governance proposal. 
            Focus on the key technical points, implementation details, and any development impact:

            {content[:4000]}  # Limit content length for API
            """
            
            response = self.ai_client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "Error generating summary"

    def send_discord_notification(self, proposal, summary):
        """Send a notification to Discord with the proposal summary."""
        try:
            if not self.discord_webhook_url:
                print("Discord webhook URL not configured. Skipping notification.")
                return
                
            webhook = DiscordWebhook(url=self.discord_webhook_url)
            
            # Create embed with AAVE's purple color
            embed = DiscordEmbed(
                title=f"New AAVE Development Proposal",
                description=f"**{proposal['title']}**\n\n{summary[:2000]}",  # Discord has a 2000 char limit
                color=0x7C3AED  # AAVE purple
            )
            
            # Add metadata fields
            embed.add_embed_field(name="Proposal ID", value=proposal['id'])
            embed.add_embed_field(name="Created At", value=datetime.fromtimestamp(proposal['created_at']).strftime('%Y-%m-%d %H:%M:%S'))
            embed.add_embed_field(name="Forum Link", value=proposal['url'])
            
            webhook.add_embed(embed)
            webhook.execute()
            print("Discord notification sent!")
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

    def test_scraping(self):
        """Test the forum scraping functionality."""
        print("Testing AAVE forum scraping...")
        proposals = self.fetch_proposals()
        
        if proposals:
            print("\nTesting content fetching for first proposal...")
            first_proposal = proposals[0]
            content = self.get_proposal_content(first_proposal['id'])
            
            print(f"\nProposal Content Preview (first 500 chars):")
            print("-" * 50)
            print(content[:500])
            print("-" * 50)
            
            print("\nGenerating summary...")
            summary = self.summarize_proposal(content)
            
            print("\nGenerated Summary:")
            print("-" * 50)
            print(summary)
            print("-" * 50)
            
            if self.discord_webhook_url:
                print("\nSending test notification to Discord...")
                self.send_discord_notification(first_proposal, summary)
                print("Discord notification sent!")
        else:
            print("No proposals found to test with.")

if __name__ == "__main__":
    scraper = AaveForumScraper()
    # Run in scraping test mode
    scraper.test_scraping() 