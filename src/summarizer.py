import json
from dotenv import load_dotenv
from pytube import YouTube
from src.db.client import Client as DBClient
from src.models.model import Model as GeminiModel

class Summarizer:
    """
    Given some url, summarize it into a JSON object
    """
    def __init__(self):
        load_dotenv()
        
        self.db = DBClient()
        self.model = GeminiModel()

    def download_audio(self, url: str):
        """Download the highest quality audio stream from YouTube if duration <= 1 hour."""
        
        yt = YouTube(url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        if not audio_stream:
            raise ValueError("No audio streams available.")
        
        audio_file = "data/sample.mp3"
        audio_stream.download(output_path='.', filename=audio_file)
        
        return yt, audio_file
    
    def get_interviewee_name(self, yt_description: str):
        prompt = f"""
        Given the following YouTube description, identify just 1 thing: the name of the interviewee.
        It is **imperative you only give the name of the interviewee, and nothing else**.
        {yt_description}
        """
        
        res = self.model.get_response(prompt)
        return res.strip()

    def get_key_insights(self, audio_file_path):
        prompt = f"""
        Given the following audio file, **provide the 3 most interesting insights from this conversation**.
        For each insight, provide 1 descriptive & meaningful sentence each, separated by 2 newline characters (\n\n) and nothing else.
        Do not use any special characters to denote each point.
        """
        
        res = self.model.execute_prompt_from_audio(prompt, audio_file_path)
        return res.strip()

    def process_youtube_videos(self, urls):
        """Process each YouTube video URL for content generation and upload the results if not already in the database."""
        for url in urls:
            if self.db.url_exists(url):
                print(f"URL present in DB, skipping: {url}")
                continue

            try:
                yt, audio_file = self.download_audio(url)
                if not yt.description:
                    continue
                
                interviewee_name = self.get_interviewee_name(yt.description)

                key_insights = self.get_key_insights(audio_file)
                if key_insights:
                    insights = key_insights.split("\n\n")[:3]
                    insight_1 = insights[0] if len(insights) >= 1 else ""
                    insight_2 = insights[1] if len(insights) >= 2 else ""
                    insight_3 = insights[2] if len(insights) >= 3 else ""

                data = {
                    "publish_date": yt.publish_date.strftime("%Y-%m-%d") if yt.publish_date else "Unknown publish date",
                    "youtube_url": yt.watch_url,
                    "thumbnail_url": yt.thumbnail_url,
                    "interviewer": yt.author,
                    "interviewee": interviewee_name,
                    "insight_1": insight_1,
                    "insight_2": insight_2,
                    "insight_3": insight_3,
                }

                self.db.upload(data)
                
                print(f'"{yt.title}"')
                print(json.dumps(data, indent=4))

            except ValueError as e:
                print(f"Skipping URL {url} due to error: {str(e)}")
