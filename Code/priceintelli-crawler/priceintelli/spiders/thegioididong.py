import scrapy


class IphoneTgddSpider(scrapy.Spider):
    name = "thegioididong"
    collection_name = "iphone_thegioididong"
    allowed_domains = ["www.thegioididong.com"]
    start_urls = ["https://www.thegioididong.com/dtdd-apple-iphone"]

    # Cấu hình Custom Settings trực tiếp trong Spider để giả lập trình duyệt thật
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.google.com/',
            'Sec-Ch-Ua': '"Chromium";v="128", "Not=A?Brand";v="24", "Google Chrome";v="128"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        },
        'ROBOTSTXT_OBEY': False,  # Bỏ qua robot.txt nếu bị cản trở
        'DOWNLOAD_DELAY': 1.5,     # Tăng độ trễ giữa các request để tránh bị chặn IP
    }

    def parse(self, response):
        products = response.xpath("//ul[@class='listproduct']/li/a")
        for product in products:
            name = product.xpath(".//p/text()").get(default='').strip()
            link = product.xpath(".//@href").get()
            
            # Đã sửa callback=self.parse_country thành self.parse_product
            yield response.follow(url=link, callback=self.parse_product, meta={"product_name": name})
    
    def parse_product(self, response):
        name = response.meta.get("product_name")

        groups = response.xpath("//div[contains(@class, 'box03 group desk')]/a")

        # Trường hợp sản phẩm có nhiều dung lượng
        if groups:
            for group in groups:
                group_capacity = group.xpath(".//text()").get()
                group_link = group.xpath(".//@href").get()

                yield response.follow(
                    url=group_link, 
                    callback=self.parse_group, 
                    meta={"product_name": name, "product_capacity": group_capacity}
                )
        else:
            # Nếu sản phẩm không chia dung lượng, chuyển thẳng sang cào màu sắc
            yield scrapy.Request(
                url=response.url, 
                callback=self.parse_group, 
                meta={"product_name": name, "product_capacity": "Mac dinh"},
                dont_filter=True
            )
    
    def parse_group(self, response):
        name = response.meta.get("product_name")
        capacity = response.meta.get("product_capacity")
        colours = response.xpath("//div[contains(@class, 'box03 color desk')]/a")

        if colours:
            for colour in colours:
                colour_name = colour.xpath(".//text()").get()
                colour_link = colour.xpath(".//@href").get()

                yield response.follow(
                    url=colour_link, 
                    callback=self.parse_colour, 
                    meta={"product_name": name, "product_capacity": capacity, "product_colour": colour_name}
                )
        else:
            yield scrapy.Request(
                url=response.url, 
                callback=self.parse_colour, 
                meta={"product_name": name, "product_capacity": capacity, "product_colour": "Mac dinh"},
                dont_filter=True
            )
        
    def parse_colour(self, response):
        name = response.meta.get("product_name")
        capacity = response.meta.get("product_capacity")
        colour = response.meta.get("product_colour")

        price = response.xpath("//div[contains(@class, 'box_servicepack')]//span/b/text()").get()
        
        original_price = response.xpath("//div[contains(@class, 'box_servicepack')]//span/em/text()").get()
        average_rating = response.xpath("//text[@class='point-average-score']/text()").get()
        total_satisfied = response.xpath("//p[@class='point-satisfied']/text()").get()
        total_rated = response.xpath("//span[@class='point-alltimerate']/text()").get()


        yield {
            "name": name,
            "capacity": capacity,
            "colour": colour,
            "price": price,
            "original_price": original_price,
            "average_rating": average_rating,
            "total_satisfied": total_satisfied,
            "total_rated": total_rated,
            "link": response.url,
        }