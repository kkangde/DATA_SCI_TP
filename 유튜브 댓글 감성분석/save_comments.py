import os
import json
import re
import csv
from konlpy.tag import Okt
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Django 환경 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sentiment_project.settings')
import django
django.setup()
from analysis.models import CommentSentiment

# 여러 API 키 순환 사용
API_KEYS = [
    "AIzaSyBY7zG5sVJ4VXlqd6JdCW4Q_29zNwox7V0",
    "AIzaSyCG9G9CSIHFmlRruVgshmU5-xGkhATlMZ0",
    "AIzaSyCF4WX5FGjd9-zsb9PPLvNZfe5z-6mESL8",
    "AIzaSyC5GxrmYvYHJXDQub_0JMHhc4ArQHhzyoA"
]
current_key_index = 0

def get_youtube_client():
    global current_key_index
    key = API_KEYS[current_key_index]
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    return build('youtube', 'v3', developerKey=key)

# 감성 사전 로드
with open("SentiWord_info.json", "r", encoding="utf-8") as f:
    senti_dict = {item["word_root"]: int(item["polarity"]) for item in json.load(f)}

okt = Okt()

def clean_text(text):
    return re.sub(r'[^\uAC00-\uD7A3a-zA-Z0-9\s]', '', text)

def analyze_sentiment(text):
    words = okt.morphs(clean_text(text))
    score = sum([senti_dict.get(word, 0) for word in words])
    sentiment = "긍정" if score > 0 else "부정" if score < 0 else "중립"
    return sentiment, score

def fetch_comments(video_id, max_count=30, max_retries=5):
    """
    좋아요(인기) 순으로 댓글 30개 수집 (중복 방지는 DB에서 처리)
    API 키 순환 및 쿼터 초과/오류 자동 전환
    """
    comments = []
    next_page_token = None
    tried = 0
    while len(comments) < max_count:
        youtube = get_youtube_client()
        try:
            req = youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=min(100, max_count - len(comments)),
                textFormat='plainText',
                order='relevance'
            )
            if next_page_token:
                req = req.pageToken(next_page_token)
            res = req.execute()
            for item in res.get('items', []):
                snippet = item['snippet']['topLevelComment']['snippet']
                text = snippet['textDisplay']
                like_count = snippet.get('likeCount', 0)
                if len(text.strip()) > 5:
                    comments.append((text, like_count))
                    if len(comments) >= max_count:
                        break
            next_page_token = res.get('nextPageToken')
            if not next_page_token:
                break
        except HttpError as e:
            tried += 1
            error_reason = str(e)
            print(f"❗ API 오류({error_reason}), 다른 API 키로 재시도({tried}/{max_retries})")
            if tried >= max_retries * len(API_KEYS):
                print("❌ 모든 API 키 실패")
                break
            continue
        except Exception as e:
            print(f"❗ 댓글 요청 실패: {e}")
            break
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

            comments = fetch_comments(video_id, max_count=30)
            print(f"\n🎯 {name} | 영상: {title} | 댓글 수: {len(comments)}")
            for comment, like_count in comments:
                # 중복 댓글 방지
                if CommentSentiment.objects.filter(member_name=name, comment_text=comment).exists():
                    continue
                try:
                    sentiment, score = analyze_sentiment(comment)
                    CommentSentiment.objects.create(
                        member_name=name,
                        comment_text=comment,
                        sentiment=sentiment,
                        sentiment_score=score,
                        like_count=like_count  # 모델에 like_count 필드가 있어야 함!
                    )
                    print(f"✅ 저장: {sentiment} ({score}) | 좋아요:{like_count} - {comment[:30]}...")
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
