import scrapy


class ProductItem(scrapy.Item):
    name = scrapy.Field()
    title = scrapy.Field()
    price = scrapy.Field()
    current_price = scrapy.Field()
    original_price = scrapy.Field()
    price_sale = scrapy.Field()
    price_original = scrapy.Field()
    discount_amount = scrapy.Field()
    discount_percent = scrapy.Field()
    category = scrapy.Field()
    capacity = scrapy.Field()
    colour = scrapy.Field()
    color = scrapy.Field()
    currency = scrapy.Field()
    product_code = scrapy.Field()
    product_id = scrapy.Field()
    sku = scrapy.Field()
    part_number = scrapy.Field()
    image_url = scrapy.Field()
    product_url = scrapy.Field()
    url = scrapy.Field()
    link = scrapy.Field()
    description = scrapy.Field()
    rating = scrapy.Field()
    rating_score = scrapy.Field()
    review_count = scrapy.Field()
    total_rated = scrapy.Field()
    crawled_at = scrapy.Field()


class AppleStoreItem(ProductItem):
    product_series = scrapy.Field()


class FptShopItem(ProductItem):
    pass


class TopzoneItem(ProductItem):
    pass
