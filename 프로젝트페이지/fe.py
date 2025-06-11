import os
import requests
import json
import re
import logging
import unicodedata
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from cachelib import SimpleCache
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

cache = SimpleCache()

API_KEY = os.getenv("ASSEMBLY_API_KEY", "your_default_api_key")
CURRENT_API = "https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu"
HISTORY_API = "https://open.assembly.go.kr/portal/openapi/ALLNAMEMBER"

PARTIES = {
    '국민의힘': 'party_template.html',
    '더불어민주당': 'party_template.html',
    '개혁신당': 'party_template.html',
    '기본소득당': 'party_template.html',
    '진보당': 'party_template.html',
    '무소속': 'party_template.html',
    '조국혁신당': 'party_template.html',
    '사회민주당': 'party_template.html'
}

def normalize_text(text):
    if not text:
        return ""
    normalized = unicodedata.normalize('NFKD', str(text))
    return re.sub(r'[\s\-_.()\/,;|·\\]+', '', normalized).lower()

def get_current_members():
    cached = cache.get('current_members')
    if cached:
        return cached

    members = []
    page = 1
    page_size = 100
    max_retries = 3

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
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
                    res = requests.get(CURRENT_API, params=params, headers=headers, timeout=10)
                    res.raise_for_status()
                    break
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries - 1:
                        logger.error(f"API 호출 실패: {e}")
                        raise

            data = res.json()
            rows = []
            if "nwvrqwxyaytdsfvhu" in data and isinstance(data["nwvrqwxyaytdsfvhu"], list):
                rows = data["nwvrqwxyaytdsfvhu"][1].get("row", [])

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
    cached = cache.get('historical_members')
    if cached:
        return cached

    params = {
        "KEY": API_KEY,
        "Type": "json",
        "pSize": 1000  # 충분한 크기
    }

    try:
        res = requests.get(HISTORY_API, params=params)
        res.raise_for_status()
        data = res.json()

        historical = []
        allnamember = data.get("ALLNAMEMBER", [])
        if isinstance(allnamember, list) and len(allnamember) > 1:
            historical = allnamember[1].get("row", [])
        else:
            logger.warning("예상치 못한 ALLNAMEMBER 응답 구조")
            logger.warning(json.dumps(data, ensure_ascii=False, indent=2))

        cache.set('historical_members', historical, timeout=24*60*60)
        return historical

    except Exception as e:
        logger.error(f"get_historical_members 예외 발생: {e}")
        raise
    
    

def merge_member_data(current, historical):
    """현재 의원 데이터에 사진 및 기타 상세 정보 추가"""
    for member in current:
        match = next((h for h in historical if h.get("HG_NM") == member.get("HG_NM")), None)
        if match:
            member.update({
                "NAAS_PIC": match.get("NAAS_PIC"),
                "EMAIL": match.get("EMAIL"),
                "HOMEPAGE": match.get("HOMEPAGE"),
                "TEL_NO": match.get("TEL_NO"),
                "BTH_DATE": match.get("BTH_DATE"),
                "POSITION": match.get("MEM_TITLE"),  # 예시
                # 필요시 더 추가
            })
    return current


@app.route('/')
def home():
    try:
        current = get_current_members()
        historical = get_historical_members()
        merged = merge_member_data(current, historical)
        return render_template('index.html', members=merged)
    except Exception as e:
        logger.error(f"홈페이지 로드 실패: {e}")
        return jsonify({"error": "내부 서버 오류"}), 500

@app.route('/party/<party_name>')
def party_page(party_name):
    if party_name not in PARTIES:
        logger.warning(f"존재하지 않는 정당: {party_name}")
        return jsonify({"error": "존재하지 않는 정당"}), 404

    try:
        current = get_current_members()
        historical = get_historical_members()
        merged = merge_member_data(current, historical)
        party_members = [
            m for m in merged
            if normalize_text(party_name) in normalize_text(m.get('POLY_NM', ''))
        ]
        return render_template(PARTIES[party_name], members=party_members, party=party_name)
    except Exception as e:
        logger.error(f"정당 페이지 로드 실패: {e}")
        return jsonify({"error": "내부 서버 오류"}), 500

@app.route('/api/party/<party_name>')
def api_party_members(party_name):
    if party_name not in PARTIES:
        logger.warning(f"존재하지 않는 정당: {party_name}")
        return jsonify({"error": "존재하지 않는 정당"}), 404

    try:
        current = get_current_members()
        historical = get_historical_members()
        merged = merge_member_data(current, historical)
        party_members = [
            m for m in merged
            if normalize_text(party_name) in normalize_text(m.get('POLY_NM', ''))
        ]
        result = [
            {
                "name": m.get("HG_NM", ""),
                "party": m.get("POLY_NM", ""),
                "image_url": m.get("NAAS_PIC", "")
            }
            for m in party_members
        ]
        return jsonify(result)
    except Exception as e:
        logger.error(f"정당 API 페이지 로드 실패: {e}")
        return jsonify({"error": "내부 서버 오류"}), 500
    
@app.route('/api-docs')
def api_docs():
    return render_template('api_docs.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
