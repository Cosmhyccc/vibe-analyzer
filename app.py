import ssl
import certifi
import logging
import praw
from flask import Flask, render_template, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import os
import traceback
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

load_dotenv()

# Create SSL context
ssl_context = ssl.create_default_context(cafile=certifi.where())

app = Flask(__name__, template_folder='Templates')

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Initialize OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
logging.debug(f"OpenAI API Key Loaded: {bool(os.getenv('OPENAI_API_KEY'))}")

# Initialize Reddit
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent='Vibe_Analysis_V1'
)

# Cache for Reddit data
@lru_cache(maxsize=1)
def fetch_cached_reddit_data():
    subreddits = ['technology', 'machinelearning']
    all_posts = []
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        for post in subreddit.top(time_filter='day', limit=3):
            all_posts.append(f"{post.title}. {post.selftext[:50]}")
    return all_posts

# Asynchronous OpenAI API call
async def async_openai_call(client, content):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(
            pool,
            lambda: client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": f"Write a news paragraph based on the following content. The paragraph should start with a 1-sentence headline, followed by a 7-sentence detailed news summary.:\n\n{content}"}
                ]
            )
        )
    return response.choices[0].message.content.strip()

# Asynchronous summary generation
async def generate_summaries(posts):
    tasks = [async_openai_call(client, post) for post in posts]
    return await asyncio.gather(*tasks)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
async def analyze():
    try:
        # Fetch cached Reddit data
        content = fetch_cached_reddit_data()
        
        # Generate summaries asynchronously
        summaries = await generate_summaries(content)
        
        return jsonify({'summary': summaries})
    except Exception as e:
        logging.error(f"Error in analyze: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/result')
def result():
    return render_template('result.html')

@app.route('/about')
def about():
    return render_template('aboutus.html')

@app.route('/supportus')
def support():
    return render_template('supportus.html')

if __name__ == '__main__':
    from hypercorn.config import Config
    from hypercorn.asyncio import serve

    config = Config()
    config.bind = ["localhost:5001"]
    asyncio.run(serve(app, config))