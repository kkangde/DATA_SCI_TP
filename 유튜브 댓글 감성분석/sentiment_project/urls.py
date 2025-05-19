from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('analysis/', include('analysis.urls')),
    path('', lambda request: redirect('analysis/')),  # 빈 경로 접근 시 /analysis/ 로 리다이렉트
]
