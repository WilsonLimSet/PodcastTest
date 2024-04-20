from dotenv import load_dotenv
import os
import requests
from pytube import YouTube
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Retrieve API key from environment variables
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Configure the API with the key
genai.configure(api_key=GOOGLE_API_KEY)

# URL of the file you want to download
#URL = "https://storage.googleapis.com/generativeai-downloads/data/State_of_the_Union_Address_30_January_1961.mp3"
#URL = "https://www.youtube.com/watch?v=xv4r18hAc1I"
url = "https://www.youtube.com/watch?v=xv4r18hAc1I"
yt = YouTube(url)
audio_stream = yt.streams.filter(only_audio=True).first()

print(yt.thumbnail_url)
audio_stream.download(output_path='.', filename='sample.mp3')


# Download the file using requests
#response = requests.get(URL)
# if response.status_code == 200:
#     with open('sample.mp3', 'wb') as f:
#         f.write(response.content)

# Upload the file using the Google API
your_file = genai.upload_file(path='sample.mp3')

prompt = "Listen carefully to the following audio file. Provide a brief summary with timestamps of when he said what."
model = genai.GenerativeModel('models/gemini-1.5-pro-latest')
response = model.generate_content([prompt, your_file])

# Output the response to a text file
with open('output.txt', 'w') as file:
    file.write(response.text)

print(response.text)
