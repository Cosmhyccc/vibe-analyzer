import ssl
import certifi
import aiohttp
import logging
import asyncpraw
from flask import Flask, render_template, request, jsonify
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import traceback
import asyncio
from functools import lru_cache
from datetime import datetime, timedelta
import time

load_dotenv()

# Create SSL context
ssl_context = ssl.create_default_context(cafile=certifi.where())

app = Flask(__name__, template_folder='Templates')

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize AsyncOpenAI
client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
logging.debug(f"OpenAI API Key Loaded: {bool(os.getenv('OPENAI_API_KEY'))}")

# Cache for Reddit data
reddit_cache = {}
CACHE_DURATION = timedelta(minutes=15)

async def create_reddit_client():
    session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context))
    reddit = asyncpraw.Reddit(client_id=os.getenv('REDDIT_CLIENT_ID'),
                              client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                              user_agent='Vibe_Analysis_V1',
                              requestor_kwargs={'session': session})
    return reddit

async def fetch_subreddit_data(reddit, subreddit_name):
    start_time = time.time()
    subreddit = await reddit.subreddit(subreddit_name)
    content = ""
    async for post in subreddit.top(time_filter='day', limit=5):
        content += post.title + ". " + post.selftext[:100] + "\n\n"
    end_time = time.time()
    logging.info(f"Fetched data from r/{subreddit_name} in {end_time - start_time:.2f} seconds")
    return content

async def fetch_reddit_data(reddit, subreddits):
    start_time = time.time()
    tasks = [fetch_subreddit_data(reddit, subreddit) for subreddit in subreddits]
    results = await asyncio.gather(*tasks)
    end_time = time.time()
    logging.info(f"Fetched all Reddit data in {end_time - start_time:.2f} seconds")
    return "".join(results)

@lru_cache(maxsize=1)
def get_cached_reddit_data():
    return reddit_cache.get('data'), reddit_cache.get('timestamp')

async def get_reddit_data():
    start_time = time.time()
    cached_data, cached_timestamp = get_cached_reddit_data()
    if cached_data and cached_timestamp and datetime.now() - cached_timestamp < CACHE_DURATION:
        logging.info("Using cached Reddit data")
        end_time = time.time()
        logging.info(f"Retrieved cached data in {end_time - start_time:.2f} seconds")
        return cached_data

    subreddits = ['technology', 'machinelearning', 'tech']
    reddit = await create_reddit_client()
    combined_content = await fetch_reddit_data(reddit, subreddits)
    
    reddit_cache['data'] = combined_content
    reddit_cache['timestamp'] = datetime.now()
    get_cached_reddit_data.cache_clear()
    
    end_time = time.time()
    logging.info(f"Fetched and cached new Reddit data in {end_time - start_time:.2f} seconds")
    return combined_content

async def analyze_reddit_data(content):
    start_time = time.time()
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Based on the following content provide a detailed 6 paragraph summary that captures the key discussions and overall sentiment. Add 1 emoji at the end of each paragraph. Make it sound cool, interesting, and funny with dark humor:\n\n{content}"}
            ]
        )
        summary = response.choices[0].message.content.strip()
        end_time = time.time()
        logging.info(f"Analyzed Reddit data with OpenAI in {end_time - start_time:.2f} seconds")
        return summary.split('\n\n')
    except Exception as e:
        logging.error(f"Error in analyze_reddit_data: {str(e)}")
        return [f"An error occurred during analysis: {type(e).__name__} - {str(e)}. Please try again later."]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
async def analyze():
    start_time = time.time()
    content = await get_reddit_data()
    summary = await analyze_reddit_data(content)
    end_time = time.time()
    logging.info(f"Total analysis time: {end_time - start_time:.2f} seconds")
    return jsonify({'summary': summary})

@app.route('/result')
def result():
    return render_template('result.html')

@app.route('/about')
def about():
    return render_template('aboutus.html')

@app.route('/test-connections')
async def test_connections():
    reddit_status = "Error"
    openai_status = "Error"
    try:
        reddit = await create_reddit_client()
        await reddit.user.me()
        reddit_status = "OK"
    except Exception as e:
        reddit_status = f"Error: {type(e).__name__} - {str(e)}"
    
    try:
        await client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": "Hello"}])
        openai_status = "OK"
    except Exception as e:
        openai_status = f"Error: {type(e).__name__} - {str(e)}"
    
    return f"Reddit: {reddit_status}<br>OpenAI: {openai_status}"

if __name__ == '__main__':
    app.run(debug=True, port=5001)