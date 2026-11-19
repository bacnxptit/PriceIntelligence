import scrapy


class TopzoneItem(scrapy.Item):
    name = scrapy.Field()
    category = scrapy.Field()
    capacity = scrapy.Field()
    colour = scrapy.Field()
    price = scrapy.Field()
    original_price = scrapy.Field()
    discount_percent = scrapy.Field()
    currency = scrapy.Field()
    product_id = scrapy.Field()
    product_code = scrapy.Field()
    image_url = scrapy.Field()
    product_url = scrapy.Field()
    description = scrapy.Field()
