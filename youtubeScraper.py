from googleapiclient.discovery import build
import datetime

# Create a YouTube client
api_service_name = "youtube"
api_version = "v3"
DEVELOPER_KEY = "AIzaSyBytRHSTpDp-mOQNGZSJsaYmmQu72n_kTI"

youtube = build(api_service_name, api_version, developerKey=DEVELOPER_KEY)

# Define the date range
end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=7)

# Format the dates for the API
start_date_str = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
end_date_str = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')

def youtube_search(query, max_results=50):
    # Call the search.list method to retrieve results matching the specified query term.
    search_response = youtube.search().list(
        q=query,
        part="id,snippet",
        maxResults=max_results,
        publishedAfter=start_date_str,
        publishedBefore=end_date_str,
        type="video"
    ).execute()

    # Collect the videos
    videos = []
    for search_result in search_response.get("items", []):
        videos.append(f'{search_result["snippet"]["title"]} - https://www.youtube.com/watch?v={search_result["id"]["videoId"]}')

    return videos

def return_urls(query, max_results=50):
    podcasts = youtube_search("tech podcast")
    urls = []
    for podcast in podcasts:
        podcast = podcast.split(" ")
        urls.append(podcast[-1])

    return urls

# print(return_urls("podcast")[0])