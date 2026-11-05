print("===== Caesar Cipher Tool =====")

text = input("請輸入英文文字：")
shift = int(input("請輸入位移格數："))
mode = input("加密請輸入 E，解密請輸入 D：").upper()

result = ""

for letter in text:
    if "A" <= letter <= "Z":
        start = ord("A")
    elif "a" <= letter <= "z":
        start = ord("a")
    else:
        result += letter
        continue

    number = ord(letter) - start

    if mode == "D":
        new_number = (number - shift) % 26
    else:
        new_number = (number + shift) % 26

    result += chr(start + new_number)

print("處理結果：", result)
