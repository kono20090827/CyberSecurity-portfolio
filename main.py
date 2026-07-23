password = input("請輸入密碼：")

weak_passwords = [
    "123456",
    "password",
    "qwerty",
    "admin"
]

score = 0
suggestions = []


if len(password) >= 8:
    score += 1
else:
    suggestions.append("密碼長度不足，建議至少8碼")
    

if any(c.isupper() for c in password):
    score += 1
else:
    suggestions.append("加入大寫字母")

    

if any(c.islower() for c in password):
    score += 1

if any(c.isdigit() for c in password):
    score += 1

if any(c in "!@#$%^&*" for c in password):
    score += 1
else:
    suggestions.append("加入特殊符號")


print("安全分數：", score, "/5")

if score <= 2:
    print("安全程度：弱")
elif score <= 4:
    print("安全程度：中")
else:
    print("安全程度：強")

if password in weak_passwords:
    print("⚠ 警告：這是常見弱密碼！")

if suggestions:
    print("\n改善建議：")
    for suggestion in suggestions:
        print("-", suggestion)
else:
    print("\n✅ 密碼安全性良好，沒有改善建議！")
