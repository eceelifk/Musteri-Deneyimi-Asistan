import sys
sys.path.append(".")
from app.translate import translate_en_to_tr
print("Testing words...")
out1 = translate_en_to_tr("To return the product, please log in.")
out2 = translate_en_to_tr("To get a refund for your item, please sign in.")
out3 = translate_en_to_tr("If you want to send the item back and get your money, follow these steps.")
out4 = translate_en_to_tr("Product return process:")
print("1:", out1)
print("2:", out2)
print("3:", out3)
print("4:", out4)
