import json
import re
import scrapy
from fptshop.items import FptShopItem


class FptShopSpider(scrapy.Spider):
    name = "fptshop"
    allowed_domains = ["fptshop.com.vn"]
    start_urls = ["https://fptshop.com.vn/dien-thoai/apple-iphone"]

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
        "DOWNLOAD_DELAY": 1.0,
    }

    def parse(self, response):
        """
        Duyệt trang danh mục FPT Shop để lấy các liên kết đến trang chi tiết iPhone.
        CHỈ thu thập điện thoại iPhone.
        """
        links = response.css("a[href*='/dien-thoai/iphone-']::attr(href)").getall()

        seen_links = set()
        for link in links:
            clean_link = link.split("?")[0].split("#")[0].strip()
            if not clean_link or clean_link in seen_links:
                continue

            # Đảm bảo chỉ cào điện thoại iPhone
            if "/dien-thoai/iphone" not in clean_link:
                continue

            seen_links.add(clean_link)
            yield response.follow(clean_link, callback=self.parse_product)

        self.logger.info(f"Đã tìm thấy {len(seen_links)} sản phẩm iPhone từ {response.url}")

    def parse_product(self, response):
        """
        Trích xuất thông tin sản phẩm từ trang chi tiết iPhone của FPT Shop.
        """
        # 1. Trích xuất Schema.org JSON-LD
        ld_name = None
        ld_price = None
        ld_image = None
        ld_desc = None

        for script in response.xpath("//script[@type='application/ld+json']/text()").getall():
            try:
                data = json.loads(script)
                if data.get("@type") == "Product":
                    ld_name = data.get("name")
                    ld_image = data.get("image")
                    ld_desc = data.get("description")
                    offers = data.get("offers")
                    if isinstance(offers, dict):
                        ld_price = offers.get("price")
            except Exception:
                pass

        # 2. Tên sản phẩm
        h1 = response.css("h1::text").get()
        product_name = (h1 or ld_name or "").strip()
        
        # Chỉ nhận sản phẩm có chữ iPhone
        if not product_name or "iphone" not in product_name.lower():
            return

        # 3. Giá bán và giá gốc
        price_text = None
        if ld_price:
            price_text = f"{int(float(ld_price)):,}đ".replace(",", ".")

        all_prices = response.css("div.product-detail-info ::text").re(r"[\d\.]+\s*đ")
        original_price = None
        if all_prices:
            if not price_text:
                price_text = all_prices[0]
            if len(all_prices) > 1:
                original_price = all_prices[1] if all_prices[1] != price_text else None

        if not original_price:
            original_price = price_text

        # 4. Trích xuất mã sản phẩm (No. ...)
        sku_match = response.xpath("//text()[contains(., 'No.')]").re_first(r"No\.\s*([0-9A-Za-z]+)")

        # 5. Trích xuất dung lượng (ROM)
        cap_match = re.search(r"(\d+\s*(?:GB|TB))", product_name, re.IGNORECASE)
        capacity = cap_match.group(1).upper() if cap_match else "Mặc định"

        # 6. Trích xuất danh sách màu sắc trong div.product-detail-info
        colors = []
        info_block = response.css("div.product-detail-info")
        if info_block:
            color_section = info_block.xpath(".//div[contains(text(), 'Màu sắc') or .//div[contains(text(), 'Màu sắc')]]/following-sibling::div[1]")
            if color_section:
                btn_colors = color_section.css("button ::text").getall()
                colors = [c.strip() for c in btn_colors if c.strip() and not re.search(r"GB|TB|đ|₫", c)]
            
            if not colors:
                for btn in info_block.css("button"):
                    txt = btn.css("::text").get(default="").strip()
                    if txt and not re.search(r"\d+\s*(?:GB|TB)|đ|₫|Giao hàng|Nhận tại", txt):
                        colors.append(txt)

        # 7. Ảnh sản phẩm
        image_url = ld_image or response.css("img[alt*='iPhone']::attr(src)").get()

        category = "iPhone"

        # Nếu có danh sách màu, sinh item theo từng màu sắc
        if colors:
            for col in colors:
                item = FptShopItem(
                    name=f"{product_name} - {col}",
                    category=category,
                    capacity=capacity,
                    colour=col,
                    price=price_text.strip() if price_text else None,
                    original_price=original_price.strip() if original_price else price_text,
                    discount_amount=None,
                    currency="VND",
                    product_code=sku_match,
                    image_url=image_url,
                    product_url=response.url,
                    description=ld_desc,
                )
                yield item
        else:
            item = FptShopItem(
                name=product_name,
                category=category,
                capacity=capacity,
                colour="Mặc định",
                price=price_text.strip() if price_text else None,
                original_price=original_price.strip() if original_price else price_text,
                discount_amount=None,
                currency="VND",
                product_code=sku_match,
                image_url=image_url,
                product_url=response.url,
                description=ld_desc,
            )
            yield item
