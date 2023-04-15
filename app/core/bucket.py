import json

def load_bucket_credentials():
    with open("keyfiles/bucket.json", "r") as file:
        credentials = json.load(file)
    return credentials
