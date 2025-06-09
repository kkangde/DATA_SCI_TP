from django.urls import path
from . import views

urlpatterns = [
    path('', views.sentiment_list, name='sentiment_list'),
]
