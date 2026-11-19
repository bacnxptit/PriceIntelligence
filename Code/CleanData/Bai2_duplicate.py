import os
import sys

import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient

from Bai1_normalize import (
    MONGO_COLLECTION,
    MONGO_DB,
    fetch_raw_documents,
    normalize,
    prepare_for_normalize,
)


load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """Keep the newest record for each store, SKU, and crawl date."""
    df = df.copy()
    df = df.sort_values(
        "crawled_at",
        ascending=False,
        na_position="last",
        kind="mergesort",
    )
    return df.drop_duplicates(
        subset=["store", "sku", "crawl_date"],
        keep="first",
    ).reset_index(drop=True)


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

    # Reuse Bai1's preparation and normalization; deduplicate that DataFrame.
    normalized_df = normalize(prepare_for_normalize(documents))
    deduplicated_df = deduplicate(normalized_df)

    before_count = len(normalized_df)
    after_count = len(deduplicated_df)
    removed_count = before_count - after_count
    reduction_percent = (
        removed_count / before_count * 100 if before_count else 0
    )

    print(f"Database: {MONGO_DB} | Collection: {MONGO_COLLECTION}")
    print(f"So ban ghi truoc khi dedup: {before_count}")
    print(f"So ban ghi sau khi dedup: {after_count}")
    print(
        f"So ban ghi bi loai (trung lap): {removed_count} "
        f"({reduction_percent:.2f}%)"
    )

    print("\nTop 10 SKU xuat hien nhieu nhat (truoc dedup):")
    sku_counts = normalized_df["sku"].value_counts(dropna=True).head(10)
    if sku_counts.empty:
        print("Khong co SKU de thong ke.")
    else:
        print(
            sku_counts.rename_axis("SKU")
            .reset_index(name="So lan")
            .to_string(index=False)
        )

    sample_columns = [
        column
        for column in ["product_name", "store", "sku", "price", "crawl_date"]
        if column in deduplicated_df.columns
    ]
    print("\n5 ban ghi mau sau dedup:")
    if deduplicated_df.empty:
        print("Khong co ban ghi.")
    else:
        print(deduplicated_df[sample_columns].head(5).to_string(index=False))


if __name__ == "__main__":
    main()
