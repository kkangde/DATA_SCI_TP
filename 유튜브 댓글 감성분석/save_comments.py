# save_comments.py
import os
import json
import re
import time
import csv
from dotenv import load_dotenv
from konlpy.tag import Okt
from googleapiclient.discovery import build

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sentiment_project.settings')
import django
django.setup()
from analysis.models import CommentSentiment

# 환경 설정
load_dotenv()
YOUTUBE_API_KEY = ("YOUTUBE_API_KEY")
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# 감성 사전 로드
with open("Training.json", "r", encoding="utf-8") as f:
    senti_dict = {item["word_root"]: int(item["polarity"]) for item in json.load(f)}

okt = Okt()

def clean_text(text):
    return re.sub(r'[^\uAC00-\uD7A3a-zA-Z0-9\s]', '', text)

def analyze_sentiment(text):
    words = okt.morphs(clean_text(text))
    score = sum([senti_dict.get(word, 0) for word in words])
    sentiment = "긍정" if score > 0 else "부정" if score < 0 else "중립"
    return sentiment, score

def fetch_comments(video_id, max_count=30):
    comments = []
    try:
        res = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            maxResults=max_count,
            textFormat='plainText'
        ).execute()
        for item in res.get('items', []):
            text = item['snippet']['topLevelComment']['snippet']['textDisplay']
            if len(text.strip()) > 5:
                comments.append(text)
    except Exception as e:
        print(f"❗ 댓글 요청 실패: {e}")
    return comments

def analyze_and_store_from_csv(csv_path='video_ids.csv'):
    if not os.path.exists(csv_path):
        print("❗ CSV 파일이 없습니다.")
        return

    updated_rows = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = list(csv.DictReader(f))
        for row in reader:
            if row.get("analyzed", "").lower() == 'true':
                updated_rows.append(row)
                continue

            name = row['member_name']
            video_id = row['video_id']
            title = row['video_title']
            if not video_id:
                updated_rows.append(row)
                continue

            comments = fetch_comments(video_id)
            print(f"\n🎯 {name} | 영상: {title} | 댓글 수: {len(comments)}")
            for comment in comments:
                if CommentSentiment.objects.filter(member_name=name, comment_text=comment).exists():
                    continue
                try:
                    sentiment, score = analyze_sentiment(comment)
                    CommentSentiment.objects.create(
                        member_name=name,
                        comment_text=comment,
                        sentiment=sentiment,
                        sentiment_score=score
                    )
                    print(f"✅ 저장: {sentiment} ({score}) - {comment[:30]}...")
                except Exception as e:
                    print(f"⚠️ 저장 실패: {e}")

            row['analyzed'] = 'True'
            updated_rows.append(row)

    # 갱신된 analyzed 상태 다시 저장
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['member_name', 'video_id', 'video_title', 'analyzed'])
        writer.writeheader()
        writer.writerows(updated_rows)

def main():
    analyze_and_store_from_csv()

if __name__ == "__main__":
    main()
