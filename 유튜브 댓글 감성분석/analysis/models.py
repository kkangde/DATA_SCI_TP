from django.db import models

class CommentSentiment(models.Model):
    member_name = models.CharField(max_length=100)  # 국회의원 이름
    comment_text = models.TextField()               # 댓글 내용
    sentiment = models.CharField(max_length=20)     # 감성 결과 (예: 긍정, 부정, 중립)
    sentiment_score = models.FloatField(null=True, blank=True)  # 감성 점수(신뢰도), 없을 수도 있음
    created_at = models.DateTimeField(auto_now_add=True)  # 저장 시간

    def __str__(self):
        return f"{self.member_name} - {self.sentiment} ({self.sentiment_score})"
