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
            combined_content += post.title + ". " + post.selftext[:70] + "\n\n"
    
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
                {"role": "system", "content": "You are a helpful and witty assistant who excels at summarizing tech news with a blend of humor and insight. Keep the tone conversational but informative, and always aim to engage the reader. You always give 7 detailed paragraphs , each has one headline, put one emoji before each title."},
                {"role": "user", "content": f" Based on the following content provide a detailed 5 paragraph summary that captures the key discussions and overall sentiment. Add 1 emoji at the end of each paragraph. Add a 1 liner title before each paragraph.Each paragraph must be exactly 7 sentences Make it sound cool, interesting, and funny with dark humor. Here is the content:\n\n{content}"}
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