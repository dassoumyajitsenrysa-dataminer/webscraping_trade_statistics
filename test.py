from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

URL = (
    "https://www.trademap.org/"
    "Country_SelProductCountry.aspx?"
    "nvpm=1|699||||090111|||6|1|1|1|1||2|1||1"
)

options = Options()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

wait = WebDriverWait(driver, 40)
driver.get(URL)

# wait for data rows
wait.until(EC.presence_of_element_located((By.CLASS_NAME, "partner_label")))

html = driver.page_source
soup = BeautifulSoup(html, "lxml")

table = soup.find("table", id="ctl00_PageContent_MyGridView1")
print("TABLE FOUND:", table is not None)

rows = table.find_all("tr")
print("TOTAL <tr>:", len(rows))

data_rows = []
td_lengths = set()

for tr in rows:
    if tr.find("a", class_="partner_label"):
        tds = tr.find_all("td")
        td_lengths.add(len(tds))
        data_rows.append(tds)

print("DATA ROW COUNT:", len(data_rows))
print("TD COUNTS SEEN:", td_lengths)

# inspect first data row
if data_rows:
    print("\nFIRST DATA ROW TD COUNT:", len(data_rows[0]))
    for i, td in enumerate(data_rows[0]):
        print(f"TD[{i}] =", td.get_text(strip=True))

driver.quit()
