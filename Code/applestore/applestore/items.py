import scrapy


class AppleStoreItem(scrapy.Item):
    name = scrapy.Field()
    product_series = scrapy.Field()
    capacity = scrapy.Field()
    colour = scrapy.Field()
    price = scrapy.Field()
    original_price = scrapy.Field()
    currency = scrapy.Field()
    sku = scrapy.Field()
    part_number = scrapy.Field()
    image_url = scrapy.Field()
    product_url = scrapy.Field()
    description = scrapy.Field()
