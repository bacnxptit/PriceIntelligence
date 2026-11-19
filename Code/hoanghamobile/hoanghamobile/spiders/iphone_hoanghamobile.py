import scrapy


class IphoneHoanghamobileSpider(scrapy.Spider):
    name = "iphone_hoanghamobile"
    allowed_domains = ["hoanghamobile.com"]
    start_urls = ["https://hoanghamobile.com/dien-thoai-di-dong/iphone"]

    # Bổ sung User-Agent và Header giả lập trình duyệt Chrome thật
    custom_settings = {
        "USER_AGENT": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
            ),
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://hoanghamobile.com/",
        },
        "ROBOTSTXT_OBEY": False,  # Bỏ qua file robots.txt nếu bị cản trở
        "DOWNLOAD_DELAY": 1.5,     # Tăng thời gian chờ giữa các request để tránh bị khoá IP
    }

    def parse(self, response):
        # Kiểm tra xem có lấy được nội dung HTML thật không
        products = response.css("div.pj16-item, div.item")

        # Trường hợp lấy danh sách sản phẩm thành công
        for product in products:
            name = product.css("h3 a::text, div.name a::text").get()
            product_url = product.css("h3 a::attr(href), div.name a::attr(href)").get()
            price = product.css("div.price-tags div.price strong::text, span.price::text").get()
            original_price = product.css("div.price-last strike::text").get()
            image_url = product.css("div.img-info img::attr(src), div.img img::attr(src)").get()

            if name:
                yield {
                    "name": name.strip(),
                    "price": price.strip() if price else None,
                    "original_price": original_price.strip() if original_price else None,
                    "product_url": response.urljoin(product_url) if product_url else None,
                    "image_url": response.urljoin(image_url) if image_url else None,
                }

        # Xử lý nút phân trang "Xem thêm"
        next_page = response.css("div.v5-more-product#page-pager a::attr(href), div#page-pager a::attr(href)").get()
        if next_page:
            yield scrapy.Request(
                url=response.urljoin(next_page),
                callback=self.parse
            )