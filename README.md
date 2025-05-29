# 정치인 여론 분석 웹페이지

## 📌 프로젝트 소개
트위터 API를 활용하여 정치인에 대한 여론을 수집, 감성 분석하고
웹 페이지에서 시각적으로 제공하는 프로젝트입니다.

## 🛠 기술 스택
- Python + Flask
- HTML / CSS
- MariaDB + SQL
- TextBlob (감성 분석)
- Git / GitHub

## 🔧 실행 방법
폴더 이동
cd C:\Users\deu\Desktop\ddd

가상환경
python -m venv venv -만들기
venv\Scripts\activate -활성화

디장고 라이브러리
pip install django
pip install google-api-python-client
pip install transformers
pip install torch
pip install requests

마이그레이션
python manage.py makemigrations
python manage.py migrate

서버실행
python manage.py runserver

국회의원 키
1343ad8c9a584b86a2493aa90cf51060

