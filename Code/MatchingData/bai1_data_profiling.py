import os
import sys
import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

MONGO_URI = os.getenv("MONGODB_URI")
MONGO_DB_NAME = os.getenv("MONGODB_DB", "imdb")


def profile_collection(df: pd.DataFrame, collection_name: str, target_fields: list[str]) -> None:
    """
    Ham in ra danh sach tat ca cac gia tri doc ban va so luong xuat hien cua tung gia tri.
    """
    print("\n" + "=" * 90)
    print(f"THONG KE CHI TIET COLLECTION: {collection_name.upper()} (Tong: {len(df)} ban ghi)")
    print("=" * 90)

    for field in target_fields:
        if field in df.columns:
            series = df[field].astype(str).str.strip()
            counts = series.value_counts(dropna=False)
            unique_vals = series.unique().tolist()

            print(f"\nCot [{field}]: Co {len(unique_vals)} gia tri khac nhau")
            print("-" * 65)
            print(f"{'Gia tri (Value)':<45} | {'So luong (Count)':<15}")
            print("-" * 65)
            for val, count in counts.items():
                display_val = "<None/NaN>" if val in ["nan", "None", "None/NaN"] else val
                print(f"{display_val:<45} | {count:<15}")
        else:
            print(f"\nCot [{field}]: Khong ton tai trong collection nay.")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if not MONGO_URI:
        raise SystemExit("Chua cau hinh MONGODB_URI trong .env!")

    print("Ket noi MongoDB Atlas...")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
    client.admin.command("ping")
    db = client[MONGO_DB_NAME]
    print(f"Ket noi thanh cong den Database: {MONGO_DB_NAME}")

    # Doc du lieu tho (ho tro ca ten co prefix 'iphone_' hoac khong)
    apple_col_name = "iphone_applestore" if "iphone_applestore" in db.list_collection_names() else "apple_store"
    fpt_col_name = "iphone_fptshop" if "iphone_fptshop" in db.list_collection_names() else "fptshop"

    docs_apple = list(db[apple_col_name].find({}))
    docs_fpt = list(db[fpt_col_name].find({}))

    df_apple = pd.DataFrame(docs_apple)
    df_fpt = pd.DataFrame(docs_fpt)

    # 1. Chay thong ke chi tiet cho Apple Store
    fields_apple = [
        col for col in ["category", "capacity", "colour", "color", "product_title", "title", "name"]
        if col in df_apple.columns
    ]
    profile_collection(df_apple, apple_col_name, fields_apple)

    # 2. Chay thong ke chi tiet cho FPT Shop
    title_col_fpt = "title" if "title" in df_fpt.columns else ("name" if "name" in df_fpt.columns else "product_title")
    fields_fpt = [
        col for col in [title_col_fpt, "capacity", "category", "rating_score", "colour", "color"]
        if col in df_fpt.columns
    ]
    profile_collection(df_fpt, fpt_col_name, fields_fpt)

    # 3. In tat ca tieu de mau de soi chuoi
    print("\n" + "=" * 90)
    print("TOAN BO DANH SACH TEN SAN PHAM (PRODUCT TITLES) DOC BAN")
    print("=" * 90)

    title_apple_col = "product_title" if "product_title" in df_apple.columns else (
        "title" if "title" in df_apple.columns else "name"
    )
    if title_apple_col in df_apple.columns:
        print(f"\n[APPLE STORE - Unique Titles ({len(df_apple[title_apple_col].dropna().unique())} mau)]")
        for idx, t in enumerate(df_apple[title_apple_col].dropna().unique()[:10], 1):
            print(f" {idx:2d}. {t}")

    if title_col_fpt in df_fpt.columns:
        print(f"\n[FPT SHOP - Unique Titles ({len(df_fpt[title_col_fpt].dropna().unique())} mau)]")
        for idx, t in enumerate(df_fpt[title_col_fpt].dropna().unique()[:10], 1):
            print(f" {idx:2d}. {t}")

    print("\n" + "=" * 90)


if __name__ == "__main__":
    main()
