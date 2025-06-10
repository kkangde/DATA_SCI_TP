import sqlite3
import requests
import urllib.parse
import json
import re
import html
import time
from transformers import pipeline

# 국회의원 API 인증키
CONGRESS_API_KEY = "1343ad8c9a584b86a2493aa90cf51060"

# 네이버 API 인증 정보
client_id = "ppH1uMGA4_jWdMzMYMH4"
client_secret = "j5wtomptl2"

# 감정 분석 파이프라인 (CPU 사용)
sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="nlptown/bert-base-multilingual-uncased-sentiment",
    device=-1
)

def get_db_connection():
    conn = sqlite3.connect('political_analysis.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS politicians (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            party TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS news_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            politician_id INTEGER,
            title TEXT,
            content TEXT,
            pub_date TEXT,
            link TEXT,
            FOREIGN KEY(politician_id) REFERENCES politicians(id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sentiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_id INTEGER,
            label TEXT,
            score REAL,
            FOREIGN KEY(news_id) REFERENCES news_articles(id)
        )
    ''')
    conn.commit()
    conn.close()

def fetch_members_of_parliament():
    url = "https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu"
    params = {
        "KEY": CONGRESS_API_KEY,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 300
    }
    res = requests.get(url, params=params)
    if res.status_code == 200:
        data = res.json()
        rows = data.get("nwvrqwxyaytdsfvhu", [])[1].get("row", [])
        return [(row["HG_NM"], row.get("POLY_NM", "무소속")) for row in rows if "HG_NM" in row]
    print("❌ 국회의원 API 요청 실패:", res.status_code)
    return []

def clean_text(text):
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text)

def analyze_politician(name, party):
    query = urllib.parse.quote(name)
    url = f"https://openapi.naver.com/v1/search/news.json?query={query}&display=3&sort=date"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
        "User-Agent": "Mozilla/5.0"
    }

    conn = get_db_connection()
    try:
        # 정치인 정보 저장 (별도 트랜잭션)
        conn.execute('INSERT OR IGNORE INTO politicians (name, party) VALUES (?, ?)', (name, party))
        politician_id = conn.execute('SELECT id FROM politicians WHERE name = ?', (name,)).fetchone()[0]
        conn.commit()  # 트랜잭션 종료

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            result = response.json()
            print(f"\n[{name}] 관련 최신 뉴스 3건:")

            # 뉴스 기사 트랜잭션 시작
            for idx, item in enumerate(result.get("items", []), 1):
                title = clean_text(item.get("title", ""))
                description = clean_text(item.get("description", ""))
                pub_date = item.get("pubDate", "")
                link = item.get("originallink", "")

                # 뉴스 기사 저장
                conn.execute('''
                    INSERT INTO news_articles 
                    (politician_id, title, content, pub_date, link)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    politician_id,
                    title,
                    description,
                    pub_date,
                    link
                ))
                news_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

                # 감정 분석 결과 저장
                text = (title + " " + description)[:512]
                sentiment = sentiment_pipeline(text)[0]
                conn.execute('''
                    INSERT INTO sentiments 
                    (news_id, label, score)
                    VALUES (?, ?, ?)
                ''', (news_id, sentiment['label'], sentiment['score']))

                print(f"\n{idx}. 제목: {title}")
                print(f"   저장 완료 (뉴스 ID: {news_id})")
                time.sleep(0.5)
            conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"⚠️ {name} 처리 중 오류 발생: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    members = fetch_members_of_parliament()
    if not members:
        print("❗ 국회의원 명단을 수정할 수 없습니다. 프로그램을 종료합니다.")
        exit()
    print(f"✅ 총 {len(members)}명의 국회의원 분석 시작...")
    for idx, (name, party) in enumerate(members, 1):
        print(f"\n{'='*40}")
        print(f"{idx}/{len(members)} 분석 진행 중: {name}({party})")
        analyze_politician(name, party)
    print("\n✅ 모든 국회의원 분석 완료! 데이터베이스를 확인하세요.")
