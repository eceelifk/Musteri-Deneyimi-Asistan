import sys
sys.path.append(".")
from app.translate import translate_en_to_tr
print("Testing words...")
out1 = translate_en_to_tr("First, log into your account and go to the My Orders page. Next, find the item you want to track. Finally, click the Track Package button to see where your cargo is.")
print("1:", out1)
