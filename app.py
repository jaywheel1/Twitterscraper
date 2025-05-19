import streamlit as st
import pandas as pd
import base64
from datetime import datetime
import requests
import json

st.set_page_config(page_title="Twitter Profile Scraper", page_icon="🐦")

st.title("Twitter/X Profile Scraper")
st.write("Enter a Twitter username to scrape their recent tweets")

# Form for user input
username = st.text_input("Twitter Username (without @)", value="")
num_tweets = st.slider("Number of tweets to scrape", min_value=5, max_value=100, value=20)

# Simplified approach using nitter.net as a Twitter frontend
def scrape_profile(username, num_tweets=50):
    """Scrape tweets from a Twitter profile using a public API"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    status_text.text(f"Fetching tweets from @{username}...")
    
    tweets = []
    
    try:
        # Use a public API that provides Twitter data
        # Note: This is a demonstration API and might have rate limits
        api_url = f"https://api.allorigins.win/raw?url=https://nitter.net/{username}/rss"
        
        response = requests.get(api_url)
        
        if response.status_code != 200:
            st.error(f"Error: Could not fetch data for @{username}")
            return []
        
        # Parse the XML response
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)
        
        # Find all items (tweets)
        items = root.findall(".//item")
        
        # Extract data from each tweet
        for i, item in enumerate(items[:num_tweets]):
            if i >= num_tweets:
                break
                
            # Update progress
            progress = min((i + 1) / num_tweets, 0.99)
            progress_bar.progress(progress)
            status_text.text(f"Processing {i + 1} of {num_tweets} tweets...")
            
            try:
                # Get the tweet content (remove the username part)
                full_text = item.find("title").text
                text = full_text.split(":", 1)[1].strip() if ":" in full_text else full_text
                
                # Get the timestamp
                pub_date = item.find("pubDate").text
                timestamp = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z").strftime("%Y-%m-%d %H:%M:%S")
                
                # Get the link (which contains the tweet ID)
                link = item.find("link").text
                tweet_id = link.split("/")[-1]
                
                tweet_data = {
                    "text": text,
                    "timestamp": timestamp,
                    "link": link,
                    "tweet_id": tweet_id
                }
                
                tweets.append(tweet_data)
                
            except Exception as e:
                st.warning(f"Error processing a tweet: {str(e)}")
                continue
                
        progress_bar.progress(1.0)
        status_text.text(f"Successfully collected {len(tweets)} tweets!")
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        
    return tweets

def get_csv_download_link(df, filename):
    """Generate a link to download the DataFrame as a CSV file."""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download CSV File</a>'
    return href

# Only run the scraper when the button is clicked
if st.button("Scrape Tweets"):
    if not username:
        st.error("Please enter a Twitter username")
    else:
        with st.spinner(f"Scraping tweets from @{username}..."):
            tweets = scrape_profile(username, num_tweets)
            
            if tweets:
                # Convert tweets to DataFrame
                df = pd.DataFrame(tweets)
                
                # Display the results
                st.subheader(f"Scraped {len(tweets)} tweets from @{username}")
                st.dataframe(df)
                
                # Create download link
                filename = f"{username}_tweets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                st.markdown(get_csv_download_link(df, filename), unsafe_allow_html=True)
            else:
                st.error("No tweets were scraped. Please check the username and try again.")

st.markdown("---")
st.markdown("""
### 📝 Notes:
- This tool uses Nitter's RSS feed to collect tweets from public Twitter/X profiles.
- Please use responsibly and respect Twitter's terms of service.
- Limited data is available through this method (no like/retweet counts).
- Twitter/X may change their site structure which could cause this tool to stop working.
""")
