import requests
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

# 🔑 Twitter API Bearer Token 설정 (여기에 본인의 토큰 입력)
bearer_token = "AAAAAAAAAAAAAAAAAAAAAH0X1AEAAAAAaRvJHfL65O7kcxn949jNiQbwB60%3DKGWr4sHmnLMLE6hQmkyLcIDB1FU6795XLC4U6rc3ZZ8IV0X0gL"

# 💬 감성 분석 모델 설정
model_name = "beomi/KcELECTRA-base-v2022"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)

# 🧠 감성 분석 함수
def transformer_sentiment(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = F.softmax(outputs.logits, dim=1)
    labels = ["Negative", "Positive"]
    pred = torch.argmax(probs)
    return labels[pred]

# 🐦 트위터 API 요청 함수
def search_tweets(query, max_results=10):
    url = f"https://api.twitter.com/2/tweets/search/recent?query={query}&max_results={max_results}&tweet.fields=lang"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "User-Agent": "SentimentBot/1.0"  # ✅ 한글 없는 User-Agent
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get("data", [])
    except requests.exceptions.RequestException as e:
        print("❌ Twitter API 요청 실패:", e)
        return []

# 🚀 실행 예제
if __name__ == "__main__":
    query = "국회의원 lang:ko"  # 한국어 트윗만 검색
    tweets = search_tweets(query)

    for tweet in tweets:
        text = tweet["text"]
        sentiment = transformer_sentiment(text)
        print(f"\n트윗: {text}\n감성 분석: {sentiment}")
