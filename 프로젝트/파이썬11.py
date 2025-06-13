import requests
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import urllib.parse
from transformers import pipeline
import re
import html
import logging
import unicodedata
from cachelib import SimpleCache
import sqlite3
import os

DB_PATH1 = r"c:\Users\Hangh\OneDrive\바탕 화면\DATA_SCI_TP\dddd\db.sqlite3"
DB_PATH2 = r"c:\Users\Hangh\OneDrive\바탕 화면\DATA_SCI_TP\dddd\political_analysis.db"
conn = sqlite3.connect(DB_PATH2)
conn.execute("""
CREATE TABLE IF NOT EXISTS politicians (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    party TEXT
)
""")
conn.execute("""
CREATE TABLE IF NOT EXISTS news_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    politician_id INTEGER,
    title TEXT,
    content TEXT,
    pub_date TEXT,
    link TEXT,
    label TEXT,
    score REAL,
    FOREIGN KEY(politician_id) REFERENCES politicians(id)
)
""")
conn.commit()
conn.close()
app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

cache = SimpleCache()

API_KEY = "f387f85a7e104ed4834c91779eef1249"
BASE_URL = "https://open.assembly.go.kr/portal/openapi/ALLNAMEMBER"
sentiment_pipeline = pipeline("sentiment-analysis", model="WhitePeak/bert-base-cased-Korean-sentiment")
client_id = "ppH1uMGA4_jWdMzMYMH4"
client_secret = "j5wtomptl2"

PARTIES = [
    '국민의힘', '더불어민주당', '개혁신당', '기본소득당',
    '진보당', '무소속', '조국혁신당', '사회민주당'
]

def normalize_text(text):
    """공백, 특수문자, 대소문자, 유니코드 모두 제거"""
    if not text:
        return ""
    normalized = unicodedata.normalize('NFKD', str(text))
    return re.sub(r'[\s\-_\.\(\)/,;|·\\]+', '', normalized).lower()

def is_22nd_member(member):
    """22대 의원 여부 판별"""
    terms = (member.get('GTELT_ERACO') or '').split(',')
    for term in terms:
        term_num = re.sub(r'[^0-9]', '', term.strip())
        if term_num == '22':
            return True
    return False

# 예외 처리 매핑 테이블 (이름: 실제 소속 정당)
EXCEPTION_PARTY_MAP = {
    '한창민': '사회민주당',
    '우원식': '무소속',
    '김종민': '무소속',
    '전종덕': '진보당',
    '정혜경': '진보당'
    # 추가 예외 항목 필요시 여기에 작성
}

def get_22nd_party(member):
    # 예외 처리 우선 적용
    member_name = member.get('NAAS_NM', '')
    if member_name in EXCEPTION_PARTY_MAP:
        return EXCEPTION_PARTY_MAP[member_name]
    
    # 기존 처리 로직
    raw_parties = (member.get('PLPT_NM') or '').replace('\\', '/').strip()
    parties = [
        p.strip()
        for p in raw_parties.split('/')
        if p.strip() and p.strip() not in ('-', 'N/A')
    ]
    
    if not parties:
        return None
    
    current_party = parties[-1]
    if current_party.endswith(('연합', '교섭단체', '연대')):
        return parties[-2] if len(parties) >= 2 else current_party
    
    return current_party

def get_all_members():
    cached_data = cache.get('all_members')
    if cached_data is not None:
        logger.info(f"캐시에서 {len(cached_data)}명의 의원 데이터 반환")
        return cached_data

    members = []
    page = 1
    page_size = 100
    max_retries = 3

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate"
    }

    try:
        while True:
            params = {
                "KEY": API_KEY,
                "Type": "json",
                "pIndex": page,
                "pSize": page_size
            }
            for attempt in range(max_retries):
                try:
                    logger.info(f"API 호출 중... 페이지: {page}, 시도: {attempt + 1}")
                    res = requests.get(BASE_URL, params=params, headers=headers, timeout=15)
                    res.raise_for_status()
                    break
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries - 1:
                        raise e
                    logger.warning(f"API 호출 실패, 재시도 중... {e}")
                    continue

            data = res.json()
            rows = []
            if "ALLNAMEMBER" in data and isinstance(data["ALLNAMEMBER"], list) and len(data["ALLNAMEMBER"]) > 1:
                rows = data["ALLNAMEMBER"][1].get("row", [])

            if not rows:
                logger.info(f"페이지 {page}에서 데이터 없음. 종료")
                break

            for m in rows:
                members.append(m)

            if len(rows) < page_size:
                break
            page += 1

        cache.set('all_members', members, timeout=5 * 60)
        logger.info(f"총 {len(members)}명의 국회의원 데이터 로드 완료")
        return members

    except requests.exceptions.RequestException as e:
        logger.error(f"API 요청 오류: {e}")
        return []
    except Exception as e:
        logger.error(f"get_all_members 예외 발생: {e}")
        return []

@app.route('/')
def home():
    all_members = get_all_members()
    members_22nd = [m for m in all_members if is_22nd_member(m)]
    logger.info(f"메인 페이지 로드: {len(members_22nd)}명 의원")
    return render_template('s.html', parties=PARTIES, members=members_22nd)

@app.route('/party/<party_name>')
def party_page(party_name):
    if party_name not in PARTIES:
        logger.warning(f"존재하지 않는 정당: {party_name}")
        return "페이지를 찾을 수 없습니다.", 404

    all_members = get_all_members()
    party_members = []
    
    for m in all_members:
        if not is_22nd_member(m):
            continue
            
        current_party = get_22nd_party(m)
        if not current_party:
            continue
            
        # 정당명 정규화 후 비교
        if normalize_text(current_party) == normalize_text(party_name):
            party_members.append({
                **m,
                'CURRENT_PARTY': current_party  # 현재 정당 정보 추가
            })
    
    logger.info(f"{party_name} 페이지: {len(party_members)}명 의원 반환")
    return render_template(f'{party_name}.html', members=party_members)

@app.route('/get_22nd_names')
def get_22nd_names():
    """22대 국회의원 API"""
    members = get_all_members()
    members_22nd = [m for m in members if is_22nd_member(m)]
    return jsonify({
        "success": True,
        "members": members_22nd,
        "total_count": len(members_22nd)
    })

@app.route('/get_party_members/<party_name>')
def get_party_members(party_name):
    """특정 정당 22대 의원만 반환 (현재 정당 기준)"""
    all_members = get_all_members()
    party_members = []
    
    for m in all_members:
        if not is_22nd_member(m):
            continue
            
        current_party = get_22nd_party(m)
        if not current_party:
            continue
            
        if normalize_text(current_party) == normalize_text(party_name):
            party_members.append({
                **m,
                'CURRENT_PARTY': current_party
            })
    
    return jsonify({
        "success": True,
        "party": party_name,
        "members": party_members,
        "total_count": len(party_members)
    })

# 디버깅용 엔드포인트 추가
@app.route('/debug/party_check/<party_name>')
def debug_party_check(party_name):
    """무소속 의원 디버깅"""
    all_members = get_all_members()
    debug_info = []
    
    for m in all_members:
        if is_22nd_member(m):
            current_party = get_22nd_party(m)
            debug_info.append({
                "name": m.get('NAAS_NM'),
                "full_party_history": m.get('PLPT_NM'),
                "extracted_current_party": current_party,
                "matches_target": normalize_text(current_party) == normalize_text(party_name) if current_party else False
            })
    
    return jsonify({
        "target_party": party_name,
        "debug_data": debug_info,
        "matching_members": [d for d in debug_info if d["matches_target"]]
    })

@app.route('/analyze_politician', methods=['GET'])
def get_politician_analysis():
    """정치인 감정 분석"""
    name = request.args.get('name')
    if not name:
        return jsonify({"error": "Name parameter is required."}), 400

    try:
        query = urllib.parse.quote(name)
        url = f"https://openapi.naver.com/v1/search/news.json?query={query}&display=3&sort=date"
        headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}

        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
        data = res.json()

        news_articles = []
        for item in data.get("items", []):
            title = re.sub(r"<[^>]+>", "", item.get("title", ""))
            description = re.sub(r"<[^>]+>", "", item.get("description", ""))
            text = f"{title} {description}"[:512]

            sentiment = sentiment_pipeline(text)[0]
            news_articles.append({
                "title": title,
                "description": description,
                "link": item.get("link", ""),
                "sentiment_label": sentiment['label'],
                "sentiment_score": round(sentiment['score'], 2)
            })

        logger.info(f"{name} 뉴스 분석 완료: {len(news_articles)}개 기사")
        return jsonify({
            "politician_name": name,
            "news_articles": news_articles
        })

    except Exception as e:
        logger.error(f"감정 분석 오류: {e}")
        return jsonify({"error": str(e)}), 500

# DB 파일 경로 (상대경로)
DB_PATH1 = os.path.abspath(os.path.join(os.path.dirname(__file__), '../dddd/db.sqlite3'))
DB_PATH2 = os.path.abspath(os.path.join(os.path.dirname(__file__), 'dddd/political_analysis.db'))

@app.route('/comments')
def show_comments():
    conn = sqlite3.connect(DB_PATH1)
    cursor = conn.cursor()
    cursor.execute("SELECT member_name, comment_text, sentiment, sentiment_score, like_count, created_at FROM analysis_commentsentiment ORDER BY created_at DESC")
    comments = cursor.fetchall()
    conn.close()
    return render_template('comments.html', comments=comments)

@app.route('/tables')
def show_tables():
    conn = sqlite3.connect(DB_PATH1)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    conn.close()
    return '<br>'.join([t[0] for t in tables])

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"내부 서버 오류: {error}")
    return jsonify({"error": "내부 서버 오류가 발생했습니다."}), 500

@app.route('/news')
def show_news():
    conn = sqlite3.connect(DB_PATH2)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT n.title, n.content, n.pub_date, n.link, n.label, n.score, p.name as politician_name
        FROM news_articles n
        LEFT JOIN politicians p ON n.politician_id = p.id
        ORDER BY n.pub_date DESC
        LIMIT 100
    """)
    news = cursor.fetchall()
    conn.close()
    return render_template('news.html', news=news)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=4880)
