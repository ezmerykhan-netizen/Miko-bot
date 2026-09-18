from googleapiclient.discovery import build
from config import YOUTUBE_API_KEY

_youtube = None


def get_youtube():
    global _youtube
    if _youtube is None and YOUTUBE_API_KEY:
        try:
            _youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        except Exception as e:
            print(f"[YOUTUBE] init: {e}")
            return None
    return _youtube


async def search_music(query, max_results=5):
    """جستجوی آهنگ تو YouTube"""
    yt = get_youtube()
    if not yt:
        return []
    try:
        request = yt.search().list(
            q=query,
            part="snippet",
            maxResults=max_results,
            type="video",
            videoCategoryId="10",  # Music
        )
        response = request.execute()
        results = []
        for item in response.get("items", []):
            vid_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            channel = item["snippet"]["channelTitle"]
            results.append({
                "video_id": vid_id,
                "title": title,
                "channel": channel,
                "url": f"https://youtu.be/{vid_id}"
            })
        return results
    except Exception as e:
        print(f"[YOUTUBE] خطا: {e}")
        return []
