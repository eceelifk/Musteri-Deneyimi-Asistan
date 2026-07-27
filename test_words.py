import sys
sys.path.append(".")
from app.translate import translate_en_to_tr
print("Testing words...")
text = """Here is a detailed guide on how to track your order:
1. **Log in**: First, go to our website and log into your account.
2. **My Orders**: Navigate to the "My Orders" section from the dashboard.
3. **Track**: Click on the "Track Package" button next to your specific item.

If you have any further questions, please feel free to reach out to our support team!"""
out1 = translate_en_to_tr(text)
print("1:\n", out1)
