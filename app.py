import ssl
import certifi
import logging
import praw
from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import os
import traceback

load_dotenv()

# Create SSL context
ssl_context = ssl.create_default_context(cafile=certifi.where())

app = Flask(__name__, template_folder='Templates')

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Initialize OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
logging.debug(f"OpenAI API Key Loaded: {bool(os.getenv('OPENAI_API_KEY'))}")

def fetch_reddit_data():
    reddit = praw.Reddit(client_id=os.getenv('REDDIT_CLIENT_ID'),
                         client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                         user_agent='Vibe_Analysis_V1')
    
    subreddits = ['technology', 'machinelearning']
    combined_content = ""
    
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        for post in subreddit.top(time_filter='day', limit=3):
            combined_content += post.title + ". " + post.selftext[:100] + "\n\n"
    
    return combined_content

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        content = fetch_reddit_data()

        summaries = []
        
        for piece in content.split('\n\n'):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant who writes short, catchy headlines followed by detailed news summaries. Each headline should be one sentence, and the news summary should be exactly seven sentences, providing context, analysis, and a touch of humor."},
                    {"role": "user", "content": f" Write a news paragraph based on the following content. The paragraph should start with a 1-sentence headline, followed by a 7-sentence detailed news summary.:\n\n{piece}"}
                ]
            )
            summary = response.choices[0].message.content.strip()
            summaries.append(summary)

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
    app.run(debug=True, port=5001)