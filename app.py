import streamlit as st
import time
from datetime import datetime
import pandas as pd
import base64
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

st.set_page_config(page_title="Twitter Profile Scraper", page_icon="🐦")

st.title("Twitter/X Profile Scraper")
st.write("Enter a Twitter username to scrape their recent tweets")

# Form for user input
username = st.text_input("Twitter Username (without @)", value="")
num_tweets = st.slider("Number of tweets to scrape", min_value=5, max_value=100, value=20)

def setup_driver():
    """Set up and return a configured Chrome webdriver."""
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def scrape_profile(username, num_tweets=50):
    """Scrape tweets from a specified Twitter/X profile."""
    # Initialize progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    driver = setup_driver()
    url = f"https://twitter.com/{username}"
    
    status_text.text(f"Navigating to {url}")
    driver.get(url)
    
    # Wait for tweets to load
    wait = WebDriverWait(driver, 10)
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweet"]')))
    except:
        st.error(f"Could not find tweets for @{username}. Please check if the username is correct.")
        driver.quit()
        return []
    
    tweets = []
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while len(tweets) < num_tweets:
        # Update progress
        progress = min(len(tweets) / num_tweets, 0.9)
        progress_bar.progress(progress)
        status_text.text(f"Collected {len(tweets)} of {num_tweets} tweets...")
        
        # Scroll down to load more tweets
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Wait for new tweets to load
        
        # Get all tweets on the page
        tweet_elements = driver.find_elements(By.CSS_SELECTOR, '[data-testid="tweet"]')
        
        for tweet in tweet_elements:
            if len(tweets) >= num_tweets:
                break
                
            try:
                # Extract tweet text
                tweet_text_element = tweet.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
                tweet_text = tweet_text_element.text
                
                # Extract timestamp
                time_element = tweet.find_element(By.CSS_SELECTOR, 'time')
                timestamp = time_element.get_attribute('datetime')
                
                # Extract metrics (likes, retweets, replies)
                metrics = {}
                try:
                    metrics['replies'] = tweet.find_element(By.CSS_SELECTOR, '[data-testid="reply"]').text
                except:
                    metrics['replies'] = "0"
                    
                try:
                    metrics['retweets'] = tweet.find_element(By.CSS_SELECTOR, '[data-testid="retweet"]').text
                except:
                    metrics['retweets'] = "0"
                    
                try:
                    metrics['likes'] = tweet.find_element(By.CSS_SELECTOR, '[data-testid="like"]').text
                except:
                    metrics['likes'] = "0"
                
                tweet_data = {
                    'text': tweet_text,
                    'timestamp': timestamp,
                    'replies': metrics['replies'],
                    'retweets': metrics['retweets'],
                    'likes': metrics['likes']
                }
                
                # Only add if not already in the list
                if tweet_data not in tweets:
                    tweets.append(tweet_data)
            
            except Exception as e:
                st.warning(f"Error extracting tweet: {str(e)}")
                continue
        
        # Check if we've reached the bottom or if no new tweets were loaded
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    
    driver.quit()
    progress_bar.progress(1.0)
    status_text.text(f"Successfully collected {len(tweets)} tweets!")
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
