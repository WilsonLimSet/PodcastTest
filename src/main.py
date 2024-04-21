from src.summarizer import Summarizer

def main():
    summarizer = Summarizer()
    urls = ["https://www.youtube.com/watch?v=8HrzoEvLWH0"]
    summarizer.process_youtube_videos(urls)

if __name__ == "__main__":
    main()
