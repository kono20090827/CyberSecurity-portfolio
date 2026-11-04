import hashlib

print("===== SHA-256 Hash Generator =====")

text = input("請輸入文字：")

data = text.encode("utf-8")

hash_result = hashlib.sha256(data)

print("\n原始文字：", text)
print("SHA-256：", hash_result.hexdigest())
