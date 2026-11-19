import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


def crawl_viettelstore():
    # 1. Cấu hình Chrome
    chrome_options = Options()
    # Nếu muốn xem trình duyệt tự cuộn và bấm nút, hãy đổi "--headless" thành "# --headless"
    chrome_options.add_argument("# --headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

    print("==> Đang khởi tạo trình duyệt Chrome...")
    driver = webdriver.Chrome(
        options=chrome_options,
    )

    url = "https://www.viettelstore.vn/dtdd-apple-iphone"
    print(f"==> Đang truy cập URL: {url}")
    driver.get(url)
    time.sleep(3)  # Chờ 3 giây để trang tải xong

    # 2. Vòng lặp tự động tìm và click nút "Xem thêm"
    click_count = 0
    while True:
        try:
            # Tìm nút "Xem thêm"
            btn = driver.find_element(
                By.CSS_SELECTOR, "#div_Danh_Sach_San_Pham_loadMore_btn a"
            )

            if btn.is_displayed():
                # Cuộn chuột xuống vị trí nút bấm
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(1)

                # Click nút bằng JavaScript
                driver.execute_script("arguments[0].click();", btn)
                click_count += 1
                print(f"==> Đã bấm 'Xem thêm' lần thứ {click_count}")

                # Chờ 3 giây để sản phẩm mới load ra
                time.sleep(3)
            else:
                print("==> Đã tải hết sản phẩm (Nút Xem thêm bị ẩn).")
                break
        except Exception as e:
            print("==> Đã tải hoàn tất toàn bộ sản phẩm!")
            break

    # 3. Lấy toàn bộ thẻ sản phẩm sau khi đã click Xem thêm xong
    products_elements = driver.find_elements(By.CSS_SELECTOR, "div.product-info-container")
    print(f"==> Tổng số sản phẩm thu thập được: {len(products_elements)}")

    extracted_data = []

    for product in products_elements:
        try:
            # Tìm thẻ chứa link và data-attributes
            link_tag = product.find_element(By.CSS_SELECTOR, "div.product-info > a")
            product_id = link_tag.get_attribute("data-id")
            brand_id = link_tag.get_attribute("data-brand")
            data_name = link_tag.get_attribute("data-name")
            data_price = link_tag.get_attribute("data-price")
            product_url = link_tag.get_attribute("href")

            # Tên sản phẩm hiển thị
            try:
                name_elem = product.find_element(By.CSS_SELECTOR, "div.product-name h3")
                name = name_elem.text.strip()
            except Exception:
                name = data_name.strip() if data_name else None

            # Giá bán
            try:
                price_elem = product.find_element(By.CSS_SELECTOR, "div.block-box-price div.price")
                price = price_elem.text.strip()
            except Exception:
                price = None

            # Giá niêm yết cũ
            try:
                price_old_elem = product.find_element(By.CSS_SELECTOR, "div.block-box-price div.price-old")
                price_old = price_old_elem.text.strip()
            except Exception:
                price_old = None

            # % Giảm giá
            try:
                discount_elem = product.find_element(By.CSS_SELECTOR, "div.percent-discount-text2")
                discount = discount_elem.text.strip()
            except Exception:
                discount = None

            # Ảnh sản phẩm
            try:
                img_elem = product.find_element(By.CSS_SELECTOR, "div.product-image img")
                image_url = img_elem.get_attribute("src")
            except Exception:
                image_url = None

            # Khuyến mãi
            try:
                promo_elem = product.find_element(By.CSS_SELECTOR, "div.product-promotions p.promotion-text")
                promotions = promo_elem.text.strip()
            except Exception:
                promotions = None

            # Nhãn dán / Sticker
            stickers = []
            try:
                sticker_elems = product.find_elements(By.CSS_SELECTOR, "div[class^='ico-stick'] img")
                for st in sticker_elems:
                    alt = st.get_attribute("alt")
                    if alt:
                        stickers.append(alt.strip())
            except Exception:
                pass

            if name:
                extracted_data.append({
                    "product_id": product_id,
                    "brand_id": brand_id,
                    "name": name,
                    "price": price,
                    "price_old": price_old,
                    "raw_data_price": data_price,
                    "discount_percent": discount,
                    "product_url": product_url,
                    "image_url": image_url,
                    "promotions": promotions,
                    "stickers": stickers
                })
        except Exception as e:
            continue

    driver.quit()

    # 4. Ghi kết quả ra file JSON đúng chuẩn UTF-8
    output_filename = "viettelstore_iphone_29_09.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, ensure_ascii=False, indent=4)

    print(f"==> HOÀN THÀNH! Đã xuất {len(extracted_data)} sản phẩm vào file '{output_filename}'.")


if __name__ == "__main__":
    crawl_viettelstore()