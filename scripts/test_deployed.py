# scripts/test_deployed.py
import requests

# REPLACE WITH YOUR ACTUAL VERCEL URL
YOUR_APP_URL = "https://fake-news-detector-tan.vercel.app/"  # <-- CHANGE THIS!

API_URL = f"{YOUR_APP_URL}/api/analyze"

test_cases = [
    # REAL NEWS
    ("Official Government Statement", 
     "The Central Bank of Nigeria has announced that the Monetary Policy Committee has raised the interest rate to 26.75% to combat rising inflation. CBN Governor Yemi Cardoso stated this at a press briefing in Abuja.",
     "REAL"),
    
    ("Legitimate Security Report",
     "The Nigerian Army has rescued 45 kidnap victims in a coordinated operation with local vigilantes in Zamfara State. Army spokesperson Major General Onyema Nwachukwu confirmed the rescue operation.",
     "REAL"),
    
    ("Official Health Update",
     "The Nigeria Centre for Disease Control has reported 67 new cases of Lassa fever across 12 states in the past week. NCDC Director General Dr. Jide Idris urged citizens to maintain proper hygiene.",
     "REAL"),
    
    ("Educational News",
     "JAMB has announced that the 2025 Unified Tertiary Matriculation Examination will hold from April 25 to May 5. Registration begins February 10.",
     "REAL"),
    
    ("Sports News",
     "Super Eagles head coach Finidi George has released a 25-man squad for the upcoming AFCON qualifier against Benin Republic. Captain William Troost-Ekong and striker Victor Osimhen make the list.",
     "REAL"),
    
    # FAKE NEWS
    ("Death Hoax",
     "BREAKING!!! PRESIDENT TINUBU CONFIRMED DEAD IN LONDON!!! SHARE TO ALL NIGERIAN GROUPS!!! URGENT!!! The presidency has not yet made an official statement but family sources confirm the worst.",
     "FAKE"),
    
    ("WhatsApp Palliative Scam",
     "URGENT!!! FG APPROVES ₦75,000 PALLIATIVE FOR ALL NIGERIANS!!! SHARE THIS MESSAGE TO 10 WHATSAPP GROUPS WITHIN 5 MINUTES TO CLAIM YOURS!!! FAILURE TO SHARE WILL RESULT IN DISQUALIFICATION!!!",
     "FAKE"),
    
    ("Political Manipulation",
     "EXPOSED!!! INEC OFFICIALS CAUGHT WITH PRE-TICKETED BALLOT PAPERS IN LAGOS!!! YOU WON'T BELIEVE WHAT THEY FOUND!!! 10 MILLION PRE-TICKETED BALLOTS READY FOR RIGGING!!!",
     "FAKE"),
    
    ("Security Hoax",
     "SHOCKING!!! BOKO HARAM HAS INVADED ABUJA!!! THEY ARE ENTERING FROM KEFFI AXIS!!! EVERYONE SHOULD STAY INDOORS!!! SHARE TO SAVE LIVES!!! CONFIRMED!!!",
     "FAKE"),
    
    ("Health Misinformation",
     "DANGER!!! NAFDAC CONFIRMS COCA-COLA KILLS!!! MIXING COCA-COLA WITH VITAMIN C CREATES POISON IN YOUR STOMACH!!! 67 NIGERIANS HAVE ALREADY DIED!!! SHARE TO SAVE YOUR FAMILY!!!",
     "FAKE"),
]

print("=" * 70)
print("🧪 TESTING DEPLOYED FAKE NEWS DETECTOR")
print(f"📍 API URL: {API_URL}")
print("=" * 70)

correct = 0
total = len(test_cases)

for i, (name, text, expected) in enumerate(test_cases, 1):
    print(f"\n📝 Test {i}: {name}")
    print(f"   Expected: {expected}")
    print(f"   Text: {text[:80]}...")
    
    try:
        response = requests.post(API_URL, json={"input": text}, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            predicted = result.get('classification', 'UNKNOWN')
            confidence = result.get('confidence', 0)
            
            status = "✅" if predicted == expected else "❌"
            if predicted == expected:
                correct += 1
            
            print(f"   {status} Result: {predicted} ({confidence}%)")
            
            # Show explanation for wrong predictions
            if predicted != expected:
                print(f"   📝 Explanation: {result.get('explanation', 'N/A')[:150]}")
        else:
            print(f"   ❌ API Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Cannot connect to {API_URL}")
        print(f"   Make sure your app is deployed and the URL is correct!")
        break
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 70)
print("📊 TEST SUMMARY")
print("=" * 70)
print(f"✅ Correct: {correct}/{total}")
print(f"📈 Accuracy: {(correct/total)*100:.1f}%")