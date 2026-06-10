import re
from decimal import Decimal, InvalidOperation

from .models import Product
from .morphology import normalize_text


PRICE_RE = re.compile(
    r"(?:до|за|дешевле|меньше|не дороже)?\s*(?P<price>\d[\d\s]{2,})(?:\s*(?:р|руб|рублей|₽))?",
    re.IGNORECASE,
)
STOP_WORDS = {"до", "за", "руб", "рублей", "р", "не", "дороже", "дешевле", "меньше"}


def search_products(query, limit=None):
    parsed = _parse_query(query)
    if not parsed["terms"] and parsed["max_price"] is None:
        return Product.objects.none()

    products = Product.objects.select_related("category__product_line").prefetch_related(
        "images",
        "specs__specification",
    )

    matched_products = []
    for product in products:
        if parsed["max_price"] is not None and product.final_price > parsed["max_price"]:
            continue

        haystack = _product_haystack(product)
        if parsed["terms"] and not all(term in haystack for term in parsed["terms"]):
            continue

        matched_products.append(product)

    matched_products.sort(key=lambda product: _rank_product(product, parsed), reverse=True)
    return matched_products[:limit] if limit else matched_products


def _parse_query(query):
    text = (query or "").strip()
    max_price = None
    price_match = PRICE_RE.search(text)
    if price_match:
        raw_price = re.sub(r"\s+", "", price_match.group("price"))
        try:
            max_price = Decimal(raw_price)
            text = (text[: price_match.start()] + " " + text[price_match.end() :]).strip()
        except (InvalidOperation, ValueError):
            pass

    normalized = normalize_text(text)
    terms = [
        term
        for term in re.findall(r"[a-zA-Zа-яА-ЯёЁ0-9]+", normalized.lower())
        if term not in STOP_WORDS
    ]
    return {"original": query or "", "terms": terms, "max_price": max_price}


def _product_haystack(product):
    specs = " ".join(
        f"{spec.specification.name} {spec.value}"
        for spec in product.specs.select_related("specification").all()
    )
    text = " ".join(
        [
            product.name,
            product.description or "",
            product.category.name,
            product.category.slug,
            product.category.product_line.name,
            specs,
        ]
    )
    return normalize_text(text).lower()


def _rank_product(product, parsed):
    normalized_name = normalize_text(product.name).lower()
    score = 0
    for term in parsed["terms"]:
        if term in normalized_name:
            score += 10
        else:
            score += 1
    return score
