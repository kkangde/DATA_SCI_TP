import csv
from googleapiclient.discovery import build

# YouTube API 키
YOUTUBE_API_KEY = 'YOUR_YOUTUBE_API_KEY'
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# 의원 이름 리스트 예시 (실제론 get_all_member_names() 같은 함수에서 받아오세요)
member_names = [
    '홍길동', '김철수', '이영희'
]

def fetch_representative_video_id(youtube, member_name):
    try:
        search_response = youtube.search().list(
            q=member_name,
            part='snippet',
            type='video',
            maxResults=1
        ).execute()

        items = search_response.get('items', [])
        if not items:
            return None

        video_id = items[0]['id']['videoId']
        return video_id
    except Exception as e:
        print(f"❌ {member_name} 검색 오류: {e}")
        return None

def save_video_ids_to_csv(data, filename='member_video_ids.csv'):
    with open(filename, mode='w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(['member_name', 'video_id'])
        writer.writerows(data)

def main():
    results = []
    for name in member_names:
        video_id = fetch_representative_video_id(youtube, name)
        if video_id:
            print(f"✅ {name}: {video_id}")
            results.append((name, video_id))
        else:
            print(f"⚠️ {name}: 영상 없음")

    save_video_ids_to_csv(results)
    print("CSV 저장 완료!")

if __name__ == "__main__":
    main()
