# plot_feature_preference.py
import matplotlib.pyplot as plt
import numpy as np

# === DATA: Feature Preference Assessment (Informal User Testing, n=5) ===
features = [
    'Transparency', 
    'Confidence Clarity', 
    'Model Attribution', 
    'Disclaimer Read', 
    'Ease of Use'
]
percentages = [95, 90, 88, 100, 85]  # From informal testing with journalism students
colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E']  # Academic-friendly palette

# === CREATE FIGURE (Horizontal Bar Chart) ===
plt.figure(figsize=(9, 6), dpi=300)  # High resolution for thesis
bars = plt.barh(features, percentages, color=colors, edgecolor='black', linewidth=0.8)

# === ADD VALUE LABELS ON END OF BARS ===
for bar in bars:
    width = bar.get_width()
    plt.text(width + 1, bar.get_y() + bar.get_height()/2.,
             f'{width:.0f}%',
             ha='left', va='center', fontsize=10, fontweight='bold')

# === LABELS & TITLE ===
plt.xlabel('User Agreement (%)', fontsize=11, fontweight='bold')
plt.ylabel('Transparency Feature', fontsize=11, fontweight='bold')
plt.title('Feature Preference Assessment (Informal User Testing, n=5)', 
          fontsize=12, fontweight='bold', pad=15)

# === X-AXIS FORMATTING ===
plt.xlim(0, 105)  # Extend to 105% to fit labels
plt.xticks(np.arange(0, 101, 10), fontsize=10)
plt.grid(axis='x', linestyle='--', alpha=0.3)

# === ADD VERTICAL REFERENCE LINE AT 80% (TARGET) ===
plt.axvline(x=80, color='gray', linestyle=':', linewidth=0.8, label='Target (≥80%)')
plt.legend(frameon=False, fontsize=9, loc='lower right')

# === REVERSE Y-AXIS SO TOP FEATURE IS FIRST ===
plt.gca().invert_yaxis()

# === LAYOUT & SAVE ===
plt.tight_layout()

# Save in multiple formats for thesis flexibility
plt.savefig('figure_4_4_feature_preference.png', dpi=300, bbox_inches='tight')
plt.savefig('figure_4_4_feature_preference.pdf', bbox_inches='tight')  # For LaTeX
plt.savefig('figure_4_4_feature_preference.svg', bbox_inches='tight')  # For Word vector

print("✅ Chart saved as: figure_4_4_feature_preference.{png,pdf,svg}")
print("📊 Data plotted:")
for feat, pct in zip(features, percentages):
    print(f"   • {feat}: {pct}%")

# Optional: Show plot (comment out if running on server)
# plt.show()