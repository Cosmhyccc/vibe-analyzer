from flask import Flask, render_template, request
from openai import OpenAI
import praw
from dotenv import load_dotenv
import os
import logging
import traceback

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, template_folder='Templates')

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Set up OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
logging.debug(f"OpenAI API Key Loaded: {bool(os.getenv('OPENAI_API_KEY'))}")

# Set up Reddit API client
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent='Vibe_Analysis_V1'
)

def analyze_reddit():
    try:
        subreddits = ['technology', 'machinelearning', 'tech', 'openai']
        combined_content = ""
        for subreddit_name in subreddits:
            subreddit = reddit.subreddit(subreddit_name)
            top_posts = subreddit.top(time_filter='day', limit=10)
            for post in top_posts:
                combined_content += post.title + ". " + post.selftext + "\n\n"
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Based on the following content provide a concise 2-paragraph summary that captures the key discussions and overall sentiment. The summary should tell the user some detail as to what the discussions were about. make it sound cool and interesting to read, not boring. Do not name the subreddits anywhere in the output, keep it natural. Add a humourous touch to everything. always remember its funny because its true so seek truth in funny. The summary should give a clear sense of what's happening in the tech culture. MAKE IT FUNNY, REALLY FUNNY.:\n\n{combined_content}"}
            ]
        )
        logging.debug(f"OpenAI API Response: {response}")
        summary = response.choices[0].message.content.strip()
        paragraphs = summary.split('\n\n')
        return paragraphs
    except Exception as e:
        error_type = type(e).__name__
        error_message = str(e)
        error_traceback = traceback.format_exc()
        logging.error(f"Error type: {error_type}")
        logging.error(f"Error message: {error_message}")
        logging.error(f"Error traceback: {error_traceback}")
        return [f"An error occurred during analysis: {error_type} - {error_message}. Please try again later."]

# Flask routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    summary = analyze_reddit()
    return render_template('result.html', summary=summary)

@app.route('/about')
def about():
    return render_template('aboutus.html')

@app.route('/test-connections')
def test_connections():
    reddit_status = "Error"
    openai_status = "Error"
    try:
        reddit.user.me()
        reddit_status = "OK"
    except Exception as e:
        reddit_status = f"Error: {type(e).__name__} - {str(e)}"
    
    try:
        client.chat.completions.create(model="gpt-4", messages=[{"role": "user", "content": "Hello"}])
        openai_status = "OK"
    except Exception as e:
        openai_status = f"Error: {type(e).__name__} - {str(e)}"
    
    return f"Reddit: {reddit_status}<br>OpenAI: {openai_status}"

if __name__ == '__main__':
    app.run(debug=True, port=5001)