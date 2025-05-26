import csv
from googleapiclient.discovery import build
import requests

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

# YouTube API 키 및 빌드
YOUTUBE_API_KEY = 'AIzaSyBNqTeD-YJ_5zSeqhKFY0s1Sno_ai2TtQ8'
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# 영상 ID 저장 함수
def save_video_ids_to_csv(member_names, output_csv='video_ids.csv'):
    with open(output_csv, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['member_name', 'video_id', 'video_title'])

        for name in member_names:
            try:
                search_response = youtube.search().list(
                    q=name,
                    part='snippet',
                    type='video',
                    maxResults=1
                ).execute()

                if search_response['items']:
                    video = search_response['items'][0]
                    video_id = video['id']['videoId']
                    video_title = video['snippet']['title']
                    writer.writerow([name, video_id, video_title])
                    print(f"✅ 저장: {name} - {video_id} ({video_title})")
                else:
                    print(f"⚠️ 영상 없음: {name}")

            except Exception as e:
                print(f"❌ 오류 발생: {name} - {e}")

# 실행
OPEN_API_KEY = "1343ad8c9a584b86a2493aa90cf51060"
member_names = get_all_member_names(OPEN_API_KEY)
save_video_ids_to_csv(member_names)
