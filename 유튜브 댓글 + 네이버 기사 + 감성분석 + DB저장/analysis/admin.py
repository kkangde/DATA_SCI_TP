from django.contrib import admin
from .models import CommentSentiment

@admin.register(CommentSentiment)
class CommentSentimentAdmin(admin.ModelAdmin):
    list_display = ('member_name', 'sentiment', 'sentiment_score', 'created_at')  # 보여줄 컬럼
    search_fields = ('member_name', 'comment_text')  # 검색 필드
    list_filter = ('sentiment',)  # 필터 옵션
    ordering = ('-created_at',)  # 최신순 정렬
