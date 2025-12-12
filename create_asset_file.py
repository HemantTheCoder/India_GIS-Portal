import os

# Read the base64 string
with open("base64.txt", "r") as f:
    b64_content = f.read().strip()

# Create the python file content
py_content = f'INDIA_MAP_BASE64 = "{b64_content}"\n'

# Ensure directory exists (it should, but good practice)
os.makedirs("components", exist_ok=True)

# Write to components/map_asset.py
with open("components/map_asset.py", "w") as f:
    f.write(py_content)

print("Successfully created components/map_asset.py")
