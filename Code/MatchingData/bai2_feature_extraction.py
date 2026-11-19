import os
import re
import sys
import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

MONGO_URI = os.getenv("MONGODB_URI")
MONGO_DB_NAME = os.getenv("MONGODB_DB", "imdb")


def clean_model_name(title_or_cat: str) -> str:
    """
    Tach Model chuan hoa dang chu thuong (lowercase).
    VD: '18 pro max', '17e', 'air', 'duo', '16 plus', '15'
    """
    text = str(title_or_cat or "").strip().lower()
    # Loai bo cac ky tu dac biet nhu '-' hay '|'
    text = text.replace("-", " ").replace("|", " ")
    match = re.search(r"(?:iphone\s+)?([\w\s]+?)(?=\s+\d+(?:gb|tb)|$)", text)
    if match:
        model = match.group(1).strip()
    else:
        model = text

    model = re.sub(r"\biphone\b", "", model).strip()
    # Thu gon nhieu khoang trang
    model = re.sub(r"\s+", " ", model)
    return model if model else "unknown"


def clean_capacity_gb(val_str: str) -> int | None:
    """
    Chuyen doi moi dinh dang dung luong ('256 GB', '512gb', '1 TB') ve so nguyen GB.
    """
    if pd.isna(val_str) or not val_str:
        return None
    val_str = str(val_str).upper().strip()
    match = re.search(r"(\d+)\s*(GB|TB)", val_str)
    if match:
        num, unit = int(match.group(1)), match.group(2)
        return int(num * 1024 if unit == "TB" else num)
    return None


def extract_features_apple_store(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Trich chon dac trung chuan hoa rieng cho collection [apple_store]
    """
    df = df_raw.copy()

    # 1. Title goc
    title_col = "product_title" if "product_title" in df.columns else (
        "title" if "title" in df.columns else "name"
    )
    df["title_clean"] = df.get(title_col, pd.Series([""] * len(df)))

    # 2. Brand & Model
    df["brand"] = "apple"
    cat_series = df.get("category", pd.Series([None] * len(df)))
    df["model"] = cat_series.fillna(df["title_clean"]).apply(clean_model_name)

    # 3. Capacity (GB) - Dung combine_first de tranh loi dtype cua pandas 3.0+
    cap_col = df.get("capacity", pd.Series([None] * len(df))).apply(clean_capacity_gb)
    cap_title = df["title_clean"].apply(clean_capacity_gb)
    df["capacity_gb"] = cap_col.combine_first(cap_title).astype("Int64")

    # 4. Product Match Key
    df["product_match_key"] = (
        df["brand"] + "_" + df["model"] + "_" + df["capacity_gb"].astype(str)
    ).str.replace(r"\s+", "", regex=True)

    return df[["title_clean", "brand", "model", "capacity_gb", "product_match_key"]]


def extract_features_fptshop(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Trich chon dac trung chuan hoa rieng cho collection [fptshop]
    """
    df = df_raw.copy()

    # 1. Title goc
    title_col = "title" if "title" in df.columns else (
        "name" if "name" in df.columns else "product_title"
    )
    df["title_clean"] = df.get(title_col, pd.Series([""] * len(df)))

    # 2. Brand & Model
    df["brand"] = "apple"
    df["model"] = df["title_clean"].apply(clean_model_name)

    # 3. Capacity (GB) - Dung combine_first de tranh loi dtype cua pandas 3.0+
    cap_col = df.get("capacity", pd.Series([None] * len(df))).apply(clean_capacity_gb)
    cap_title = df["title_clean"].apply(clean_capacity_gb)
    df["capacity_gb"] = cap_col.combine_first(cap_title).astype("Int64")

    # 4. Product Match Key
    df["product_match_key"] = (
        df["brand"] + "_" + df["model"] + "_" + df["capacity_gb"].astype(str)
    ).str.replace(r"\s+", "", regex=True)

    return df[["title_clean", "brand", "model", "capacity_gb", "product_match_key"]]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if not MONGO_URI:
        raise SystemExit("Chua cau hinh MONGODB_URI trong .env!")

    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
    db = client[MONGO_DB_NAME]

    apple_col_name = "iphone_applestore" if "iphone_applestore" in db.list_collection_names() else "apple_store"
    fpt_col_name = "iphone_fptshop" if "iphone_fptshop" in db.list_collection_names() else "fptshop"

    print("=" * 115)
    print("CHUONG TRINH TEST THU TRICH CHON DAC TRUNG (BRAND, MODEL, CAPACITY, PRODUCT_MATCH_KEY)")
    print("=" * 115)

    # TEST FPTSHOP
    docs_fpt = list(db[fpt_col_name].find({}))
    if docs_fpt:
        df_fpt_raw = pd.DataFrame(docs_fpt)
        df_fpt_test = extract_features_fptshop(df_fpt_raw)
        print(f"\nKET QUA TEST MAU COLLECTION [{fpt_col_name.upper()}] (10 BAN GHI DAU):")
        print("-" * 115)
        print(df_fpt_test.head(10).to_string(index=False))

    # TEST APPLE STORE
    docs_apple = list(db[apple_col_name].find({}))
    if docs_apple:
        df_apple_raw = pd.DataFrame(docs_apple)
        df_apple_test = extract_features_apple_store(df_apple_raw)
        print(f"\n\nKET QUA TEST MAU COLLECTION [{apple_col_name.upper()}] (10 BAN GHI DAU):")
        print("-" * 115)
        print(df_apple_test.head(10).to_string(index=False))

    print("\n" + "=" * 115)


if __name__ == "__main__":
    main()
