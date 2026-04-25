# plot_accuracy_by_content.py
import matplotlib.pyplot as plt
import numpy as np

# === DATA: Accuracy by Content Type (Nigerian Dataset) ===
content_types = ['Political', 'Security', 'Health', 'Economic', 'Celebrity']
accuracies = [86.7, 90.0, 73.3, 80.0, 88.0]  # From your empirical test results
colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E']  # Academic-friendly palette

# === CREATE FIGURE ===
plt.figure(figsize=(8, 5), dpi=300)  # High resolution for thesis
bars = plt.bar(content_types, accuracies, color=colors, edgecolor='black', linewidth=0.8)

# === ADD VALUE LABELS ON TOP OF BARS ===
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height + 0.8,
             f'{height:.1f}%',
             ha='center', va='bottom', fontsize=10, fontweight='bold')

# === LABELS & TITLE ===
plt.xlabel('Content Type', fontsize=11, fontweight='bold')
plt.ylabel('Accuracy (%)', fontsize=11, fontweight='bold')
plt.title('Model Accuracy by Content Category (Nigerian Dataset n=60)', fontsize=12, fontweight='bold', pad=15)

# === Y-AXIS FORMATTING ===
plt.ylim(0, 100)
plt.yticks(np.arange(0, 101, 10), fontsize=10)
plt.grid(axis='y', linestyle='--', alpha=0.3)

# === ADD HORIZONTAL REFERENCE LINE AT 80% (TARGET) ===
plt.axhline(y=80, color='gray', linestyle=':', linewidth=0.8, label='Target (80%)')
plt.legend(frameon=False, fontsize=9, loc='lower right')

# === LAYOUT & SAVE ===
plt.tight_layout()

# Save in multiple formats for thesis flexibility
plt.savefig('figure_4_3_accuracy_by_content.png', dpi=300, bbox_inches='tight')
plt.savefig('figure_4_3_accuracy_by_content.pdf', bbox_inches='tight')  # For LaTeX
plt.savefig('figure_4_3_accuracy_by_content.svg', bbox_inches='tight')  # For Word vector

print("✅ Chart saved as: figure_4_3_accuracy_by_content.{png,pdf,svg}")
print("📊 Data plotted:")
for ct, acc in zip(content_types, accuracies):
    print(f"   • {ct}: {acc}%")

# Optional: Show plot (comment out if running on server)
# plt.show()