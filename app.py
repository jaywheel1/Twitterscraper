import streamlit as st
import pandas as pd
import base64
from datetime import datetime
import snscrape.modules.twitter as sntwitter
import time

st.set_page_config(page_title="Twitter Profile Scraper", page_icon="🐦")

st.title("Twitter/X Profile Scraper")
st.write("Enter a Twitter username to scrape their recent tweets")

# Form for user input
username = st.text_input("Twitter Username (without @)", value="")
num_tweets = st.slider("Number of tweets to scrape", min_value=5, max_value=100, value=20)

def scrape_profile(username, num_tweets=50):
    """Scrape tweets from a specified Twitter/X profile using snscrape."""
    # Initialize progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    tweets = []
    query = f"from:{username}"
    
    status_text.text(f"Fetching tweets from @{username}...")
    
    # Create a generator for the tweets
    tweets_generator = sntwitter.TwitterSearchScraper(query).get_items()
    
    # Collect tweets
    try:
        for i, tweet in enumerate(tweets_generator):
            if i >= num_tweets:
                break
                
            # Update progress
            progress = min((i + 1) / num_tweets, 0.99)
            progress_bar.progress(progress)
            status_text.text(f"Collected {i + 1} of {num_tweets} tweets...")
            
            tweet_data = {
                'text': tweet.content,
                'timestamp': tweet.date.strftime('%Y-%m-%d %H:%M:%S'),
                'replies': tweet.replyCount,
                'retweets': tweet.retweetCount,
                'likes': tweet.likeCount
            }
            
            tweets.append(tweet_data)
            
            # Small delay to avoid rate limiting
            time.sleep(0.1)
        
        progress_bar.progress(1.0)
        status_text.text(f"Successfully collected {len(tweets)} tweets!")
        
    except Exception as e:
        st.error(f"Error scraping tweets: {str(e)}")
        
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
- This tool uses web scraping to collect tweets from public Twitter/X profiles.
- Please use responsibly and respect Twitter's terms of service.
- Twitter/X may change their website structure which could cause this tool to stop working.
""")
