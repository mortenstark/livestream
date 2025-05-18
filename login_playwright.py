from playwright.sync_api import sync_playwright
import os

# CHROME_PROFILE = r"A:\Docker\livestream\notebook-bot\playwright-user-data"
CHROME_PROFILE = r"C:\Users\morte\AppData\Local\Google\Chrome\User Data\Default"
STORAGE_OUT = "auth.json"

os.makedirs(CHROME_PROFILE, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir=CHROME_PROFILE,
        headless=False,
        channel="chrome"
    )
    page = browser.new_page()
    page.goto("https://notebooklm.google.com")

    print("🛠 Log ind manuelt i browseren, og åbn NotebookML")
    input("✅ Tryk Enter for at gemme auth.json...")

    browser.storage_state(path=STORAGE_OUT)
    print(f"✅ auth.json gemt!")
    browser.close()