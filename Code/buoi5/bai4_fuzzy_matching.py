import re
import sys
from difflib import SequenceMatcher

# =============================================================
# 1. CAC HAM THUAT TOAN SO KHOP CHUOI (SIMILARITY METRICS)
# =============================================================

def levenshtein_similarity(str1: str, str2: str) -> float:
    """
    1. SequenceMatcher (dua tren Levenshtein):
    Do do tuong dong chuoi theo ty le ky tu khop (0.0 -> 1.0).
    """
    return round(
        SequenceMatcher(None, str1.lower(), str2.lower()).ratio(),
        4,
    )


def jaccard_similarity(str1: str, str2: str) -> float:
    """
    2. Jaccard Similarity (Token-based):
    Tach chuoi thanh tap hop cac tu (Tokens) va do do giao nhau
    J(A, B) = |A giao B| / |A hop B|.
    """
    words1 = set(re.findall(r"\w+", str1.lower()))
    words2 = set(re.findall(r"\w+", str2.lower()))
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    if not union:
        return 0.0
    return round(len(intersection) / len(union), 4)


def token_sort_similarity(str1: str, str2: str) -> float:
    """
    3. Token Sort Ratio:
    Sap xep cac tu theo thu tu bang chu cai truoc khi so sanh.
    Giup xu ly truong hop cung tu nhung khac vi tri.
    """
    words1 = " ".join(sorted(re.findall(r"\w+", str1.lower())))
    words2 = " ".join(sorted(re.findall(r"\w+", str2.lower())))
    return levenshtein_similarity(words1, words2)


# =============================================================
# 2. QUY TRINH TIEN XU LY DU LIEU (PREPROCESSING)
# =============================================================

SYNONYMS = {
    r"\bip\b": "iphone",
    r"\bprm\b": "pro max",
    r"\bpromax\b": "pro max",
    r"\bvna\b": "",
    r"\bvn/a\b": "",
}

STOPWORDS = [
    "dien thoai",
    "chinh hang",
    "gia re",
    "moi fullbox",
    "tra gop 0%",
    "tra gop",
    "mau titan",
    "mau",
]


def preprocess_text(text: str) -> str:
    """
    Tien xu ly: Dong nhat tu viet tat va loai bo tu rac.
    """
    clean_str = text.lower().strip()

    # 1. Synonym mapping
    for pattern, replacement in SYNONYMS.items():
        clean_str = re.sub(pattern, replacement, clean_str)

    # 2. Stopwords removal
    for stopword in STOPWORDS:
        clean_str = clean_str.replace(stopword, "")

    # 3. Chuan hoa khoang trang
    clean_str = re.sub(r"\s+", " ", clean_str).strip()
    return clean_str


def hard_filter_check(str1: str, str2: str) -> bool:
    """
    Kiem tra loc cung (Hard Filter):
    Kiem tra xem ca 2 chuoi co khop ve model dac biet (Pro Max vs Pro, Plus, v.v.)
    va dung luong (capacity) hay khong.
    """
    s1 = str1.lower()
    s2 = str2.lower()

    # Kiem tra Pro Max vs Pro (tranh truong hop Pro bi nham sang Pro Max)
    has_prm1 = "pro max" in s1 or "prm" in s1
    has_prm2 = "pro max" in s2 or "prm" in s2
    if has_prm1 != has_prm2:
        return False

    has_plus1 = "plus" in s1
    has_plus2 = "plus" in s2
    if has_plus1 != has_plus2:
        return False

    # Kiem tra capacity neu ca 2 deu co ghi dung luong
    cap1 = re.findall(r"\b(\d+)\s*(?:gb|tb)\b", s1)
    cap2 = re.findall(r"\b(\d+)\s*(?:gb|tb)\b", s2)
    if cap1 and cap2 and set(cap1) != set(cap2):
        return False

    return True


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    test_pairs = [
        {
            "case": "Cap 1: Viet tat & Tu rac (Shopee vs FPT)",
            "title_a": "iPhone 15 Pro Max 256GB VN/A",
            "title_b": "Ip 15 prm 256GB chinh hang vna gia re",
        },
        {
            "case": "Cap 2: Khac tu lot & Tieu de dai",
            "title_a": "Apple iPhone 16 Plus 128GB Xanh",
            "title_b": "Dien thoai iPhone 16 Plus 128GB Moi Fullbox Apple",
        },
        {
            "case": "Cap 3: Hai san pham KHAC NHAU hoan toan",
            "title_a": "iPhone 15 Pro Max 256GB",
            "title_b": "iPhone 15 Pro 256GB",
        },
    ]

    THRESHOLD = 0.75  # Nguong quyet dinh co khop san pham hay khong

    print("=" * 110)
    print("THU NGHIEM CAC THUAT TOAN SO KHOP CHUOI (FUZZY MATCHING DEMO - BAI 5)")
    print("=" * 110)

    for item in test_pairs:
        a = item["title_a"]
        b = item["title_b"]

        # So sanh truc tiep
        lev_score = levenshtein_similarity(a, b)
        jac_score = jaccard_similarity(a, b)
        tok_score = token_sort_similarity(a, b)

        # So sanh sau tien xu ly
        a_clean = preprocess_text(a)
        b_clean = preprocess_text(b)
        tok_clean_score = token_sort_similarity(a_clean, b_clean)

        hard_ok = hard_filter_check(a, b)
        is_match = (tok_clean_score >= THRESHOLD) and hard_ok

        print(f"\n{item['case']}")
        print(f" - Chuoi A          : '{a}'")
        print(f" - Chuoi B          : '{b}'")
        print(f" - Chuoi A sau clean: '{a_clean}'")
        print(f" - Chuoi B sau clean: '{b_clean}'")
        print(f" {'-' * 50}")
        print(f" Diem so tuong dong goc:")
        print(f"   1. Levenshtein (Ky tu) : {lev_score * 100:.1f}%")
        print(f"   2. Jaccard (Tap hop tu): {jac_score * 100:.1f}%")
        print(f"   3. Token Sort (Da xep) : {tok_score * 100:.1f}%")
        print(f" Diem sau Preprocessing (Token Sort): {tok_clean_score * 100:.1f}%")
        print(f" Hard Filter (Loc cung model/capacity): {'DAT' if hard_ok else 'KHONG DAT (Khac Model/Cap)'}")
        print(f" KET LUAN SO KHOP (Threshold >= {THRESHOLD} & Hard Filter): "
              f"{'KHOP (SAME PRODUCT)' if is_match else 'KHONG KHOP'}")

    print("\n" + "=" * 110)


if __name__ == "__main__":
    main()
