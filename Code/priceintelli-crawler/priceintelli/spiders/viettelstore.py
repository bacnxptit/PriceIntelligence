import time
import scrapy
from parsel import Selector
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class IphoneViettelstoreSpider(scrapy.Spider):
    name = "viettelstore"
    collection_name = "iphone_viettelstore"
    allowed_domains = ["viettelstore.vn"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        opts = Options()
        # KHÔNG bật headless để giống hệt bản Selenium thuần đang chạy được
        # opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--no-sandbox")
        opts.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        self.driver = webdriver.Chrome(options=opts)

    async def start(self):
        url = "https://www.viettelstore.vn/dtdd-apple-iphone"
        self.logger.info(f"==> [Selenium] Mở: {url}")
        self.driver.get(url)
        time.sleep(3)

        # Vòng lặp click "Xem thêm" — y hệt bản Selenium thuần
        click_count = 0
        while True:
            try:
                btn = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "#div_Danh_Sach_San_Pham_loadMore_btn a",
                )
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

        # Parse DOM thật bằng parsel (thay cho BeautifulSoup)
        sel = Selector(text=self.driver.page_source)
        products = sel.css("div.product-info-container")
        self.logger.info(f"==> TỔNG SỐ SẢN PHẨM: {len(products)}")

        for product in products:
            link_tag = product.css("div.product-info > a")
            raw_href = link_tag.attrib.get("href", "")

            yield {
                "product_id": link_tag.attrib.get("data-id"),
                "brand_id": link_tag.attrib.get("data-brand"),
                "name": (
                    product.css("div.product-name h3::text").get(default="").strip()
                    or (link_tag.attrib.get("data-name") or "").strip()
                ),
                "price": product.css("div.block-box-price div.price::text").get(default="").strip(),
                "price_old": product.css("div.block-box-price div.price-old::text").get(default="").strip(),
                "raw_data_price": link_tag.attrib.get("data-price"),
                "discount_percent": product.css("div.percent-discount-text2::text").get(default="").strip(),
                "product_url": (
                    raw_href if raw_href.startswith("http")
                    else f"https://www.viettelstore.vn{raw_href}"
                ),
                "image_url": product.css("div.product-image img::attr(src)").get(),
                "promotions": product.css("div.product-promotions p.promotion-text::text").get(default="").strip(),
                "stickers": product.css("div[class^='ico-stick'] img::attr(alt)").getall(),
            }

    def closed(self, reason):
        self.driver.quit()
        self.logger.info("==> Đã đóng Selenium Driver.")