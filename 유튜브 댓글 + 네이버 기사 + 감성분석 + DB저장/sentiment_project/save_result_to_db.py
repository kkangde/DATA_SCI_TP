import os
import django

# Django 프로젝트 세팅 연결 (manage.py 있는 경로 기준)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sentiment_project.settings')
django.setup()

from analysis.models import SentimentResult

def save_result_to_db(lawmaker, title, comment, sentiment, confidence, video_url):
    SentimentResult.objects.create(
        lawmaker_name=lawmaker,
        video_title=title,
        comment=comment,
        sentiment=sentiment,
        confidence=confidence,
        video_url=video_url
    )
