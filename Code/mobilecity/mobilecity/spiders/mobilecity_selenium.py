import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


def crawl_mobilecity():
    chrome_options = Options()
    # Bỏ comment dòng dưới nếu muốn ẩn cửa sổ trình duyệt:
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

    print("==> Khởi tạo trình duyệt Chrome...")
    driver = webdriver.Chrome(
        options=chrome_options,
    )

    url = "https://mobilecity.vn/dien-thoai-iphone-chinh-hang-vna"
    print(f"==> Đang truy cập URL: {url}")
    driver.get(url)
    time.sleep(3)

    click_count = 0
    while True:
        try:
            # Tìm nút "Xem thêm điện thoại" theo ID #product_view_more
            btn = driver.find_element(By.ID, "product_view_more")

            if btn.is_displayed():
                # Cuộn màn hình tới nút bấm
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(1)

                # Click bằng JavaScript để tránh bị các phần tử khác đè lên
                driver.execute_script("arguments[0].click();", btn)
                click_count += 1
                print(f"==> Đã bấm 'Xem thêm' lần thứ {click_count}")

                # Chờ 3 giây để AJAX load sản phẩm mới ra
                time.sleep(3)
            else:
                print("==> Nút Xem thêm bị ẩn (Đã tải hết).")
                break
        except Exception:
            print("==> Hoàn tất tải thêm (Không tìm thấy nút Xem thêm nữa)!")
            break

    # Lấy toàn bộ thẻ sản phẩm trong danh sách
    product_items = driver.find_elements(By.CSS_SELECTOR, "div.product-list-item")
    print(f"==> Tổng số sản phẩm thu thập được: {len(product_items)}")

    extracted_data = []

    for item in product_items:
        try:
            # 1. Tên & Link sản phẩm
            name_tag = item.find_element(By.CSS_SELECTOR, "div.product-item-left p.name a")
            name = name_tag.text.strip()
            product_url = name_tag.get_attribute("href")

            # 2. Giá sản phẩm
            try:
                price = item.find_element(By.CSS_SELECTOR, "div.product-item-left p.price").text.strip()
            except Exception:
                price = None

            # 3. Link Ảnh
            try:
                img_tag = item.find_element(By.CSS_SELECTOR, "div.product-item-image img")
                # Lấy src hoặc data-original-src phòng trường hợp lazy load
                image_url = img_tag.get_attribute("src") or img_tag.get_attribute("data-original-src")
            except Exception:
                image_url = None

            # 4. Nhãn tem (Hot, New...)
            try:
                badge = item.find_element(By.CSS_SELECTOR, "div.hot-and-new span").text.strip()
            except Exception:
                badge = None

            # 5. Thông tin Bảo hành / Ưu đãi (Mask list)
            warranty_policy = []
            try:
                mask_items = item.find_elements(By.CSS_SELECTOR, "div.mask ul.mask-list li")
                for m in mask_items:
                    warranty_policy.append(m.text.strip())
            except Exception:
                pass

            if name:
                extracted_data.append({
                    "name": name,
                    "price": price,
                    "badge": badge,
                    "product_url": product_url,
                    "image_url": image_url,
                    "warranty_policy": warranty_policy,
                })
        except Exception as e:
            continue

    driver.quit()

    # Xuất file JSON
    output_filename = "mobilecity_iphone_29_09.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, ensure_ascii=False, indent=4)

    print(f"==> HOÀN THÀNH! Đã xuất {len(extracted_data)} sản phẩm vào file '{output_filename}'.")


if __name__ == "__main__":
    crawl_mobilecity()