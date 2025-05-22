import requests # requests 라이브러리 추가              #김현민 
import os # os 라이브러리 추가 (API 키를 환경 변수에서 가져오기 위함)
from transformers import pipeline

# 키워드 정의
pos_words = ["지지", "응원", "좋은", "최고", "기분", "훌륭", "성과", "긍정적", "성공"]
neg_words = ["실망", "문제", "반대", "논란", "비판", "싫고", "짜증", "화가", "부정적", "실패"]

try:
    print("감성 분석 모델 로딩")
    model = pipeline("sentiment-analysis", model="WhitePeak/bert-base-cased-Korean-sentiment") #한국 정치 분석하기에 적합한 허깅페이스의 분석 프로그램 
    print("감성 분석 모델 로드 완료.")
except Exception as e:
    print(f"오류 발생: 모델 로드 실패 (현재 코드에서는 직접 사용되지 않음)\n{e}")
    model = None

def get_model_sentiment(text):
    #Hugging Face 모델을 사용하여 텍스트의 감성을 분석
    if model:
        try:
            res = model(text)[0]
            label = res['label']
            confidence = res['score']
            if label == '긍정':
                return {"label": "긍정적", "score": confidence}
            elif label == '부정':
                return {"label": "부정적", "score": confidence}
            else:
                return {"label": "중립", "score": confidence}
        except Exception as e:
            print(f"오류 발생: 텍스트 분석 중 오류 - {e}")
            return {"label": "오류", "score": 0.0}
    else:
        return {"label": "오류", "score": 0.0, "message": "감성 분석 모델이 로드되지 않았습니다."}

def analyze_text_sentiment(text):
    """
    오직 키워드 개수만을 기준으로 감성을 판단합니다.
    """
    pos_count = sum(1 for word in pos_words if word in text) #긍정
    neg_count = sum(1 for word in neg_words if word in text) #부정 

    label = "중립" # 기본값
    score = 0.0    # 점수는 키워드 매치 개수로 임시 설정

    if pos_count > neg_count:
        label = "긍정적"
        score = pos_count
    elif neg_count > neg_count: # 이 부분도 neg_count > pos_count로 수정해야 합니다.
        label = "부정적"
        score = neg_count

    kw_info = ""
    if pos_count > 0:
        found_pos_words = [word for word in pos_words if word in text]
        kw_info += f"(긍정 키워드 {pos_count}개 포함: {', '.join(found_pos_words)})"

    if neg_count > 0:
        found_neg_words = [word for word in neg_words if word in text]
        if kw_info: # 이미 긍정 키워드 정보가 있으면 쉼표 추가
            kw_info += ", "
        kw_info += f"(부정 키워드 {neg_count}개 포함: {', '.join(found_neg_words)})"

    return f"느낌: {label} ({score:.3f}){kw_info}"
#---------------------------------------------------------------------------------------------------------------------------------- 밑에껀 서진씨가 함 
if __name__ == "__main__":
    # 네이버 API 인증 정보 (환경 변수 또는 직접 입력)
    # 보안을 위해 환경 변수 사용을 권장합니다.
    # 예시: os.environ.get("NAVER_CLIENT_ID")
    client_id = "아이디"  # 여기에 본인의 네이버 Client ID 입력
    client_secret = "비밀번호 " # 여기에 본인의 네이버 Client Secret 입력

    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }

    # 분석할 검색어 입력
    search_query = input("분석하고 싶은 정치인/주제 이름을 입력하세요: ") #정치인 입력 

    # 네이버 뉴스 API 호출
    # 수정된 URL: 불필요한 마크다운 링크 문법 제거
    url = f"https://openapi.naver.com/v1/search/news.json?query={search_query}&display=10&sort=date" #갯수  조정 
    news_articles = []

    try:
        response = requests.get(url, headers=headers, timeout=10) # 타임아웃 추가
        response.raise_for_status() # HTTP 오류가 발생하면 예외 발생
        result = response.json()
        
        if 'items' in result:
            for item in result['items']:
                # HTML 태그 제거 및 불필요한 문자 제거
                title = item['title'].replace("<b>", "").replace("</b>", "").replace("&quot;", "\"")
                description = item['description'].replace("<b>", "").replace("</b>", "").replace("&quot;", "\"")
                news_articles.append(f"{title} {description}") # 제목과 내용을 합쳐서 분석

            print(f"--- '{search_query}' 관련 네이버 뉴스 감성 분석 ({len(news_articles)}개) ---")
            
            # 뉴스 기사별 감성 분석
            for i, article_text in enumerate(news_articles):
                sentiment_result = analyze_text_sentiment(article_text)
                print(f"뉴스 {i+1}:")
                print(f"원문 (일부): '{article_text[:100]}...'") # 긴 기사의 경우 앞 100자만 표시
                print(f"분석 결과: {sentiment_result}")
                print("=" * 70)
        else:
            print("네이버 뉴스 API에서 'items'를 찾을 수 없습니다. 응답 구조를 확인하세요.")

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 오류 발생: {http_err} (상태 코드: {response.status_code}, 응답: {response.text})")
        if response.status_code == 401:
            print("Client ID 또는 Client Secret이 유효하지 않거나 할당량이 초과되었을 수 있습니다.")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"연결 오류 발생: 인터넷 연결을 확인하거나 네이버 API 서버에 문제가 있을 수 있습니다.\n{conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"요청 시간 초과: 네이버 API 응답이 너무 느리거나 인터넷 연결이 불안정합니다.\n{timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"요청 처리 중 오류 발생: {req_err}")
    except Exception as e:
        print(f"예상치 못한 오류 발생: {e}")
