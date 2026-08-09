import urllib.request
import json
import time

base_url = "http://127.0.0.1:8000"

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
        print(f"Created Plant response: {res}")
        assert "plant_id" in res
        assert res["crop_name"] == crop_name
        assert res["plant_name"] == plant_name
        return res["plant_id"]

def list_plants(token):
    url = f"{base_url}/plants"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}"
        },
        method="GET"
    )
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode("utf-8"))
        print(f"List Plants response: {res}")
        return res

def get_plant(token, plant_id):
    url = f"{base_url}/{plant_id}" if plant_id.startswith("plants/") else f"{base_url}/plants/{plant_id}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}"
        },
        method="GET"
    )
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode("utf-8"))
        print(f"Get Plant {plant_id} response: {res}")
        return res

def delete_plant(token, plant_id):
    url = f"{base_url}/plants/{plant_id}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}"
        },
        method="DELETE"
    )
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode("utf-8"))
        print(f"Delete Plant {plant_id} response: {res}")
        return res

if __name__ == "__main__":
    time.sleep(1)
    try:
        print("Authenticating...")
        token = get_auth_token()
        print("Authenticated successfully.")

        print("\nCreating Plant 1...")
        p1_id = create_plant(token, "Tomato", "Tomato Plant 1")
        print(f"Plant 1 ID: {p1_id}")

        print("\nCreating Plant 2...")
        p2_id = create_plant(token, "Potato", "Potato Plant 1")
        print(f"Plant 2 ID: {p2_id}")

        print("\nListing plants...")
        plants = list_plants(token)
        # We might have plants from previous tests, so we assert >= 2
        assert len(plants) >= 2

        print(f"\nRetrieving Plant {p1_id}...")
        plant_details = get_plant(token, p1_id)
        assert plant_details["plant_id"] == p1_id
        assert plant_details["crop_name"] == "Tomato"

        print(f"\nSoft deleting Plant {p1_id}...")
        del_response = delete_plant(token, p1_id)
        assert "soft-deleted" in del_response["message"]

        print("\nListing plants after delete...")
        plants_after = list_plants(token)
        # Verify plant 1 is no longer in the active list
        plant_ids_after = [p["plant_id"] for p in plants_after]
        assert p1_id not in plant_ids_after
        print(f"Plant {p1_id} is successfully omitted from list!")

        print(f"\nVerifying GET on soft-deleted plant {p1_id} returns 404...")
        try:
            get_plant(token, p1_id)
            print("ERROR: Should have raised 404 for deleted plant!")
            exit(1)
        except urllib.error.HTTPError as he:
            assert he.code == 404
            print(f"Confirmed: GET {p1_id} returned expected 404.")

        print("\nAll Phase 2 Plant CRUD tests passed successfully!")
    except Exception as ex:
        print("\nTests failed:", ex)
        exit(1)
