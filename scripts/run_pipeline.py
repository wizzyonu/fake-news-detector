# scripts/run_pipeline.py
"""
One-command pipeline: Scrape → Train → Convert → Deploy
"""
import subprocess
import sys
import os

def run_command(command, description):
    print(f"\n{'='*70}")
    print(f"📌 {description}")
    print(f"{'='*70}")
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"❌ Failed: {description}")
        return False
    print(f"✅ Completed: {description}")
    return True

def main():
    print("=" * 70)
    print("🚀 FULL PIPELINE: Scrape → Train → Convert")
    print("=" * 70)
    
    steps = [
        ("python scripts/scrape_nigerian_news.py", "Scraping Nigerian News (2020-2026)"),
        ("python scripts/retrain_pipeline.py", "Retraining Model with All Data"),
        ("python scripts/convert_models.py", "Converting to ONNX"),
    ]
    
    for command, description in steps:
        if not run_command(command, description):
            print("\n❌ Pipeline stopped at:", description)
            sys.exit(1)
    
    print("\n" + "=" * 70)
    print("🎉 PIPELINE COMPLETE!")
    print("=" * 70)
    print("\n✅ New model is ready!")
    print("📝 Restart your Next.js app: npm run dev")

if __name__ == "__main__":
    main()