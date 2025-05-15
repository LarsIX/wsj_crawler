from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.debugger_address = "127.0.0.1:9222"

driver = webdriver.Chrome(service=Service(), options=chrome_options)
print("🚀 Current URL:", driver.current_url)
driver.get("https://www.wsj.com/")
print("🌍 New URL:", driver.current_url)