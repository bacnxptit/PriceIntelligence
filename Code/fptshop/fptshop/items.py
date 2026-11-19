import scrapy


class FptShopItem(scrapy.Item):
    name = scrapy.Field()
    category = scrapy.Field()
    capacity = scrapy.Field()
    colour = scrapy.Field()
    price = scrapy.Field()
    original_price = scrapy.Field()
    discount_amount = scrapy.Field()
    currency = scrapy.Field()
    product_code = scrapy.Field()
    image_url = scrapy.Field()
    product_url = scrapy.Field()
    description = scrapy.Field()
