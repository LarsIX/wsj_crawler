import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time

# Dein Chrome-Profil
user_data_dir = "C:/Users/PC/AppData/Local/Google/Chrome/User Data"
profile_dir = "Profile 1"  # oder "Default" oder dein NYT-Testprofil

options = uc.ChromeOptions()
options.add_argument(f"--user-data-dir={user_data_dir}")
options.add_argument(f"--profile-directory={profile_dir}")
options.add_argument("--window-size=1280,800")
options.add_argument("--start-maximized")

driver = uc.Chrome(options=options)

# Test: NYT öffnen und aktiv bleiben
driver.get("https://www.nytimes.com")
print("✅ NYT geöffnet – Browser bleibt 30 Sekunden offen...")
time.sleep(30)

driver.quit()
