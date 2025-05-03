import requests
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

# 🔑 Twitter API Bearer Token 설정 (본인 토큰으로 교체!)
bearer_token = "여기에_본인의_Bearer_Token_붙여넣기"

# 💬 감성 분석 모델 설정 (공개된 한국어 모델)
model_name = "beomi/KcELECTRA-base-v2022"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# 🧠 감성 분석 함수
def transformer_sentiment(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    outputs = model(**inputs)
    probs = F.softmax(outputs.logits, dim=1)
    labels = ["Negative", "Positive"]  # 이 모델은 이진 분류 (부정/긍정)
    pred = torch.argmax(probs)
    return labels[pred]

# 🐦 트위터 API 요청 함수
def search_tweets(query, max_results=10):
    url = f"https://api.twitter.com/2/tweets/search/recent?query={query}&max_results={max_results}&tweet.fields=lang"
    headers = {
        "Authorization": f"Bearer {bearer_token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        print("❌ Twitter API Error:", response.status_code, response.text)
        return []

# 🚀 실행 예제
if __name__ == "__main__":
    query = "국회의원 lang:ko"  # 한국어 트윗만 검색
    tweets = search_tweets(query)

    for tweet in tweets:
        text = tweet["text"]
        sentiment = transformer_sentiment(text)
        print(f"\n트윗: {text}\n감성 분석: {sentiment}")
