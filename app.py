from flask import Flask, render_template, request
import openai
import praw
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, template_folder='Templates')

# Set up your OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

# Set up Reddit API client
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent='Vibe_Analysis_V1'
)

def analyze_reddit():
    subreddits = ['technology', 'machinelearning', 'tech', 'openai']
    combined_content = ""

    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        top_posts = subreddit.top(time_filter='day', limit=10)
        for post in top_posts:
            combined_content += post.title + ". " + post.selftext + "\n\n"

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Based on the following content provide a concise 2-paragraph summary that captures the key discussions and overall sentiment. The summary should tell the user some detail as to what the discussions were about. make it sound cool and interesting to read, not boring. Do not name the subreddits anywhere in the output, keep it natural. Add a humourous touch to everything. always remember its funny because its true so seek truth in funny. The summary should give a clear sense of what's happening in the tech culture. MAKE IT FUNNY, REALLY FUNNY.:\n\n{combined_content}"}
        ]
    )
    summary = response['choices'][0]['message']['content'].strip()
    paragraphs = summary.split('\n\n')
    return paragraphs

## Heres all the flask stuff
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
if __name__ == '__main__':
    app.run(debug=True, port=5001)

    #testingggggggggggg
