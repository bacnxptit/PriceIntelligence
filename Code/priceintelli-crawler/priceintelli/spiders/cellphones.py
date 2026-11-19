import time
import scrapy
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class CellphonesSpider(scrapy.Spider):
    name = "cellphones"
    collection_name = "iphone_cellphones"
    allowed_domains = ["cellphones.com.vn"]
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
        # Giảm dấu hiệu "automation" để qua Cloudflare dễ hơn
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)

        self.driver = webdriver.Chrome(options=opts)
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
        )

    def start_requests(self):
        url = "https://cellphones.com.vn/mobile/apple.html"
        self.logger.info(f"==> [Selenium] Mở: {url}")
        self.driver.get(url)
        try:
            self.driver.maximize_window()
        except Exception:
            pass
        time.sleep(3)

        # Vòng lặp bấm "Xem thêm"
        click_count = 0
        while True:
            try:
                btn_more = self.driver.find_element(
                    By.CSS_SELECTOR, "a.btn-show-more, div.btn-show-more"
                )
                if btn_more.is_displayed():
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'});", btn_more
                    )
                    time.sleep(1)
                    self.driver.execute_script("arguments[0].click();", btn_more)
                    click_count += 1
                    self.logger.info(f"==> Bấm 'Xem thêm' lần {click_count}")
                    time.sleep(2.5)
                else:
                    break
            except Exception:
                break

        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        # Kiểm tra DOM thật — in ra 1 mẫu để debug selector
        product_items = soup.select("div.product-item")
        self.logger.info(f"==> TỔNG SỐ SẢN PHẨM: {len(product_items)}")

        if not product_items:
            # Log vài class thực tế để bạn cập nhật selector
            self.logger.warning("Không khớp selector. 20 class đầu tiên trong DOM:")
            classes = set()
            for tag in soup.find_all(True, class_=True)[:200]:
                for c in tag.get("class", []):
                    if "product" in c.lower():
                        classes.add(c)
            self.logger.warning(f"   {sorted(classes)}")

        for p in product_items:
            name_el = p.select_one(".product__name h3, .product__name, h3")
            price_show_el = p.select_one(".product__price--show")
            price_through_el = p.select_one(".product__price--through")
            promo_el = p.select_one(".product__promotions p, .gift-cont")
            link_el = p.select_one("a[href]")

            if not (name_el and name_el.get_text(strip=True)):
                continue

            raw_url = link_el["href"] if link_el else ""
            full_url = raw_url if raw_url.startswith("http") else f"https://cellphones.com.vn{raw_url}"

            yield {
                "name": name_el.get_text(strip=True),
                "price_sale": price_show_el.get_text(strip=True) if price_show_el else None,
                "price_original": price_through_el.get_text(strip=True) if price_through_el else None,
                "promotion": promo_el.get_text(strip=True) if promo_el else None,
                "url": full_url,
            }

    def closed(self, reason):
        self.driver.quit()
        self.logger.info("==> Đã đóng Selenium Chrome Driver.")