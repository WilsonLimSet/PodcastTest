import os
import json
from datetime import datetime
from pytube import YouTube
import google.generativeai as genai
from dotenv import load_dotenv

def setup_environment():
    """Load environment variables and configure API."""
    load_dotenv()
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    genai.configure(api_key=GOOGLE_API_KEY)

def download_audio_from_youtube(url):
    """Download the highest quality audio stream from YouTube."""
    yt = YouTube(url)
    audio_stream = yt.streams.filter(only_audio=True).first()
    audio_file = 'sample.mp3'
    audio_stream.download(output_path='.', filename=audio_file)
    return yt, audio_file

def get_description(yt):
    """Retrieve and check video description availability."""
    return yt.description if yt.description else "No description available."

def generate_content_from_model(prompt, model, upload_path=None):
    """Generate content using the Gemini model with optional file upload."""
    if upload_path:
        file_id = genai.upload_file(path=upload_path)
        return model.generate_content([prompt, file_id])
    return model.generate_content([prompt])

def output_to_json(data, filename='output_data.json'):
    """Output data to a JSON file."""
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def main():
    setup_environment()
    url = "https://www.youtube.com/watch?v=xv4r18hAc1I"
    yt, audio_file = download_audio_from_youtube(url)
    description = get_description(yt)
    print(description)

    model = genai.GenerativeModel('models/gemini-1.5-pro-latest')

    # Extract interviewee's name
    if description != "No description available.":
        prompt_for_name = f"From the following description, identify the name of the interviewee and dont give anything else besides the full name:: {description}"
        response_for_name = generate_content_from_model(prompt_for_name, model)
        interviewee_name = response_for_name.text.strip()
    else:
        interviewee_name = "Unknown"

    # Generate insights from the audio
    prompt_for_insights = "Listen carefully to the following audio file. Provide the 3 most interesting insights."
    response_for_insights = generate_content_from_model(prompt_for_insights, model, upload_path=audio_file)

    # Compile output data
    output_data = {
        "publish_date": yt.publish_date.strftime("%Y-%m-%d") if yt.publish_date else "Unknown publish date",
        "youtube_url": yt.watch_url,
        "thumbnail_url": yt.thumbnail_url,
        "interviewer": yt.author,
        "interviewee": interviewee_name,
        "insights": response_for_insights.text
    }

    output_to_json(output_data)
    print("Interviewee Identified:", interviewee_name)
    print("Insights:", response_for_insights.text)

if __name__ == "__main__":
    main()
