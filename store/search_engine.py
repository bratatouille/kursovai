import re
import shutil
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.db.models import Q

from whoosh import index
from whoosh.analysis import CharsetFilter, LowercaseFilter, RegexTokenizer
from whoosh.fields import ID, NUMERIC, Schema, TEXT
from whoosh.qparser import FuzzyTermPlugin, MultifieldParser, OrGroup
from whoosh.support.charset import accent_map

from .morphology import enrich_text, normalize_text
from .models import Product


INDEX_DIR = Path(settings.BASE_DIR) / "whoosh_index"

CATEGORY_SYNONYMS = {
    "motherboard": ["материнская плата", "материнская", "материнка", "motherboard", "mainboard"],
    "videokarta": ["видеокарта", "видеокарты", "видео карта", "видео-карта", "графическая карта", "gpu"],
    "processor": ["процессор", "cpu", "ryzen", "core i"],
    "storage": ["ssd", "hdd", "накопитель", "жесткий диск", "диск"],
    "ram": ["оперативная память", "оперативка", "ram", "ddr4", "ddr5"],
    "psu": ["блок питания", "бп", "psu"],
    "case": ["корпус", "case"],
    "cooling": ["охлаждение", "кулер", "cooler"],
    "monitory": ["монитор", "мониторы", "display", "screen", "экран"],
    "klaviatury": ["клавиатура", "клавиатуры", "keyboard"],
    "myshi": ["мышь", "мыши", "mouse"],
    "rgb-lenty": ["rgb лента", "rgb ленты", "ргб лента", "подсветка", "лента"],
}

BRAND_SYNONYMS = {
    "amd": ["amd", "radeon", "ryzen"],
    "nvidia": ["nvidia", "geforce"],
    "intel": ["intel"],
}

MODEL_FAMILY_TERMS = ["rtx", "gtx", "gt", "rx", "arc"]

MARKED_PRICE_RE = re.compile(
    r"(?:до|за|дешевле|меньше|не дороже|до\s*цены)\s*"
    r"(?P<price>\d[\d\s]{2,})(?:\s*(?:р|руб|рублей|₽))?",
    re.IGNORECASE,
)
CURRENCY_PRICE_RE = re.compile(r"(?P<price>\d[\d\s]{2,})\s*(?:р|руб|рублей|₽)", re.IGNORECASE)


def _analyzer():
    return RegexTokenizer() | LowercaseFilter() | CharsetFilter(accent_map)


def get_schema():
    return Schema(
        product_id=ID(stored=True, unique=True),
        name=TEXT(stored=True, analyzer=_analyzer(), field_boost=3.0),
        description=TEXT(stored=True, analyzer=_analyzer()),
        category=TEXT(stored=True, analyzer=_analyzer(), field_boost=2.0),
        category_slug=ID(stored=True),
        product_line=TEXT(stored=True, analyzer=_analyzer()),
        specs=TEXT(stored=True, analyzer=_analyzer()),
        price=NUMERIC(stored=True, decimal_places=2),
    )


def get_index(create=False, clean=False):
    if clean and INDEX_DIR.exists():
        shutil.rmtree(INDEX_DIR)
    INDEX_DIR.mkdir(exist_ok=True)
    if index.exists_in(str(INDEX_DIR)):
        return index.open_dir(str(INDEX_DIR))
    if create:
        return index.create_in(str(INDEX_DIR), get_schema())
    return None


def parse_smart_query(query):
    original = (query or "").strip()
    parsed = {
        "original": original,
        "text": original,
        "max_price": None,
        "category_terms": [],
        "category_slugs": [],
        "brand_terms": [],
    }
    match = MARKED_PRICE_RE.search(original) or CURRENCY_PRICE_RE.search(original)
    if match:
        raw_price = re.sub(r"\s+", "", match.group("price"))
        try:
            parsed["max_price"] = Decimal(raw_price)
            parsed["text"] = (original[: match.start()] + " " + original[match.end() :]).strip()
        except (InvalidOperation, ValueError):
            pass

    lowered = original.lower()
    for slug, terms in CATEGORY_SYNONYMS.items():
        matched_terms = [term for term in terms if term in lowered]
        if matched_terms:
            parsed["category_terms"].extend(matched_terms)
            parsed["category_slugs"].append(slug)

    parsed["brand_terms"].extend(_extract_brand_terms(lowered))
    if any(re.search(rf"\b{re.escape(term)}\b", lowered) for term in MODEL_FAMILY_TERMS):
        if "videokarta" not in parsed["category_slugs"]:
            parsed["category_slugs"].append("videokarta")

    if not parsed["text"] and parsed["category_terms"]:
        parsed["text"] = " ".join(parsed["category_terms"][:2])

    return parsed


def build_product_document(product):
    specs = " ".join(
        f"{spec.specification.name} {spec.value}"
        for spec in product.specs.select_related("specification").all()
    )
    return {
        "product_id": str(product.id),
        "name": enrich_text(product.name),
        "description": enrich_text(product.description or ""),
        "category": enrich_text(product.category.name),
        "category_slug": product.category.slug,
        "product_line": enrich_text(product.category.product_line.name),
        "specs": enrich_text(specs),
        "price": product.final_price,
    }


def rebuild_index():
    ix = get_index(create=True, clean=True)
    writer = ix.writer()
    products = Product.objects.select_related("category__product_line").prefetch_related("specs__specification")
    count = 0
    for product in products:
        writer.update_document(**build_product_document(product))
        count += 1
    writer.commit()
    return count


def update_product_index(product):
    ix = get_index(create=True)
    writer = ix.writer()
    writer.update_document(**build_product_document(product))
    writer.commit()


def delete_product_from_index(product_id):
    ix = get_index()
    if not ix:
        return
    writer = ix.writer()
    writer.delete_by_term("product_id", str(product_id))
    writer.commit()


def search_product_ids(query, limit=None):
    parsed = parse_smart_query(query)
    if _is_category_only_query(parsed):
        qs = Product.objects.filter(category__slug__in=parsed["category_slugs"]).order_by("-id")
        if parsed["max_price"] is not None:
            product_ids = [product.id for product in qs if product.final_price <= parsed["max_price"]]
            return product_ids[:limit] if limit else product_ids
        if limit:
            qs = qs[:limit]
        return list(qs.values_list("id", flat=True))

    haystack_product_ids = _search_product_ids_with_haystack(parsed, limit)
    if haystack_product_ids is not None:
        haystack_product_ids = _apply_structured_filters(haystack_product_ids, parsed)
        haystack_product_ids = _rank_product_ids(haystack_product_ids, parsed)
        return haystack_product_ids[:limit] if limit else haystack_product_ids

    ix = get_index()
    if not ix:
        qs = _fallback_queryset(parsed)
        if limit:
            qs = qs[:limit]
        return list(qs.values_list("id", flat=True))

    search_text = _build_search_text(parsed)
    if not search_text:
        qs = _fallback_queryset(parsed)
        if limit:
            qs = qs[:limit]
        return list(qs.values_list("id", flat=True))

    parser = MultifieldParser(
        ["name", "description", "category", "product_line", "specs"],
        schema=ix.schema,
        group=OrGroup.factory(0.8),
    )
    parser.add_plugin(FuzzyTermPlugin())
    whoosh_query = parser.parse(search_text)
    search_limit = limit
    if limit and (parsed["max_price"] is not None or parsed["category_slugs"] or parsed["brand_terms"]):
        search_limit = limit * 5

    with ix.searcher() as searcher:
        results = searcher.search(whoosh_query, limit=search_limit or None)
        product_ids = [int(result["product_id"]) for result in results]
        if not product_ids or (limit and len(product_ids) < limit):
            fuzzy_query = parser.parse(_make_fuzzy_query(search_text))
            results = searcher.search(fuzzy_query, limit=search_limit or None)
            fuzzy_product_ids = [int(result["product_id"]) for result in results]
            product_ids = list(dict.fromkeys([*product_ids, *fuzzy_product_ids]))

    product_ids = _apply_structured_filters(product_ids, parsed)
    product_ids = _rank_product_ids(product_ids, parsed)
    return product_ids[:limit] if limit else product_ids


def _search_product_ids_with_haystack(parsed, limit=None):
    if not (Path(settings.BASE_DIR) / "haystack_index").exists():
        return None

    try:
        from haystack.query import SearchQuerySet
    except Exception:
        return None

    search_text = _build_search_text(parsed)
    if not search_text:
        return None

    try:
        search_limit = limit
        if limit and (parsed["max_price"] is not None or parsed["category_slugs"] or parsed["brand_terms"]):
            search_limit = limit * 5
        results = SearchQuerySet().models(Product).auto_query(search_text)
        if search_limit:
            results = results[:search_limit]
        product_ids = [int(result.pk) for result in results if result.pk]
        return product_ids or None
    except Exception:
        return None


def search_products(query, limit=None):
    product_ids = search_product_ids(query, limit=limit)
    if not product_ids:
        return Product.objects.none()
    preserved_order = {product_id: position for position, product_id in enumerate(product_ids)}
    products = list(
        Product.objects.filter(id__in=product_ids)
        .select_related("category__product_line")
        .prefetch_related("images")
    )
    products.sort(key=lambda product: preserved_order[product.id])
    return products


def _build_search_text(parsed):
    raw_text = " ".join([parsed["text"], *parsed["category_terms"]]).strip()
    normalized_text = normalize_text(raw_text)
    return " ".join([raw_text, normalized_text]).strip()


def _is_category_only_query(parsed):
    return bool(parsed["category_slugs"]) and not parsed["brand_terms"] and not _meaningful_query_terms(parsed)


def _extract_brand_terms(lowered_query):
    terms = []
    for canonical, synonyms in BRAND_SYNONYMS.items():
        if canonical in lowered_query:
            terms.extend(synonyms)
            continue
        terms.extend(term for term in synonyms if term in lowered_query)

    for term in MODEL_FAMILY_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", lowered_query):
            terms.append(term)

    return list(dict.fromkeys(terms))


def _apply_structured_filters(product_ids, parsed):
    if not product_ids:
        return []
    products_by_id = Product.objects.select_related("category").in_bulk(product_ids)
    filtered_ids = []
    for product_id in product_ids:
        product = products_by_id.get(product_id)
        if not product:
            continue
        if parsed["category_slugs"] and product.category.slug not in parsed["category_slugs"]:
            continue
        if parsed["brand_terms"] and not _product_matches_terms(product, parsed["brand_terms"]):
            continue
        if parsed["max_price"] is not None and product.final_price > parsed["max_price"]:
            continue
        filtered_ids.append(product_id)
    return filtered_ids


def _rank_product_ids(product_ids, parsed):
    if not product_ids:
        return []
    products_by_id = Product.objects.select_related("category__product_line").prefetch_related(
        "specs__specification"
    ).in_bulk(product_ids)
    query_terms = _meaningful_query_terms(parsed)
    query_phrase = " ".join(query_terms)

    def rank(product_id):
        product = products_by_id.get(product_id)
        if not product:
            return (-1, -1)
        name = product.name.lower()
        haystack = _product_haystack(product)
        score = 0

        if query_phrase and query_phrase in name:
            score += 120
        elif query_phrase and query_phrase in haystack:
            score += 80

        if query_terms:
            name_matches = sum(1 for term in query_terms if term in name)
            total_matches = sum(1 for term in query_terms if term in haystack)
            score += name_matches * 25
            score += total_matches * 10
            if total_matches == len(query_terms):
                score += 60
            if name_matches == len(query_terms):
                score += 80

        numeric_terms = [term for term in query_terms if term.isdigit()]
        if numeric_terms and all(term in name for term in numeric_terms):
            score += 70

        return (score, -product_id)

    return sorted(product_ids, key=rank, reverse=True)


def _meaningful_query_terms(parsed):
    text = parsed["text"] or parsed["original"]
    terms = [term.lower() for term in re.findall(r"[a-zA-Zа-яА-ЯёЁ0-9]+", text)]
    category_terms = {
        part.lower()
        for phrase in parsed["category_terms"]
        for part in re.findall(r"[a-zA-Zа-яА-ЯёЁ0-9]+", phrase)
    }
    stop_words = category_terms | {"до", "за", "руб", "рублей", "р"}
    return [term for term in terms if term not in stop_words]


def _make_fuzzy_query(search_text):
    terms = [term for term in re.split(r"\s+", search_text.strip()) if len(term) > 3]
    return " ".join(f"{term}~1" for term in terms) or search_text


def _product_matches_terms(product, terms):
    return any(term.lower() in _product_haystack(product) for term in terms)


def _product_haystack(product):
    haystack_parts = [
        product.name,
        product.description or "",
        product.category.name,
        product.category.product_line.name,
    ]
    haystack_parts.extend(
        f"{spec.specification.name} {spec.value}"
        for spec in product.specs.select_related("specification").all()
    )
    return " ".join(haystack_parts).lower()


def _fallback_queryset(parsed):
    query = parsed["text"] or parsed["original"]
    products = Product.objects.select_related("category__product_line").prefetch_related("images")
    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(specs__value__icontains=query)
            | Q(category__name__icontains=query)
            | Q(category__product_line__name__icontains=query)
        ).distinct()
    if parsed["category_slugs"]:
        products = products.filter(category__slug__in=parsed["category_slugs"]).distinct()
    if parsed["brand_terms"]:
        product_ids = [product.id for product in products if _product_matches_terms(product, parsed["brand_terms"])]
        products = products.filter(id__in=product_ids)
    if parsed["max_price"] is not None:
        product_ids = [product.id for product in products if product.final_price <= parsed["max_price"]]
        products = products.filter(id__in=product_ids)
    return products.order_by("-id")
