import logging
import praw
from flask import Flask, render_template, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

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

def fetch_reddit_data():
    subreddits = ['technology', 'machinelearning']
    all_posts = []
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        for post in subreddit.top(time_filter='day', limit=3):
            all_posts.append(f"{post.title}. {post.selftext[:50]}")
    return all_posts

def fetch_summary(content):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Write a news paragraph based on the following content. The paragraph should start with a 1-sentence headline, followed by a 7-sentence detailed news summary.:\n\n{content}"}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error fetching summary: {str(e)}")
        return "An error occurred while generating this summary."

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        content = fetch_reddit_data()
        summaries = [fetch_summary(post) for post in content]
        return jsonify({'summary': summaries})
    except Exception as e:
        logging.error(f"Error in analyze: {str(e)}")
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

# Remove the if __name__ == '__main__' block for Vercel deployment