import json
import re
import scrapy
from topzone.items import TopzoneItem


class TopzoneSpider(scrapy.Spider):
    name = "topzone"
    allowed_domains = ["topzone.vn"]
    start_urls = ["https://www.topzone.vn/iphone"]

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
        Duyệt qua danh sách sản phẩm trên trang danh mục iPhone của TopZone.
        CHỈ thu thập điện thoại iPhone.
        """
        items = response.css("ul.listing-cate li.item")
        self.logger.info(f"Tìm thấy {len(items)} thẻ sản phẩm trên {response.url}")

        seen_links = set()

        for it in items:
            link_el = it.css("a.main-contain")
            if not link_el:
                continue

            href = link_el.attrib.get("href")
            if not href or href in seen_links:
                continue

            # Đảm bảo chỉ cào iPhone
            if not href.startswith("/iphone/") and "iphone" not in href.lower():
                continue

            seen_links.add(href)

            card_id = link_el.attrib.get("data-id")
            card_name = link_el.attrib.get("data-name")
            card_price = link_el.attrib.get("data-price")
            card_cate = "iPhone"
            img_el = link_el.css("img.thumb::attr(src), img.thumb::attr(data-src)").get()

            # Lấy thông tin các nhóm dung lượng (256GB, 512GB, 1TB...)
            capacity_tags = it.css("div.prods-group ul li.merge__item")
            additional_urls = []
            for cap in capacity_tags:
                cap_url = cap.attrib.get("data-url")
                if cap_url and cap_url not in ["//", href] and cap_url not in seen_links:
                    if "/iphone" in cap_url:
                        seen_links.add(cap_url)
                        additional_urls.append(cap_url)

            meta_data = {
                "card_id": card_id,
                "card_name": card_name,
                "card_price": card_price,
                "card_cate": card_cate,
                "card_img": img_el,
            }

            yield response.follow(
                url=href,
                callback=self.parse_product,
                meta=meta_data,
            )

            for extra_url in additional_urls:
                yield response.follow(
                    url=extra_url,
                    callback=self.parse_product,
                    meta=meta_data,
                )

    def parse_product(self, response):
        """
        Trích xuất thông tin chi tiết từng sản phẩm iPhone:
        Tên máy, Dung lượng, Màu sắc, Giá bán, Giá gốc, Khuyến mãi, Ảnh chất lượng cao.
        """
        card_id = response.meta.get("card_id")
        card_name = response.meta.get("card_name")
        card_price = response.meta.get("card_price")
        card_cate = "iPhone"
        card_img = response.meta.get("card_img")

        # 1. Trích xuất Schema.org JSON-LD
        ld_name = None
        ld_price = None
        ld_image = None
        for script in response.xpath("//script[@type='application/ld+json']/text()").getall():
            try:
                data = json.loads(script)
                if data.get("@type") == "Product":
                    ld_name = data.get("name")
                    ld_image = data.get("image")
                    if isinstance(ld_image, list) and ld_image:
                        ld_image = ld_image[0]
                    offers = data.get("offers")
                    if isinstance(offers, dict):
                        ld_price = offers.get("price")
            except Exception:
                pass

        # 2. Tên sản phẩm
        title = response.css("h1::text").get()
        product_name = (title or ld_name or card_name or "").strip()

        # Đảm bảo chỉ lấy iPhone
        if not product_name or "iphone" not in product_name.lower():
            return

        # 3. Giá bán và giá gốc
        price_text = response.css("p.box-price-present::text, strong.price::text").get()
        old_price_text = response.css("p.box-price-old::text").get()
        discount_text = response.css("p.box-price-percent::text").get()

        if not price_text and (ld_price or card_price):
            raw_p = ld_price or card_price
            price_text = f"{int(float(raw_p)):,}₫".replace(",", ".")

        price_clean = price_text.strip() if price_text else None
        old_price_clean = old_price_text.strip() if old_price_text else price_clean
        discount_clean = discount_text.strip() if discount_text else None

        # 4. Trích xuất dung lượng (ROM/RAM)
        cap_match = re.search(r"(\d+\s*(?:GB|TB))", product_name, re.IGNORECASE)
        capacity = cap_match.group(1).upper() if cap_match else "Mặc định"

        # 5. Ảnh sản phẩm
        image_url = ld_image or card_img or response.css("div.item-img img::attr(src)").get()

        # 6. Mô tả / Đặc điểm nổi bật
        desc = response.css("div.text-detail p::text, div.content-detail p::text").getall()
        description = " ".join([d.strip() for d in desc if d.strip()]) or None

        # 7. Danh sách các màu sắc khả dụng (trong div.color-sp)
        colors_list = []
        color_elements = response.css("div.color-sp ul li")
        for cel in color_elements:
            c_name = cel.attrib.get("data-name", "")
            cleaned_color = re.sub(r"^Màu:\s*", "", c_name).strip()
            c_code = cel.attrib.get("data-code")
            if cleaned_color:
                colors_list.append((cleaned_color, c_code))

        if colors_list:
            for colour_name, code in colors_list:
                item = TopzoneItem(
                    name=f"{product_name} - {colour_name}",
                    category=card_cate,
                    capacity=capacity,
                    colour=colour_name,
                    price=price_clean,
                    original_price=old_price_clean,
                    discount_percent=discount_clean,
                    currency="VND",
                    product_id=card_id,
                    product_code=code,
                    image_url=image_url,
                    product_url=response.url,
                    description=description,
                )
                yield item
        else:
            item = TopzoneItem(
                name=product_name,
                category=card_cate,
                capacity=capacity,
                colour="Mặc định",
                price=price_clean,
                original_price=old_price_clean,
                discount_percent=discount_clean,
                currency="VND",
                product_id=card_id,
                product_code=None,
                image_url=image_url,
                product_url=response.url,
                description=description,
            )
            yield item
