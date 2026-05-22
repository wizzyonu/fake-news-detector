# scripts/test_nigerian_news.py
"""
Test your fake news detector with Nigerian context examples
"""
import requests
import json
import time

# Your API endpoint (adjust if different)
API_URL = "http://localhost:3000/api/analyze"

# Test cases
test_cases = [
    {
        "text": "The Central Bank of Nigeria has announced a new interest rate of 22.75% as part of efforts to combat rising inflation. CBN Governor Olayemi Cardoso stated this at the Monetary Policy Committee meeting in Abuja.",
        "expected": "REAL",
        "category": "Economic News"
    },
    {
        "text": "BREAKING!!! PRESIDENT TINUBU CONFIRMED DEAD IN LONDON!!! SHARE TO ALL NIGERIAN GROUPS!!! URGENT!!! The presidency has not yet made an official statement but family sources confirm the worst.",
        "expected": "FAKE",
        "category": "Death Hoax"
    },
    {
        "text": "The Nigerian Army has rescued 23 kidnap victims in a joint operation with local vigilantes in Zamfara State. Army spokesperson Major General Onyema Nwachukwu confirmed the rescue operation.",
        "expected": "REAL",
        "category": "Security News"
    },
    {
        "text": "URGENT!!! FG APPROVES ₦50,000 PALLIATIVE FOR ALL NIGERIANS!!! SHARE THIS MESSAGE TO 10 WHATSAPP GROUPS WITHIN 5 MINUTES TO CLAIM YOURS!!! FAILURE TO SHARE WILL RESULT IN DISQUALIFICATION!!!",
        "expected": "FAKE",
        "category": "WhatsApp Scam"
    },
    {
        "text": "JAMB has announced that the 2025 Unified Tertiary Matriculation Examination will hold from April 25 to May 5. Registration begins February 10. Candidates are advised to visit the official JAMB portal.",
        "expected": "REAL",
        "category": "Educational News"
    },
    {
        "text": "SHOCKING!!! BOKO HARAM HAS INVADED ABUJA!!! THEY ARE ENTERING FROM KEFFI AXIS!!! EVERYONE SHOULD STAY INDOORS!!! SHARE TO SAVE LIVES!!! CONFIRMED!!!",
        "expected": "FAKE",
        "category": "Security Hoax"
    },
    {
        "text": "The Nigeria Centre for Disease Control has reported 45 new cases of Lassa fever across 6 states this week. NCDC urges citizens to maintain proper hygiene and avoid contact with rats.",
        "expected": "REAL",
        "category": "Health News"
    },
    {
        "text": "EXPOSED!!! INEC OFFICIALS CAUGHT WITH PRE-TICKETED BALLOT PAPERS IN LAGOS!!! YOU WON'T BELIEVE WHAT THEY FOUND!!! 5 MILLION PRE-TICKETED BALLOTS READY FOR RIGGING!!!",
        "expected": "FAKE",
        "category": "Political Manipulation"
    },
    {
        "text": "Super Eagles head coach Jose Peseiro has released a 23-man squad for the upcoming AFCON qualifier against Rwanda. Captain Ahmed Musa and striker Victor Osimhen make the list.",
        "expected": "REAL",
        "category": "Sports News"
    },
    {
        "text": "DANGER!!! NAFDAC CONFIRMS COCA-COLA KILLS!!! MIXING COCA-COLA WITH VITAMIN C CREATES POISON IN YOUR STOMACH!!! 47 NIGERIANS HAVE ALREADY DIED!!! SHARE TO SAVE YOUR FAMILY!!!",
        "expected": "FAKE",
        "category": "Health Misinformation"
    }
]

def test_system():
    print("=" * 80)
    print("🧪 NIGERIAN FAKE NEWS DETECTOR - SYSTEM TEST")
    print("=" * 80)
    
    results = {
        "correct": 0,
        "incorrect": 0,
        "details": []
    }
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test['category']}")
        print(f"   Expected: {test['expected']}")
        print(f"   Text: {test['text'][:80]}...")
        
        try:
            # Call your API
            response = requests.post(API_URL, json={"input": test['text']}, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                predicted = result.get('classification', 'UNKNOWN')
                confidence = result.get('confidence', 0)
                
                is_correct = predicted == test['expected']
                
                if is_correct:
                    results["correct"] += 1
                    status = "✅ CORRECT"
                else:
                    results["incorrect"] += 1
                    status = "❌ WRONG"
                
                print(f"   Prediction: {predicted} ({confidence}% confidence)")
                print(f"   Status: {status}")
                
                # Show explanation if available
                if 'explanation' in result:
                    print(f"   Explanation: {result['explanation'][:100]}...")
                
                results["details"].append({
                    "test": i,
                    "category": test['category'],
                    "expected": test['expected'],
                    "predicted": predicted,
                    "confidence": confidence,
                    "correct": is_correct
                })
            else:
                print(f"   ❌ API Error: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("   ❌ Cannot connect to API. Make sure your app is running!")
            print("   Run: npm run dev")
            return
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        time.sleep(0.5)  # Small delay between tests
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    total = len(test_cases)
    accuracy = (results["correct"] / total) * 100
    print(f"✅ Correct: {results['correct']}/{total}")
    print(f"❌ Incorrect: {results['incorrect']}/{total}")
    print(f"📈 Accuracy: {accuracy:.1f}%")
    
    # Category breakdown
    print("\n📋 BREAKDOWN BY CATEGORY:")
    print("-" * 50)
    for detail in results["details"]:
        status = "✅" if detail["correct"] else "❌"
        print(f"  {status} {detail['category']}: Expected {detail['expected']}, Got {detail['predicted']} ({detail['confidence']}%)")
    
    return results

if __name__ == "__main__":
    print("\n🚀 Starting Nigerian News Detection Test")
    print("Make sure your Next.js app is running on http://localhost:3000")
    print("\nIf not running, open a new terminal and run: npm run dev\n")
    
    input("Press Enter to start testing...")
    test_system()