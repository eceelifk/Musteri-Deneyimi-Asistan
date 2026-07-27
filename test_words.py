import sys
sys.path.append(".")
from app.translate import translate_en_to_tr
print("Testing words...")
out1 = translate_en_to_tr("I do not have any information regarding this product in my database.")
print("1:", out1)
