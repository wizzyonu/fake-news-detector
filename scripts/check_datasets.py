# scripts/check_datasets.py
import pandas as pd
import os
import glob

print("=" * 60)
print("📊 DATASET INVENTORY")
print("=" * 60)

# Find all CSV files
csv_files = glob.glob('*.csv')
csv_files.extend(glob.glob('data/*.csv'))
csv_files = [f for f in csv_files if 'node_modules' not in f]

total_samples = 0
dataset_summary = []

for file in csv_files:
    try:
        df = pd.read_csv(file)
        samples = len(df)
        total_samples += samples
        
        # Check if 'label' column exists
        has_label = 'label' in df.columns
        if has_label:
            fake_count = len(df[df['label']==1]) if 1 in df['label'].values else 0
            real_count = len(df[df['label']==0]) if 0 in df['label'].values else 0
        else:
            fake_count = 'N/A'
            real_count = 'N/A'
        
        dataset_summary.append({
            'File': file,
            'Samples': samples,
            'Has Label': has_label,
            'FAKE (1)': fake_count,
            'REAL (0)': real_count
        })
        print(f"✅ {file}: {samples} samples")
    except Exception as e:
        print(f"❌ Could not read {file}: {e}")

print("\n" + "=" * 60)
print("📈 SUMMARY")
print("=" * 60)
print(f"Total CSV files: {len(csv_files)}")
print(f"Total samples across all files: {total_samples}")

# Create summary DataFrame
summary_df = pd.DataFrame(dataset_summary)
print("\n" + summary_df.to_string())

# Also check your trained datasets you mentioned earlier
print("\n" + "=" * 60)
print("🤖 TRAINED MODEL DATASETS")
print("=" * 60)
trained_datasets = [
    'balanced_nigerian_dataset_final.csv',
    'balanced_nigerian_news_2k.csv',
    'multi_source_nigerian_news_1k.csv',
    'nigerian_news_2k_labeled.csv'
]

for ds in trained_datasets:
    if os.path.exists(ds):
        df = pd.read_csv(ds)
        print(f"✅ {ds}: {len(df)} samples")
        if 'label' in df.columns:
            print(f"   - FAKE: {len(df[df['label']==1])}")
            print(f"   - REAL: {len(df[df['label']==0])}")