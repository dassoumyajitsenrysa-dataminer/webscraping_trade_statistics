from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
wait = WebDriverWait(driver, 40)

driver.get("https://www.trademap.org/Index.aspx")


# ================= ENSURE LOGIN MANUALLY OR AUTO =================
def ensure_logged_in():
    try:
        login_label = driver.find_element(By.ID, "ctl00_MenuControl_Label_Login")
        if login_label.text.strip().lower() == "login":
            raise Exception("Login required")
    except:
        print("⚠️ Please login manually once, then press ENTER here")
        input()
        wait.until(EC.presence_of_element_located(
            (By.ID, "ctl00_PageContent_RadComboBox_Product_Input")
        ))

ensure_logged_in()


# ================= ENTER HS6 *CORRECTLY* =================
product_input = wait.until(EC.element_to_be_clickable(
    (By.ID, "ctl00_PageContent_RadComboBox_Product_Input")
))

product_input.clear()
product_input.send_keys("090111")

# 🔑 wait for dropdown to load
time.sleep(2)

# 🔑 select from dropdown (THIS IS THE FIX)
product_option = wait.until(EC.element_to_be_clickable(
    (By.XPATH, "//div[contains(@id,'RadComboBox_Product_DropDown')]//li[contains(text(),'090111')]")
))
product_option.click()

print("✅ HS6 code 090111 selected correctly")


# ================= SELECT INDIA =================
country_input = wait.until(EC.element_to_be_clickable(
    (By.ID, "ctl00_PageContent_RadComboBox_Country_Input")
))

country_input.clear()
country_input.send_keys("India")
time.sleep(2)

country_option = wait.until(EC.element_to_be_clickable(
    (By.XPATH, "//div[contains(@id,'RadComboBox_Country_DropDown')]//li[contains(text(),'India')]")
))
country_option.click()

print("✅ Country selected: India")


# ================= CLICK TRADE INDICATORS =================
trade_btn = wait.until(EC.element_to_be_clickable(
    (By.ID, "ctl00_PageContent_Button_TradeIndicators")
))
trade_btn.click()

wait.until(EC.presence_of_element_located(
    (By.ID, "ctl00_PageContent_MyGridView1")
))

print("📊 Trade Indicators loaded correctly")
