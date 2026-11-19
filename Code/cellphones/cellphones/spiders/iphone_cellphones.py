import time
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By

# 1. Khởi tạo Selenium Browser
options = webdriver.ChromeOptions()
options.add_experimental_option("detach", True)
#options.add_argument("--headless")  # open browser in headless mode (no GUI)

driver = webdriver.Chrome(options=options)

driver.get("https://cellphones.com.vn/mobile/apple.html")
driver.maximize_window()
time.sleep(3)

# 2. Vòng lặp tự động bấm nút "Xem thêm" cho đến khi hết
while True:
    try:
        btn_more = driver.find_element(By.CSS_SELECTOR, ".btn-show-more, .btn-more")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_more)
        time.sleep(1)
        btn_more.click()
        print("Đã bấm 'Xem thêm'...")
        time.sleep(2.5)
    except Exception:
        print("Đã tải xong toàn bộ trang.")
        break

# 3. Phân tích HTML bằng BeautifulSoup
soup = BeautifulSoup(driver.page_source, 'html.parser')
driver.quit()

product_items = soup.select('.product-item, .product-info-container')
data_list = []

for p in product_items:
    name_el = p.select_one('.product__name h3, .product__name')
    price_show_el = p.select_one('.product__price--show')
    price_through_el = p.select_one('.product__price--through')
    rating_el = p.select_one('.product__promotions p')
    link_el = p.select_one('a[href]')

    if name_el:
        product_data = {
            "name": name_el.get_text(strip=True),
            "price_sale": price_show_el.get_text(strip=True) if price_show_el else None,
            "price_original": price_through_el.get_text(strip=True) if price_through_el else None,
            "rating": rating_el.get_text(strip=True) if rating_el else None,
            "url": link_el['href'] if link_el else None
        }
        data_list.append(product_data)

# 4. Xuất dữ liệu ra file JSON
with open('data_29_10_2026.json', 'w', encoding='utf-8') as f:
    json.dump(data_list, f, ensure_ascii=False, indent=4)

print(f"Đã lưu thành công {len(data_list)} sản phẩm vào file iphone_cellphones.json")