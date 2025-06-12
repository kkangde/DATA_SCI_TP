from django.shortcuts import render
from .models import CommentSentiment

def sentiment_list(request):
    comments = CommentSentiment.objects.order_by('-created_at')  # 최신순 정렬
    return render(request, 'analysis/sentiment_list.html', {'comments': comments})
