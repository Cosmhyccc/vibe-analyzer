import ssl
import certifi
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse
import praw
from openai import OpenAI
from dotenv import load_dotenv
import os
import traceback
from fastapi.middleware.cors import CORSMiddleware

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

# Create SSL context
ssl_context = ssl.create_default_context(cafile=certifi.where())

app = FastAPI()

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Set up templates
templates = Jinja2Templates(directory="Templates")

# Initialize OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
logger.debug(f"OpenAI API Key Loaded: {bool(os.getenv('OPENAI_API_KEY'))}")

def fetch_reddit_data():
    try:
        reddit = praw.Reddit(client_id=os.getenv('REDDIT_CLIENT_ID'),
                             client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                             user_agent='Vibe_Analysis_V1')
        
        subreddits = ['technology', 'machinelearning', 'tech']
        combined_content = ""
        
        for subreddit_name in subreddits:
            subreddit = reddit.subreddit(subreddit_name)
            for post in subreddit.top(time_filter='day', limit=5):
                combined_content += post.title + ". " + post.selftext[:100] + "\n\n"
        
        return combined_content
    except Exception as e:
        logger.error(f"Error fetching Reddit data: {str(e)}")
        raise

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analyze")
async def analyze():
    try:
        content = fetch_reddit_data()
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Based on the following content provide a detailed 6 paragraph summary that captures the key discussions and overall sentiment. Add 1 emoji at the end of each paragraph. Make it sound cool, interesting, and funny with dark humor:\n\n{content}"}
            ]
        )
        summary = response.choices[0].message.content.strip().split('\n\n')
        
        return JSONResponse(content={'summary': summary})
    except Exception as e:
        logger.error(f"Error in analyze: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/result", response_class=HTMLResponse)
async def result(request: Request):
    return templates.TemplateResponse("result.html", {"request": request})

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("aboutus.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)