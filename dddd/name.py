import requests

service_key = "1343ad8c9a584b86a2493aa90cf51060"
url = "https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu"

params = {
    'KEY': service_key,
    'Type': 'json',
    'pIndex': 1,
    'pSize': 300
}

response = requests.get(url, params=params)
data = response.json()

if 'nwvrqwxyaytdsfvhu' in data:
    rows = data['nwvrqwxyaytdsfvhu'][1]['row']
    print(f"총 의원 수: {len(rows)}\n")
    for member in rows:
        print(member.get('HG_NM'))
else:
    print("데이터 구조가 예상과 다릅니다.")
