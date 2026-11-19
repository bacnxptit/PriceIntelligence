import time
import scrapy
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class IphoneMobilecitySpider(scrapy.Spider):
    name = "iphone_mobilecity"
    allowed_domains = ["mobilecity.vn"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        opts = Options()
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        self.driver = webdriver.Chrome(options=opts)

    def start_requests(self):
        url = "https://mobilecity.vn/dien-thoai-iphone-chinh-hang-vna"
        self.logger.info(f"==> [Selenium] Truy cập: {url}")
        self.driver.get(url)
        self.driver.maximize_window()
        time.sleep(3)

        click_count = 0
        while True:
            try:
                btn = self.driver.find_element(By.ID, "product_view_more")
                if btn.is_displayed():
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'});", btn
                    )
                    time.sleep(1)
                    self.driver.execute_script("arguments[0].click();", btn)
                    click_count += 1
                    self.logger.info(f"==> Bấm 'Xem thêm' lần {click_count}")
                    time.sleep(3)
                else:
                    break
            except Exception:
                break

        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        product_items = soup.select("div.product-list-item")
        self.logger.info(f"==> TỔNG SỐ SẢN PHẨM: {len(product_items)}")

        for it in product_items:
            name_tag = it.select_one("div.product-item-left p.name a")
            if not name_tag or not name_tag.get_text(strip=True):
                continue

            raw = name_tag.get("href", "")
            price_tag = it.select_one("div.product-item-left p.price")
            img_tag = it.select_one("div.product-item-image img")
            badge_tag = it.select_one("div.hot-and-new span")
            mask_items = it.select("div.mask ul.mask-list li")

            # ⭐ yield thẳng item — không cần Request giả
            yield {
                "name": name_tag.get_text(strip=True),
                "price": price_tag.get_text(strip=True) if price_tag else None,
                "badge": badge_tag.get_text(strip=True) if badge_tag else None,
                "product_url": raw if raw.startswith("http") else f"https://mobilecity.vn{raw}",
                "image_url": (img_tag.get("src") or img_tag.get("data-original-src")) if img_tag else None,
                "warranty_policy": [m.get_text(strip=True) for m in mask_items],
            }

    def closed(self, reason):
        self.driver.quit()
        self.logger.info("==> Đã đóng Chrome Driver.")