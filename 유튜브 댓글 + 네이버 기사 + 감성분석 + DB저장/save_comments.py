import requests
import sqlite3
import json
import re
from urllib.parse import quote
from datetime import datetime
from konlpy.tag import Okt
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# API 키 설정
CONGRESS_API_KEY = "1343ad8c9a584b86a2493aa90cf51060"
API_KEYS = [
    "AIzaSyBY7zG5sVJ4VXlqd6JdCW4Q_29zNwox7V0",
    "AIzaSyCG9G9CSIHFmlRruVgshmU5-xGkhATlMZ0",
    "AIzaSyCF4WX5FGjd9-zsb9PPLvNZfe5z-6mESL8",
    "AIzaSyC5GxrmYvYHJXDQub_0JMHhc4ArQHhzyoA"
]
NAVER_CLIENT_ID = "ppH1uMGA4_jWdMzMYMH4"
NAVER_CLIENT_SECRET = "j5wtomptl2"

with open("SentiWord_info.json", "r", encoding="utf-8") as f:
    data = json.load(f)
    if isinstance(data, dict):  # 딕셔너리일 경우 값 추출
        data = list(data.values())  # 키가 아닌 값 사용
    SENTI_DICT = {item["word_root"]: int(item["polarity"]) for item in data}


okt = Okt()

# 1. 국회의원 정보 수집
def get_politicians():
    url = "hhttps://open.assembly.go.kr/portal/openapi/nwvrqwxyijtxqyuj"
    params = {
        "KEY": CONGRESS_API_KEY,
        "Type": "json",
        "pIndex": 1,
        "pSize": 300
    }
    try:
        res = requests.get(url, params=params)
        data = res.json()
        return [
            (item['HG_NM'], item['POLY_NM'])
            for item in data['nzmimeepazxkubdpn'][1]['row']
        ]
    except Exception as e:
        print(f"❗ 국회 API 오류: {e}")
        return []

# 2. 유튜브 댓글 수집
def get_youtube_comments(name, api_key):
    youtube = build('youtube', 'v3', developerKey=api_key)
    comments = []
    try:
        search_response = youtube.search().list(
            q=name, part='id', maxResults=3, type='video'
        ).execute()
        
        for item in search_response.get('items', []):
            video_id = item['id']['videoId']
            comments_response = youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=100,
                order='relevance'
            ).execute()
            
            for comment in comments_response.get('items', []):
                text = comment['snippet']['topLevelComment']['snippet']['textDisplay']
                likes = comment['snippet']['topLevelComment']['snippet'].get('likeCount', 0)
                comments.append((text, likes))
    except HttpError as e:
        print(f"❗ YouTube API 오류: {e}")
    return comments

# 3. 네이버 기사 수집
def get_naver_news(name):
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    try:
        res = requests.get(
            f"https://openapi.naver.com/v1/search/news.json?query={quote(name)}&display=3&sort=date",
            headers=headers
        )
        return [
            {
                "title": re.sub('<.*?>', '', item['title']),
                "content": re.sub('<.*?>', '', item['description']),
                "date": item['pubDate']
            }
            for item in res.json()['items']
        ]
    except Exception as e:
        print(f"❗ {name} 뉴스 수집 실패: {e}")
        return []

# 4. 감성분석
def analyze_sentiment(text):
    words = okt.morphs(re.sub(r'[^\w\s]', '', text))
    score = sum(SENTI_DICT.get(word, 0) for word in words)
    sentiment = "긍정" if score > 0 else "부정" if score < 0 else "중립"
    return sentiment, abs(score)

# 5. 데이터베이스 저장
def save_to_db(politicians):
    conn = sqlite3.connect('political_analysis.db')
    c = conn.cursor()
    
    # 테이블 생성
    c.execute('''
        CREATE TABLE IF NOT EXISTS politicians (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            party TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS youtube_data (
            id INTEGER PRIMARY KEY,
            politician_id INTEGER,
            comment TEXT,
            likes INTEGER,
            sentiment TEXT,
            score REAL,
            FOREIGN KEY(politician_id) REFERENCES politicians(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS naver_news (
            id INTEGER PRIMARY KEY,
            politician_id INTEGER,
            title TEXT,
            content TEXT,
            date TEXT,
            sentiment TEXT,
            score REAL,
            FOREIGN KEY(politician_id) REFERENCES politicians(id)
        )
    ''')
    
    current_key_idx = 0
    for name, party in politicians:
        # 정치인 저장
        c.execute('INSERT OR IGNORE INTO politicians (name, party) VALUES (?, ?)', (name, party))
        politician_id = c.lastrowid or c.execute('SELECT id FROM politicians WHERE name=?', (name,)).fetchone()[0]
        
        # 유튜브 데이터 처리
        youtube_comments = get_youtube_comments(name, YOUTUBE_API_KEYS[current_key_idx])
        current_key_idx = (current_key_idx + 1) % len(YOUTUBE_API_KEYS)
        for comment, likes in youtube_comments:
            sentiment, score = analyze_sentiment(comment)
            c.execute('''
                INSERT INTO youtube_data 
                (politician_id, comment, likes, sentiment, score)
                VALUES (?, ?, ?, ?, ?)
            ''', (politician_id, comment, likes, sentiment, score))
        
        # 네이버 뉴스 처리
        news_list = get_naver_news(name)
        for news in news_list:
            full_text = news['title'] + ' ' + news['content']
            sentiment, score = analyze_sentiment(full_text)
            c.execute('''
                INSERT INTO naver_news 
                (politician_id, title, content, date, sentiment, score)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (politician_id, news['title'], news['content'], news['date'], sentiment, score))
    
    conn.commit()
    conn.close()
    print("✅ 모든 데이터 저장 완료")

if __name__ == "__main__":
    politicians = get_politicians()
    if politicians:
        save_to_db(politicians)
        print(f"{datetime.now()} - {len(politicians)}명 분석 완료")
    else:
        print("❗ 명단 수집 실패")
