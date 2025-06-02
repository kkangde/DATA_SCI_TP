import os
import csv
import time
import requests
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ✅ 여러 API 키를 순환 사용
API_KEYS = [
    "AIzaSyCF4WX5FGjd9-zsb9PPLvNZfe5z-6mESL8",
    "AIzaSyC5GxrmYvYHJXDQub_0JMHhc4ArQHhzyoA",
    "AIzaSyCG9G9CSIHFmlRruVgshmU5-xGkhATlMZ0",
    "AIzaSyBY7zG5sVJ4VXlqd6JdCW4Q_29zNwox7V0"
]
current_key_index = 0

def get_youtube_client():
    global current_key_index
    key = API_KEYS[current_key_index]
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    return build("youtube", "v3", developerKey=key)

def search_video(name, max_retries=5):
    for _ in range(max_retries):
        youtube = get_youtube_client()
        try:
            res = youtube.search().list(
                q=name,
                part='snippet',
                type='video',
                maxResults=1
            ).execute()
            return res
        except HttpError as e:
            error_reason = e.error_details[0]['reason'] if hasattr(e, 'error_details') else str(e)
            if 'quotaExceeded' in str(e) or 'keyInvalid' in str(e) or 'badRequest' in str(e):
                print(f"🔁 API 키 오류 또는 쿼터 초과. 다음 키로 전환...")
                time.sleep(1)
                continue
            raise e
    print(f"❌ 모든 키 실패: {name}")
    return None

ASSEMBLY_API_KEY = "1343ad8c9a584b86a2493aa90cf51060"

def get_all_member_names():
    url = "https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu"
    params = {
        'KEY': ASSEMBLY_API_KEY,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 300
    }
    res = requests.get(url, params=params)
    if res.status_code == 200:
        data = res.json()
        rows = data.get("nwvrqwxyaytdsfvhu", [])[1].get("row", [])
        return [row["HG_NM"] for row in rows if "HG_NM" in row]
    print("❌ 국회의원 API 요청 실패:", res.status_code)
    return []

def save_video_ids_to_csv(member_names, output_csv='video_ids.csv'):
    existing = set()
    if os.path.exists(output_csv):
        with open(output_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            existing = {row['member_name'] for row in reader}

    with open(output_csv, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if os.stat(output_csv).st_size == 0:
            writer.writerow(['member_name', 'video_id', 'video_title', 'analyzed'])

        for name in member_names:
            if name in existing:
                continue

            res = search_video(name)
            if res and 'items' in res and res['items']:
                video = res['items'][0]
                video_id = video['id'].get('videoId', '')
                title = video['snippet'].get('title', '')
                writer.writerow([name, video_id, title, 'False'])
                print(f"✅ 저장: {name} - {video_id} ({title})")
            else:
                writer.writerow([name, '', '', 'False'])
                print(f"⚠️ 영상 없음 또는 요청 실패: {name}")

def main():
    members = get_all_member_names()
    save_video_ids_to_csv(members)

if __name__ == "__main__":
    main()
