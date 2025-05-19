import os
import django

# Django 환경 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sentiment_project.settings')
django.setup()

# 모델 import
from analysis.models import CommentSentiment

# 저장할 데이터 생성
cs = CommentSentiment(
    member_name="홍길동",
    comment_text="이 의원의 발언이 인상 깊었어요!",
    sentiment="긍정"
)
cs.save()

print("저장 완료!")
