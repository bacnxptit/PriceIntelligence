import os
import re
import sys
from urllib.parse import urlparse

import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

MONGO_DB = os.getenv("MONGODB_DB", "imdb")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "all")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "output.txt")


def _source_column(documents: pd.DataFrame, *names: str) -> pd.Series:
    """Combine first non-null values across candidate column names."""
    values = pd.Series(pd.NA, index=documents.index, dtype="object")
    for name in names:
        if name in documents.columns:
            values = values.combine_first(documents[name])
    return values


def fetch_raw_documents(client: MongoClient, db_name: str, collection_target: str = "all") -> list[dict]:
    """Fetch raw documents from one or all iphone collections in MongoDB."""
    db = client[db_name]
    if collection_target and collection_target not in ("all", "iphone_*", "*"):
        collections = [collection_target]
    else:
        collections = sorted([c for c in db.list_collection_names() if c.startswith("iphone_")])
        if not collections:
            collections = [collection_target] if collection_target else []

    all_docs = []
    for col_name in collections:
        for doc in db[col_name].find({}):
            doc_copy = dict(doc)
            if "source_collection" not in doc_copy:
                doc_copy["source_collection"] = col_name
            # Fallback crawled_at from ObjectId generation time if missing
            if not doc_copy.get("crawled_at") and "_id" in doc_copy and hasattr(doc_copy["_id"], "generation_time"):
                doc_copy["crawled_at"] = doc_copy["_id"].generation_time
            all_docs.append(doc_copy)
    return all_docs


def prepare_for_normalize(documents: list[dict]) -> pd.DataFrame:
    """Map raw fields from crawlers across all retail stores into a unified schema."""
    if not documents:
        return pd.DataFrame(columns=[
            "_id", "title", "sku", "current_price", "original_price",
            "discount_percent", "rating_score", "review_count",
            "capacity", "crawled_at", "url", "source_collection"
        ])

    source = pd.DataFrame(documents)
    if "_id" in source.columns:
        source["_id"] = source["_id"].map(str)

    source["title"] = _source_column(source, "title", "name", "product_name").fillna("")
    source["sku"] = _source_column(
        source, "sku", "part_number", "product_code", "product_id", "url", "product_url", "link"
    )
    source["current_price"] = _source_column(
        source, "current_price", "price", "price_sale"
    )
    source["original_price"] = _source_column(
        source, "original_price", "price_original", "price_old"
    )
    source["discount_percent"] = _source_column(
        source, "discount_percent", "discount_amount"
    )
    source["rating_score"] = _source_column(
        source, "rating_score", "average_rating", "rating"
    )
    source["review_count"] = _source_column(
        source, "review_count", "total_rated", "reviews"
    ).astype("string").str.replace(r"[^\d]", "", regex=True).replace("", pd.NA)
    source["capacity"] = _source_column(source, "capacity", "storage")
    source["crawled_at"] = _source_column(source, "crawled_at")
    source["url"] = _source_column(source, "url", "product_url", "link")
    return source


def parse_price(value):
    """Convert formatted price such as '64.990.000 đ' to an integer rounded to 10,000."""
    if pd.isna(value):
        return None

    cleaned = re.sub(r"[^\d]", "", str(value))
    if not cleaned:
        return None

    price = int(cleaned)
    if price <= 0 or price > 200_000_000:
        return None

    return round(price / 10000) * 10000


STORE_DOMAIN_MAP = {
    "fptshop.com.vn": "FPT Shop",
    "thegioididong.com": "The Gioi Di Dong",
    "topzone.vn": "TopZone",
    "cellphones.com.vn": "CellphoneS",
    "hoanghamobile.com": "Hoang Ha Mobile",
    "viettelstore.vn": "Viettel Store",
    "mobilecity.vn": "Mobile City",
    "apple.com": "Apple Vietnam",
}


def get_store(url):
    """Infer the store name from the product URL."""
    if pd.isna(url):
        return "Khác"

    domain = urlparse(str(url)).netloc.lower().replace("www.", "")
    for store_domain, store_name in STORE_DOMAIN_MAP.items():
        if store_domain in domain:
            return store_name

    return "Khác"


def parse_discount(value):
    """Convert discount text such as '10%' or numeric string to float."""
    if pd.isna(value):
        return None

    text = str(value).strip()
    if text.replace(".", "").replace(",", "").isdigit():
        return float(text.replace(",", "."))

    match = re.search(r"(\d+(?:[.,]\d+)?)\s*%", text)
    if match:
        return float(match.group(1).replace(",", "."))

    return None


def parse_rating(value):
    """Convert rating text to a float between 0 and 5."""
    if pd.isna(value):
        return None

    match = re.search(r"(\d+(?:[.,]\d+)?)", str(value).strip())
    if match:
        rating = float(match.group(1).replace(",", "."))
        if 0 <= rating <= 5:
            return rating

    return None


def parse_capacity(value):
    """Convert capacity such as '256 GB' or '1 TB' (or embedded in title) to gigabytes."""
    if pd.isna(value):
        return None

    text = str(value).strip().upper().replace(" ", "")
    match = re.search(r"(\d+)(GB|TB)", text)
    if not match:
        return None

    amount, unit = int(match.group(1)), match.group(2)
    return amount * 1024 if unit == "TB" else amount


def format_product_name(title: str, capacity_gb) -> str:
    t = str(title).strip()
    if pd.isna(capacity_gb):
        return t
    if re.search(rf"\b{int(capacity_gb)}\s*GB\b", t, re.I):
        return t
    return f"{t} {int(capacity_gb)}GB"


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize product fields while retaining the original crawler data."""
    df = df.copy()
    df["store"] = df["url"].apply(get_store)
    df["price"] = df["current_price"].apply(parse_price)
    df["listed_price"] = df["original_price"].apply(parse_price)
    df["discount_pct"] = df["discount_percent"].apply(parse_discount)

    missing_discount = (
        df["discount_pct"].isna()
        & df["price"].notna()
        & df["listed_price"].notna()
    )
    df.loc[missing_discount, "discount_pct"] = (
        (
            df.loc[missing_discount, "listed_price"]
            - df.loc[missing_discount, "price"]
        )
        / df.loc[missing_discount, "listed_price"]
        * 100
    ).round(2)

    df["rating"] = df["rating_score"].apply(parse_rating)
    df["reviews"] = (
        pd.to_numeric(df["review_count"], errors="coerce").fillna(0).astype(int)
    )

    # Parse capacity from capacity column, fallback to title
    df["capacity_gb"] = df["capacity"].apply(parse_capacity)
    missing_cap = df["capacity_gb"].isna()
    df.loc[missing_cap, "capacity_gb"] = df.loc[missing_cap, "title"].apply(parse_capacity)

    df["crawled_at"] = pd.to_datetime(df["crawled_at"], utc=True)
    df["crawled_at"] = df["crawled_at"].dt.tz_convert("Asia/Ho_Chi_Minh")
    df["crawl_date"] = df["crawled_at"].dt.date
    df["product_name"] = df.apply(
        lambda row: format_product_name(row["title"], row["capacity_gb"]),
        axis=1,
    )
    return df


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        raise SystemExit(
            "Chua cau hinh MONGODB_URI. Hay dat bien moi truong nay "
            "voi MongoDB connection string roi chay lai."
        )

    with MongoClient(mongo_uri, serverSelectionTimeoutMS=10000) as client:
        client.admin.command("ping")
        documents = fetch_raw_documents(client, MONGO_DB, MONGO_COLLECTION)

    print("MongoDB ket noi thanh cong")
    print(f"Database: {MONGO_DB} | Collection(s): {MONGO_COLLECTION}")

    if not documents:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as output:
            output.write("[]\n")
        print("\nKhong co document nao trong collection.")
        return

    normalized = normalize(prepare_for_normalize(documents))
    normalized.to_json(
        OUTPUT_FILE,
        orient="records",
        force_ascii=False,
        indent=2,
        date_format="iso",
    )
    print(f"\nDa ghi {len(normalized)} ban ghi chuan hoa vao: {OUTPUT_FILE}")

    sample_columns = [
        "product_name",
        "price",
        "listed_price",
        "discount_pct",
        "rating",
        "reviews",
        "store",
        "capacity_gb",
        "url",
    ]
    print("\n3.1 - 5 ban ghi mau sau khi chuan hoa:")
    print(normalized[sample_columns].head(5).to_string(index=False))

    print("\n3.2 - Thong ke:")
    print(f"Tong so ban ghi: {len(documents)}")
    print(f"So thieu gia: {int(normalized['price'].isna().sum())}")
    print(f"So co rating: {int(normalized['rating'].notna().sum())}")
    print(f"So san khac nhau: {normalized['store'].nunique()}")
    print("\nPhan bo theo san:")
    print(normalized["store"].value_counts().to_string())


if __name__ == "__main__":
    main()
