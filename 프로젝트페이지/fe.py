import os
import requests
import json
import re
import logging
import unicodedata
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from cachelib import SimpleCache

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

cache = SimpleCache()

# API 키 및 엔드포인트
API_KEY = "1343ad8c9a584b86a2493aa90cf51060"
CURRENT_API = "https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu"  # 22대 현역 의원
HISTORY_API = "https://open.assembly.go.kr/portal/openapi/ALLNAMEMBER"        # 역대 의원 (사진 포함)

# 정당 목록
PARTIES = [
    '국민의힘', '더불어민주당', '개혁신당', '기본소득당',
    '진보당', '무소속', '조국혁신당', '사회민주당'
]

def normalize_text(text):
    """문자열 정규화(공백, 특수문자 제거, 소문자 변환)"""
    if not text:
        return ""
    normalized = unicodedata.normalize('NFKD', str(text))
    return re.sub(r'[\s\-_\.\(\)/,;|·\\]+', '', normalized).lower()

def get_current_members():
    """현재(22대) 국회의원 목록 조회"""
    cached = cache.get('current_members')
    if cached:
        return cached

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
                    res = requests.get(CURRENT_API, params=params, headers=headers, timeout=15)
                    res.raise_for_status()
                    break
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries - 1:
                        logger.error(f"API 호출 실패: {e}")
                        raise
                    continue

            data = res.json()
            rows = []
            if "ALLNAMEMBER" in data and isinstance(data["ALLNAMEMBER"], list) and len(data["ALLNAMEMBER"]) > 1:
                rows = data["ALLNAMEMBER"][1].get("row", [])

            if not rows:
                break

            members.extend(rows)

            if len(rows) < page_size:
                break
            page += 1

        cache.set('current_members', members, timeout=5*60)
        return members

    except Exception as e:
        logger.error(f"get_current_members 예외 발생: {e}")
        raise

def get_historical_members():
    """역대 국회의원 목록 조회 (사진 포함)"""
    cached = cache.get('historical_members')
    if cached:
        return cached

    params = {
        "KEY": API_KEY,
        "Type": "json",
        "pSize": 300  # 한 번에 충분히 많은 데이터 받기
    }

    try:
        res = requests.get(HISTORY_API, params=params)
        res.raise_for_status()
        data = res.json()
        historical = data.get("ALLNAMEMBER", [{}])[1].get("row", [])
        cache.set('historical_members', historical, timeout=24*60*60)  # 1일 캐시
        return historical
    except Exception as e:
        logger.error(f"get_historical_members 예외 발생: {e}")
        raise

def merge_member_data(current, historical):
    """현재 의원 데이터에 사진 추가"""
    for member in current:
        # 이름(HG_NM)으로 매칭 (동명이인 주의, 가능하면 EMPL_NO 사용 권장)
        match = next((h for h in historical if h.get("HG_NM") == member.get("HG_NM")), None)
        if match:
            member["NAAS_PIC"] = match.get("NAAS_PIC")  # 사진 URL 추가
    return current

@app.route('/')
def home():
    """메인 페이지: 모든 국회의원 목록 표시"""
    try:
        current = get_current_members()
        historical = get_historical_members()
        merged = merge_member_data(current, historical)
        return render_template('s.html', members=merged)
    except Exception as e:
        logger.error(f"홈페이지 로드 실패: {e}")
        return jsonify({"error": "내부 서버 오류"}), 500

@app.route('/party/<party_name>')
def party_page(party_name):
    """정당별 국회의원 목록 페이지"""
    if party_name not in PARTIES:
        logger.warning(f"존재하지 않는 정당: {party_name}")
        return jsonify({"error": "존재하지 않는 정당"}), 404

    try:
        current = get_current_members()
        historical = get_historical_members()
        merged = merge_member_data(current, historical)
        party_members = [
            m for m in merged
            if any(
                normalize_text(p) in normalize_text(m.get('POLY_NM', ''))
                for p in [party_name, '새진보연합', '기본소득당·사회민주당 연합']
            )
        ]
        return render_template(f'{party_name}.html', members=party_members)
    except Exception as e:
        logger.error(f"정당 페이지 로드 실패: {e}")
        return jsonify({"error": "내부 서버 오류"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
