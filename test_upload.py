import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

url = os.getenv('WC_URL')
key = os.getenv('WC_KEY')
secret = os.getenv('WC_SECRET')

# Ensure URL ends with slash
if not url.endswith('/'):
    url += '/'

# Construct Media Endpoint
media_url = f"{url}wp-json/wp/v2/media"

print(f"Testing upload to: {media_url}")

# Create a tiny 1x1 black pixel JPEG
# Base64 for 1x1 pixel black jpeg
pixel_b64 = "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/2wBDAQMEBAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBT/wAARCAABAAEDAREAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD9Sq//2Q=="
img_data = base64.b64decode(pixel_b64)

headers = {
    'Content-Type': 'image/jpeg',
    'Content-Disposition': 'attachment; filename="test_pixel.jpg"'
}

# Try Basic Auth with WC Keys
try:
    print("Attempting upload with Basic Auth (WC Keys)...")
    response = requests.post(
        media_url,
        data=img_data,
        headers=headers,
        auth=(key, secret),
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    
    if response.status_code == 201:
        print("✅ SUCCESS! We can upload to wp/v2/media using WC keys.")
    else:
        print("❌ FAILED to upload.")

except Exception as e:
    print(f"Error: {e}")
