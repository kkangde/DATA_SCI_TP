# save_video.py
import os
import csv
import requests
from googleapiclient.discovery import build

YOUTUBE_API_KEY = ("AIzaSyBNqTeD-YJ_5zSeqhKFY0s1Sno_ai2TtQ8")
ASSEMBLY_API_KEY = ("1343ad8c9a584b86a2493aa90cf51060")
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

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
            try:
                res = youtube.search().list(
                    q=name,
                    part='snippet',
                    type='video',
                    maxResults=1
                ).execute()
                if res['items']:
                    video = res['items'][0]
                    video_id = video['id']['videoId']
                    title = video['snippet']['title']
                    writer.writerow([name, video_id, title, 'False'])
                    print(f"✅ 저장: {name} - {video_id} ({title})")
                else:
                    writer.writerow([name, '', '', 'False'])
                    print(f"⚠️ 영상 없음: {name}")
            except Exception as e:
                print(f"❌ 오류: {name} - {e}")

def main():
    members = get_all_member_names()
    save_video_ids_to_csv(members)

if __name__ == "__main__":
    main()
