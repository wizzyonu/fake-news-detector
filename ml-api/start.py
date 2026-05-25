#!/usr/bin/env python
import sys
import os

# Patch numpy BEFORE any other imports
print("Patching numpy for compatibility...")
try:
    import numpy as np
    if not hasattr(np, '_core'):
        np._core = np.core
        print("✅ Added np._core = np.core")
except Exception as e:
    print(f"⚠️ Could not patch numpy: {e}")

# Now import and run the main app
print("Starting ML API...")
from ml_api import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)