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
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful and witty assistant who excels at summarizing tech news with a blend of humor and insight. The headline should be 1 short sentence, never number the headline. Followed by a news paragraph that’s detailed, containing 7 sentences. The news content should follow the headline and provide context, analysis, and a humorous or insightful closing line."},
                {"role": "user", "content": f" Based on the following content, create 7 news paragraphs, each with 1 line headline and detailed 7-sentence news summary that correlates to the headline. The headline should be 1 sentence, and the news summary should be informative with 7 sentences, engaging, and provide some humorous or insightful commentary.:\n\n{content}"}
            ]
        )
        summary = response.choices[0].message.content.strip().split('\n\n')
        
        return jsonify({'summary': summary})
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