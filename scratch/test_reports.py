import urllib.request
import json
import time
import io
import uuid
import mimetypes
from PIL import Image

base_url = "http://127.0.0.1:8000"

def encode_multipart_formdata(fields, files):
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
    CRLF = b"\r\n"
    parts = []
    for key, value in fields.items():
        parts.append(f"--{boundary}".encode("utf-8"))
        parts.append(f'Content-Disposition: form-data; name="{key}"'.encode("utf-8"))
        parts.append(b"")
        parts.append(str(value).encode("utf-8"))
    for key, (filename, value) in files.items():
        parts.append(f"--{boundary}".encode("utf-8"))
        parts.append(f'Content-Disposition: form-data; name="{key}"; filename="{filename}"'.encode("utf-8"))
        parts.append(f"Content-Type: {mimetypes.guess_type(filename)[0] or 'application/octet-stream'}".encode("utf-8"))
        parts.append(b"")
        parts.append(value)
    parts.append(f"--{boundary}--".encode("utf-8"))
    parts.append(b"")
    body = CRLF.join(parts)
    content_type = f"multipart/form-data; boundary={boundary}"
    return content_type, body

def get_auth_token():
    url = f"{base_url}/login"
    data = {
        "email": "ramesh@gmail.com",
        "password": "securepassword123"
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode("utf-8"))
        return res["access_token"]

def create_plant(token, crop_name, plant_name):
    url = f"{base_url}/plants"
    data = {
        "crop_name": crop_name,
        "plant_name": plant_name
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        },
        method="POST"
    )
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode("utf-8"))
        return res["plant_id"]

def create_dummy_image():
    img = Image.new("RGB", (200, 200), color="green")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    return img_byte_arr.getvalue()

def upload_scan(token, plant_id, img_bytes):
    url = f"{base_url}/predict"
    fields = {"plant_id": plant_id}
    files = {"image": ("leaf.jpg", img_bytes)}
    content_type, body = encode_multipart_formdata(fields, files)
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": content_type,
            "Authorization": f"Bearer {token}"
        },
        method="POST"
    )
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode("utf-8"))
        return res

def get_reports(token, plant_id=None):
    url = f"{base_url}/reports"
    if plant_id:
        url += f"?plant_id={plant_id}"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
        method="GET"
    )
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode("utf-8"))
        return res

def get_report_detail(token, report_id):
    url = f"{base_url}/reports/{report_id}"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
        method="GET"
    )
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode("utf-8"))
        return res

def get_plant_recovery(token, plant_id):
    url = f"{base_url}/plants/{plant_id}/recovery"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
        method="GET"
    )
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode("utf-8"))
        return res

if __name__ == "__main__":
    time.sleep(1)
    try:
        print("Authenticating...")
        token = get_auth_token()
        print("Authenticated successfully.")
        
        print("\nCreating a test plant...")
        plant_id = create_plant(token, "Tomato", "Reports Test Tomato")
        print(f"Test Plant ID: {plant_id}")
        
        print("\nUploading 2 scans...")
        img_bytes = create_dummy_image()
        scan1 = upload_scan(token, plant_id, img_bytes)
        print(f"Scan 1: {scan1['disease']}, {scan1['severity']}, Trend: {scan1['trend']}")
        time.sleep(0.5)
        scan2 = upload_scan(token, plant_id, img_bytes)
        print(f"Scan 2: {scan2['disease']}, {scan2['severity']}, Trend: {scan2['trend']}")
        
        print("\nListing all reports for this plant...")
        reports = get_reports(token, plant_id)
        print(f"Found {len(reports)} reports for plant {plant_id}.")
        assert len(reports) == 2
        
        # Verify first report in list (latest first)
        latest_report = reports[0]
        assert latest_report["plant_id"] == plant_id
        assert isinstance(latest_report["tips"], list)
        
        report_id = latest_report["id"]
        print(f"\nRetrieving details for Report ID: {report_id}...")
        report_detail = get_report_detail(token, report_id)
        assert report_detail["id"] == report_id
        assert isinstance(report_detail["tips"], list)
        print(f"Report detail retrieved: {report_detail['disease']}, Tips: {report_detail['tips']}")
        
        print(f"\nRetrieving recovery history and trends for Plant: {plant_id}...")
        recovery = get_plant_recovery(token, plant_id)
        print(f"Recovery Response: {recovery}")
        assert recovery["plant_id"] == plant_id
        assert len(recovery["history"]) == 2
        assert "overall_trend" in recovery
        
        # Check details of history list item
        h_item = recovery["history"][0]
        assert "date" in h_item
        assert "severity" in h_item
        assert "score" in h_item
        assert isinstance(h_item["score"], int)
        
        print("\nAll Phase 4 Reports & Recovery History tests passed successfully!")
    except Exception as ex:
        print("\nTests failed:", ex)
        exit(1)
