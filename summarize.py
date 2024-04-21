import os
import json
from datetime import datetime
from dotenv import load_dotenv
from pytube import YouTube
import google.generativeai as genai
from supabase import create_client, Client
from youtubeScraper import return_urls
from urllib.parse import urlparse, urlunparse

def setup_environment():
    """Load environment variables and configure APIs."""
    load_dotenv()
    google_api_key = os.getenv('GOOGLE_API_KEY')
    genai.configure(api_key=google_api_key)
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    return create_client(supabase_url, supabase_key)

def standardize_url(url):
    """Standardizes URLs by ensuring the scheme is https and removing 'www.' from the domain."""
    # Normalize the URL to ensure https and remove 'www.'
    if url.startswith('http://www.'):
        url = 'https://' + url[len('http://www.'):]
    elif url.startswith('http://'):
        url = 'https://' + url[len('http://'):]
    elif url.startswith('https://www.'):
        url = 'https://' + url[len('https://www.'):]
    elif url.startswith('https://'):
        url = url  # Already in correct scheme, no 'www.' to remove
    else:
        # Default to adding 'https://' if no protocol is specified
        url = 'https://' + url

    return url

def url_exists_in_supabase(supabase, url):
    """Check if the given URL already exists in the Supabase table."""
    try:
        response = supabase.table("Podcasts").select("youtube_url").execute()
        urls_set = set(item['youtube_url'] for item in response.data)
        standard_url = standardize_url(url)
        print(f"Checking URL: {standard_url}")

        if standard_url in urls_set:
            print("URL already exists in the database.")
            return True
        else:
            print("URL does not exist in the database.")
            return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def download_audio(url):
    """Download the highest quality audio stream from YouTube if duration <= 1 hour."""
    yt = YouTube(url)
    if yt.length > 3600:
        raise ValueError("Video duration exceeds 1 hour.")
    audio_stream = yt.streams.filter(only_audio=True).first()
    if not audio_stream:
        raise ValueError("No audio streams available.")
    audio_file = 'sample.mp3'
    audio_stream.download(output_path='.', filename=audio_file)
    print(audio_stream)
    return yt, audio_file

def generate_content(prompt, model, upload_path=None):
    """Generate content using the Gemini model with optional file upload."""
    if upload_path:
        try:
            file_id = genai.upload_file(path=upload_path)
            return model.generate_content([prompt, file_id])
        except TimeoutError as e:
            print(f"Timeout during upload: {e}")
            return None
    return model.generate_content([prompt])

def upload_data_to_supabase(supabase, data):
    supabase.table('Podcasts').insert(data).execute()

def process_youtube_videos(urls, supabase):
    """Process each YouTube video URL for content generation and upload the results if not already in the database."""
    model = genai.GenerativeModel('models/gemini-1.5-pro-latest')
    for url in urls:
        #print(f"Checking URL: {url}")
        if url_exists_in_supabase(supabase, url):
            print(f"URL already exists, skipping: {url}")
            continue
        try:
            yt, audio_file = download_audio(url)
            description = yt.description or "No description available."
            #print(description)
            if description != "No description available.":
                prompt_name = f"Identify only the name of the interviewee from this description: {description}. It is imperative you **only give the name of the interviewee"
                response_name = generate_content(prompt_name, model)
                interviewee_name = response_name.text.strip() if response_name else "Unknown"
            else:
                interviewee_name = "Unknown"

            prompt_insights = "Provide the 3 most interesting insights from this audio in only 1 sentences each seperated by two newline characters (\n\n) and no heading."
            response_insights = generate_content(prompt_insights, model, upload_path=audio_file)
            print(response_insights.text)
            if response_insights:
                insights = response_insights.text.split("\n\n")[:3]  # Split the insights and take the first three
                insight_1 = insights[0] if len(insights) > 0 else "No insights could be generated."
                insight_2 = insights[1] if len(insights) > 1 else "No second insight could be generated."
                insight_3 = insights[2] if len(insights) > 2 else "No third insight could be generated."
            else:
                insight_1 = "No insights could be generated."
                insight_2 = "No insights could be generated."
                insight_3 = "No insights could be generated."

            output_data = {
                "publish_date": yt.publish_date.strftime("%Y-%m-%d") if yt.publish_date else "Unknown publish date",
                "youtube_url": yt.watch_url,
                "thumbnail_url": yt.thumbnail_url,
                "interviewer": yt.author,
                "interviewee": interviewee_name,
                "insight_1": insight_1,
                "insight_2": insight_2,
                "insight_3": insight_3,

            }

        
            upload_data_to_supabase(supabase, output_data)

            print(f"Processed: {yt.title}")
        except ValueError as e:
            print(f"Skipping URL due to error: {str(e)}")

def main():
    supabase = setup_environment()
    urls = return_urls("podcast")
    process_youtube_videos(urls, supabase)

if __name__ == "__main__":
    main()
