import urllib.request
import json

# 1. Login
url = 'http://localhost:8000/login'
data = json.dumps({'email': 'tester@farm.com', 'password': 'password123'}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as res:
    login_data = json.loads(res.read().decode('utf-8'))

token = login_data['access_token']

# 2. Get plants
plant_url = 'http://localhost:8000/plants'
p_req = urllib.request.Request(plant_url, headers={'Authorization': f'Bearer {token}'})
with urllib.request.urlopen(p_req) as res:
    plants = json.loads(res.read().decode('utf-8'))
    plant_id = plants[0]['plant_id']
    print('Using plant:', plant_id)

# 3. Multipart upload
boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
with open('sample_leaf.png', 'rb') as f:
    img_bytes = f.read()

part1 = f'--{boundary}\r\nContent-Disposition: form-data; name="plant_id"\r\n\r\n{plant_id}\r\n'.encode('utf-8')
part2 = f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="sample_leaf.png"\r\nContent-Type: image/png\r\n\r\n'.encode('utf-8')
part3 = f'\r\n--{boundary}--\r\n'.encode('utf-8')

body = part1 + part2 + img_bytes + part3

predict_url = 'http://localhost:8000/predict'
predict_req = urllib.request.Request(
    predict_url,
    data=body,
    headers={
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'Authorization': f'Bearer {token}'
    }
)

with urllib.request.urlopen(predict_req) as res:
    pred_res = json.loads(res.read().decode('utf-8'))
    print('\n==============================')
    print('>>> PREDICTION SUCCESSFUL! <<<')
    print('==============================')
    print('Report ID:', pred_res.get('report_id'))
    print('Diagnosis:', pred_res.get('disease'))
    print('Confidence:', pred_res.get('confidence'))
    print('Severity:', pred_res.get('severity'))
    print('Trend:', pred_res.get('trend'))
    print('Care Tips Count:', len(pred_res.get('tips', [])))
