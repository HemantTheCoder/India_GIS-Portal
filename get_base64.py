import base64

image_path = r"C:/Users/heman/.gemini/antigravity/brain/f2c40cfd-37ad-4202-b570-db19019b8498/india_map_premium_1765549563752.png"

with open(image_path, "rb") as image_file:
    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    with open("base64.txt", "w") as f:
        f.write(encoded_string)
    print("Done writing to base64.txt")
