import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sentiment_project.settings')
import django
django.setup()

from googleapiclient.discovery import build
from konlpy.tag import Okt
import json
import requests
from analysis.models import CommentSentiment

# 사전 로딩
with open("SentiWord_info.json", "r", encoding="utf-8") as f:
    senti_data = json.load(f)

senti_dict = {item["word_root"]: int(item["polarity"]) for item in senti_data}
okt = Okt()

def analyze_sentiment_dict(text):
    words = okt.morphs(text)
    score = sum([senti_dict.get(word, 0) for word in words])

    if score > 0:
        sentiment = "긍정"
    elif score < 0:
        sentiment = "부정"
    else:
        sentiment = "중립"

    return sentiment, score

# 국회의원 API
def get_all_member_names(api_key):
    url = "https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu"
    params = {
        'KEY': api_key,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 300
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        key = "nwvrqwxyaytdsfvhu"
        rows = data.get(key, [])[1].get("row", [])
        names = [member["HG_NM"] for member in rows if "HG_NM" in member]
        return names
    else:
        print("❌ 국회의원 API 요청 실패:", response.status_code)
        return []

# YouTube API
YOUTUBE_API_KEY = 'AIzaSyBNqTeD-YJ_5zSeqhKFY0s1Sno_ai2TtQ8'
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def fetch_comments(youtube, video_id, max_count=30):
    comments = []
    req = youtube.commentThreads().list(
        part='snippet',
        videoId=video_id,
        maxResults=max_count,
        textFormat='plainText'
    )
    res = req.execute()
    for item in res.get('items', []):
        text = item['snippet']['topLevelComment']['snippet']['textDisplay']
        if len(text.strip()) > 5:
            comments.append(text)
    return comments

# 분석 및 저장
def analyze_and_store_comments(member_names):
    for name in member_names:
        try:
            search = youtube.search().list(
                q=name,
                part='snippet',
                type='video',
                maxResults=1
            ).execute()

            if not search['items']:
                continue

            video = search['items'][0]
            video_id = video['id']['videoId']
            comments = fetch_comments(youtube, video_id)

            print(f"\n🎯 의원: {name}, 영상: {video['snippet']['title']}, 댓글 수: {len(comments)}")

            for comment in comments:
                try:
                    sentiment, score = analyze_sentiment_dict(comment)

                    CommentSentiment.objects.create(
                        member_name=name,
                        comment_text=comment,
                        sentiment=sentiment,
                        sentiment_score=score
                    )
                    print(f"✅ 저장: {sentiment} ({score}) - {comment[:30]}...")
                except Exception as e:
                    print(f"⚠️ 감성 분석 실패: {e}")
        except Exception as e:
            print(f"❌ YouTube 검색 오류: {name} - {e}")

# 실행
OPEN_API_KEY = "1343ad8c9a584b86a2493aa90cf51060"
member_names = get_all_member_names(OPEN_API_KEY)
analyze_and_store_comments(member_names)
