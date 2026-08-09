import urllib.request
import json
import time
import io
import uuid
import mimetypes
from PIL import Image

base_url = "http://127.0.0.1:8000"

def encode_multipart_formdata(fields, files):
    """Encodes form fields and file data into multipart/form-data format."""
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
    """Generates a simple 200x200 red JPEG in memory and returns raw bytes."""
    img = Image.new("RGB", (200, 200), color="red")
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

if __name__ == "__main__":
    time.sleep(1)
    try:
        print("Authenticating...")
        token = get_auth_token()
        print("Authenticated successfully.")
        
        print("\nCreating a test plant for scanning...")
        plant_id = create_plant(token, "Tomato", "Scan Test Tomato")
        print(f"Test Plant ID: {plant_id}")
        
        print("\nGenerating dummy leaf image...")
        img_bytes = create_dummy_image()
        
        # We will keep track of previous results to verify trend logic rules
        history = []
        severity_map = {"MILD": 1, "MODERATE": 2, "SEVERE": 3}
        
        for i in range(1, 4):
            print(f"\n--- Running Scan #{i} ---")
            result = upload_scan(token, plant_id, img_bytes)
            print(f"Scan #{i} Result: {result}")
            
            disease = result["disease"]
            severity = result["severity"]
            trend = result["trend"]
            
            if i == 1:
                # First scan must always be Baseline
                assert trend == "Baseline", f"First scan trend should be Baseline, got {trend}"
                print("Rule Checked: First scan is Baseline.")
            else:
                prev = history[-1]
                prev_disease = prev["disease"]
                prev_severity = prev["severity"]
                
                if prev_disease != disease:
                    assert trend == "Baseline", f"Disease changed ({prev_disease} -> {disease}) but trend is {trend} instead of Baseline"
                    print(f"Rule Checked: Disease changed from {prev_disease} to {disease}, trend correctly reset to Baseline.")
                else:
                    prev_score = severity_map[prev_severity.upper()]
                    curr_score = severity_map[severity.upper()]
                    
                    if curr_score < prev_score:
                        assert trend == "Improving", f"Expected Improving, got {trend}"
                    elif curr_score > prev_score:
                        assert trend == "Worsening", f"Expected Worsening, got {trend}"
                    else:
                        assert trend == "Stable", f"Expected Stable, got {trend}"
                    print(f"Rule Checked: Disease match ({disease}), severity changed from {prev_severity} ({prev_score}) to {severity} ({curr_score}), trend correctly evaluated as {trend}.")
            
            history.append(result)
            
        print("\nAll Phase 3 ML Mock + Preprocessing + Recovery Trend tests passed successfully!")
    except Exception as ex:
        print("\nTests failed:", ex)
        exit(1)
