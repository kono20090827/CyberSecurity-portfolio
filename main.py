password = input("請輸入密碼：")

score = 0

if len(password) >= 8:
    score += 1

if any(c.isupper() for c in password):
    score += 1

if any(c.islower() for c in password):
    score += 1

if any(c.isdigit() for c in password):
    score += 1

if any(c in "!@#$%^&*" for c in password):
    score += 1


print("安全分數：", score, "/5")

if score <= 2:
    print("安全程度：弱")
elif score <= 4:
    print("安全程度：中")
else:
    print("安全程度：強")
