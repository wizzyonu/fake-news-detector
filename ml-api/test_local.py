import requests
import json

# Test your Flask API locally
API_URL = "http://localhost:5000"

def test_health():
    response = requests.get(f"{API_URL}/health")
    print(f"Health: {response.json()}")

def test_predict():
    test_texts = [
        "URGENT!!! SHARE THIS TO 10 WHATSAPP GROUPS WITHIN 5 MINUTES OR BAD LUCK WILL FOLLOW YOU!",
        "President Tinubu is dead. This is breaking news, share everywhere!",
        "According to Premium Times, the Nigerian government has announced new economic policies.",
        "The CBN governor announced new interest rates at a press conference today."
    ]
    
    for text in test_texts:
        response = requests.post(f"{API_URL}/predict", json={'text': text})
        result = response.json()
        print(f"\nText: {text[:80]}...")
        print(f"Result: {result}")

if __name__ == "__main__":
    test_health()
    test_predict()