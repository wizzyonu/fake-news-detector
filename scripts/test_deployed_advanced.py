# scripts/test_deployed_advanced.py
import requests
import time

# YOUR VERCEL APP URL
YOUR_APP_URL = "https://fake-news-detector-tan.vercel.app"
API_URL = f"https://fake-news-detector-tan.vercel.app/api/analyze"

# Test cases with difficulty ratings
test_cases = [
    # REAL NEWS (10 cases)
    ("REAL", "Official Economic Policy", "The Federal Government has approved a new minimum wage of ₦70,000 for civil servants. Minister of Labour and Employment Simon Lalong announced this after the tripartite committee meeting in Abuja."),
    ("REAL", "Legitimate Infrastructure Project", "The Lagos State Government has announced the completion of the Blue Line rail project from Marina to Mile 2. Governor Babajide Sanwo-Olu will commission the project on June 15."),
    ("REAL", "Official Police Statement", "The Nigeria Police Force has arrested three suspects in connection with the kidnapping of 15 passengers along the Kaduna-Abuja highway. Police spokesperson Muyiwa Adejobi confirmed the arrests."),
    ("REAL", "Legitimate Health Campaign", "The National Primary Health Care Development Agency has commenced a nationwide polio vaccination campaign targeting 40 million children. Executive Director Dr. Faisal Shuaib urged parents to cooperate."),
    ("REAL", "Official Election Update", "INEC has announced that the off-cycle governorship election in Edo State will hold on September 21, 2025. INEC Chairman Prof. Mahmood Yakubu stated that 2.5 million PVCs have been collected."),
    ("REAL", "Legitimate Business News", "Dangote Refinery has begun production of diesel and aviation fuel, according to a company statement. The $20 billion facility in Lagos is expected to meet Nigeria's domestic fuel needs by Q3 2025."),
    ("REAL", "Official Education Policy", "The Federal Ministry of Education has announced that WAEC registration fees for 2025 will remain at ₦27,000. Minister of Education Dr. Tunji Alausa confirmed there will be no increase."),
    ("REAL", "Legitimate Environmental Report", "The Lagos State Environmental Protection Agency has shut down 15 factories for violating pollution standards. LASEPA General Manager Dr. Babatunde Ajayi said the closure will remain until compliance is achieved."),
    ("REAL", "Official Agricultural News", "The Federal Government has distributed 100,000 bags of fertilizer to farmers in Kano and Kaduna states. Agriculture Minister Abubakar Kyari said the distribution is part of dry season farming support."),
    ("REAL", "Legitimate International Relations", "Nigeria and the United Kingdom have signed a new trade agreement worth £2.5 billion. President Bola Tinubu witnessed the signing ceremony during his official visit to London."),
    
    # FAKE NEWS (10 cases - subtle to hard)
    ("FAKE", "Subtle Death Hoax", "The presidency has announced that President Bola Tinubu will not attend the upcoming ECOWAS summit due to health concerns. Sources close to the first family confirm the president is receiving medical attention at an undisclosed location."),
    ("FAKE", "WhatsApp Scam (Less obvious)", "The Federal Ministry of Humanitarian Affairs has launched a new conditional cash transfer program. Eligible Nigerians can receive ₦50,000 by completing the registration form at www.fg-palliative.com. The portal closes on May 30."),
    ("FAKE", "Political Misinformation", "The Independent National Electoral Commission has reportedly lost 500,000 PVCs ahead of the Edo election. A confidential memo circulating within INEC indicates the commission may postpone the election."),
    ("FAKE", "Health Hoax (Scientific-sounding)", "A recent study by the Nigerian Institute of Medical Research found that drinking hot water mixed with lemon and ginger can cure Lassa fever. The study, reportedly published in the Nigerian Medical Journal, claims 90% of patients recovered within 48 hours."),
    ("FAKE", "Subtle Security Hoax", "The Nigerian Army has advised residents of Borno State to evacuate immediately following credible intelligence about a planned attack. A military intelligence report obtained by our team indicates the attack may occur before May 15."),
    ("FAKE", "Economic Misinformation", "The Central Bank of Nigeria has directed all commercial banks to convert old naira notes to the new currency by June 1. A circular signed by CBN Director of Currency reportedly warns that non-compliance will attract sanctions."),
    ("FAKE", "Educational Scam", "The Joint Admissions and Matriculation Board has announced a special second chance admission quota for candidates who scored above 250 in UTME. Eligible candidates are directed to pay ₦15,000 through a dedicated portal to secure their slot."),
    ("FAKE", "Sports Hoax", "Super Eagles coach Finidi George has reportedly resigned following disagreements with the Nigeria Football Federation. A resignation letter dated May 15, 2025 is allegedly circulating within the NFF board."),
    ("FAKE", "Political Manipulation", "A confidential investigation report by the Economic and Financial Crimes Commission allegedly names 12 state governors in a ₦500 billion fraud. The report is said to have been submitted to the presidency for action."),
    ("FAKE", "Very Subtle Fake News", "The National Pension Commission has approved a one-off withdrawal of 50% of pension savings for unemployed contributors. The approval follows intense pressure from labor unions and is effective immediately."),
]

print("=" * 80)
print("🧪 ADVANCED FAKE NEWS DETECTION TEST - 20 CASES")
print(f"📍 API URL: {API_URL}")
print("=" * 80)

correct = 0
total = len(test_cases)
results = []

for i, (expected, name, text) in enumerate(test_cases, 1):
    print(f"\n📝 Test {i}: {name}")
    print(f"   Expected: {expected}")
    print(f"   Difficulty: {'Hard' if i >= 16 else 'Medium' if i >= 11 else 'Easy'}")
    print(f"   Text: {text[:100]}...")
    
    try:
        response = requests.post(API_URL, json={"input": text}, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            predicted = result.get('classification', 'UNKNOWN')
            confidence = result.get('confidence', 0)
            
            is_correct = predicted == expected
            if is_correct:
                correct += 1
            
            status = "✅" if is_correct else "❌"
            
            print(f"   {status} Result: {predicted} ({confidence}%)")
            
            if not is_correct:
                print(f"   ⚠️ WRONG! Pattern reasons: {result.get('patternDetails', {}).get('reasons', [])[:2]}")
            
            results.append({
                "test": i,
                "name": name,
                "expected": expected,
                "predicted": predicted,
                "confidence": confidence,
                "correct": is_correct
            })
        else:
            print(f"   ❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    time.sleep(0.3)  # Small delay

# Summary
print("\n" + "=" * 80)
print("📊 TEST SUMMARY")
print("=" * 80)

print(f"\n✅ Correct: {correct}/{total}")
print(f"📈 Accuracy: {(correct/total)*100:.1f}%")

# Breakdown by type
real_correct = sum(1 for r in results if r["expected"] == "REAL" and r["correct"])
fake_correct = sum(1 for r in results if r["expected"] == "FAKE" and r["correct"])
real_total = sum(1 for r in results if r["expected"] == "REAL")
fake_total = sum(1 for r in results if r["expected"] == "FAKE")

print(f"\n📊 REAL News: {real_correct}/{real_total} ({(real_correct/real_total)*100:.1f}%)")
print(f"📊 FAKE News: {fake_correct}/{fake_total} ({(fake_correct/fake_total)*100:.1f}%)")

# Show incorrect predictions
incorrect = [r for r in results if not r["correct"]]
if incorrect:
    print(f"\n❌ INCORRECT PREDICTIONS ({len(incorrect)}):")
    for r in incorrect:
        print(f"   - {r['name']}: Expected {r['expected']}, Got {r['predicted']} ({r['confidence']}%)")
else:
    print("\n🎉 PERFECT SCORE! No incorrect predictions!")

# Confidence analysis
avg_confidence = sum(r["confidence"] for r in results) / total
print(f"\n📈 Average Confidence: {avg_confidence:.1f}%")

print("\n" + "=" * 80)
print("✅ Test complete!")