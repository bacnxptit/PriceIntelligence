import json
import re
import scrapy
from applestore.items import AppleStoreItem


class AppleStoreSpider(scrapy.Spider):
    name = "apple_store"
    allowed_domains = ["apple.com"]
    start_urls = ["https://www.apple.com/vn/shop/buy-iphone"]

    custom_settings = {
        "USER_AGENT": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.google.com/",
        },
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_DELAY": 1.5,
    }

    def parse(self, response):
        """
        Duyệt trang danh mục iPhone chính thức của Apple Store VN:
        Tìm các thẻ sản phẩm (iPhone 16, 16 Pro,...) và chuyển tiếp đến trang chi tiết.
        """
        # Thu thập các thẻ sản phẩm trong mục 'Mọi phiên bản'
        cards = response.css("div.rf-cards-scroller-item")
        found_links = set()

        for card in cards:
            link = card.css("a[href*='/vn/shop/buy-iphone/']::attr(href)").get()
            if not link or link in found_links:
                continue

            found_links.add(link)

            # Lấy tên sản phẩm & giá khởi điểm hiển thị trên thẻ
            name_text = card.css(".rf-hcard-content ::text").getall()
            full_text = " ".join([t.strip() for t in name_text if t.strip()])

            price_match = re.search(r"Từ\s*([\d\.]+\s*đ)", full_text)
            starting_price = price_match.group(1) if price_match else None

            # Tên tiêu đề sản phẩm
            title = card.css("h3::text, .rf-hcard-copy h3::text, span[class*='header']::text").get()
            if not title:
                # Lấy từ text nếu không có thẻ h3
                title_match = re.search(r"(iPhone\s*[\w\s\+]+?)(?=\s*Tìm hiểu|\s*Từ|$)", full_text)
                title = title_match.group(1) if title_match else "Apple iPhone"

            yield response.follow(
                url=link,
                callback=self.parse_product,
                meta={
                    "series_name": title.strip(),
                    "starting_price": starting_price,
                },
            )

    def parse_product(self, response):
        """
        Thu thập thông tin chi tiết từng phiên bản iPhone:
        Ưu tiên đọc dữ liệu cấu hình JSON (id='metrics') và Schema.org JSON-LD có sẵn trong mã nguồn.
        """
        series_name = response.meta.get("series_name", "iPhone")
        starting_price = response.meta.get("starting_price")

        # 1. Trích xuất metadata từ JSON-LD (Schema.org Product)
        ld_name = None
        ld_desc = None
        ld_image = None
        ld_price = None

        for script in response.xpath("//script[@type='application/ld+json']/text()").getall():
            try:
                data = json.loads(script)
                if data.get("@type") == "Product":
                    ld_name = data.get("name")
                    ld_desc = data.get("description")
                    ld_image = data.get("image")
                    offers = data.get("offers", [])
                    if isinstance(offers, list) and offers:
                        offer = offers[0]
                        ld_price = offer.get("lowPrice") or offer.get("price")
                    elif isinstance(offers, dict):
                        ld_price = offers.get("lowPrice") or offers.get("price")
            except Exception:
                continue

        # 2. Trích xuất biến thể chi tiết (SKU, Part Number, Màu sắc, Dung lượng, Giá) từ script id="metrics"
        metrics_script = response.xpath("//script[@id='metrics']/text()").get()
        variants_yielded = 0

        if metrics_script:
            try:
                metrics_data = json.loads(metrics_script)
                products_list = metrics_data.get("data", {}).get("products", [])

                for prod in products_list:
                    p_name = prod.get("name") or ld_name or series_name
                    if not p_name or "iphone" not in p_name.lower():
                        continue
                    p_sku = prod.get("sku")
                    p_part = prod.get("partNumber")
                    p_price_val = prod.get("price", {}).get("fullPrice") or ld_price

                    # Định dạng giá tiền
                    if p_price_val:
                        price_formatted = f"{int(p_price_val):,}đ".replace(",", ".")
                    else:
                        price_formatted = starting_price

                    # Trích xuất dung lượng (GB, TB)
                    cap_match = re.search(r"(\d+\s*(?:GB|TB))", p_name, re.IGNORECASE)
                    capacity = cap_match.group(1).upper() if cap_match else "Mặc định"

                    # Trích xuất màu sắc (từ cuối tên hoặc sau dung lượng)
                    colour = "Mặc định"
                    if cap_match:
                        parts = p_name.split(cap_match.group(1))
                        if len(parts) > 1 and parts[1].strip():
                            colour = parts[1].strip()

                    item = AppleStoreItem(
                        name=p_name.strip(),
                        product_series=series_name,
                        capacity=capacity,
                        colour=colour,
                        price=price_formatted,
                        original_price=price_formatted,
                        currency="VND",
                        sku=p_sku,
                        part_number=p_part,
                        image_url=ld_image,
                        product_url=response.url,
                        description=ld_desc,
                    )
                    variants_yielded += 1
                    yield item
            except Exception as e:
                self.logger.warning("Không thể parse script metrics: %s", e)

        # 3. Fallback: Nếu không có metrics script, trả về thông tin chung từ JSON-LD / HTML
        if variants_yielded == 0:
            price_val = f"{int(ld_price):,}đ".replace(",", ".") if ld_price else starting_price
            item = AppleStoreItem(
                name=ld_name or series_name,
                product_series=series_name,
                capacity="Mặc định",
                colour="Mặc định",
                price=price_val,
                original_price=price_val,
                currency="VND",
                sku=None,
                part_number=None,
                image_url=ld_image,
                product_url=response.url,
                description=ld_desc,
            )
            yield item
