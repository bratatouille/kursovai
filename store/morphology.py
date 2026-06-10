import inspect
import re
import warnings
from collections import namedtuple
from functools import lru_cache


CYRILLIC_RE = re.compile(r"[а-яё]", re.IGNORECASE)
TOKEN_RE = re.compile(r"[a-zA-Zа-яА-ЯёЁ0-9]+")


def _patch_pymorphy2_inspect():
    if hasattr(inspect, "getargspec"):
        return

    arg_spec = namedtuple("ArgSpec", "args varargs keywords defaults")

    def getargspec(func):
        spec = inspect.getfullargspec(func)
        return arg_spec(spec.args, spec.varargs, spec.varkw, spec.defaults)

    inspect.getargspec = getargspec


@lru_cache(maxsize=1)
def get_morph_analyzer():
    try:
        _patch_pymorphy2_inspect()
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="pkg_resources is deprecated.*")
            import pymorphy2

            return pymorphy2.MorphAnalyzer()
    except Exception:
        return None


@lru_cache(maxsize=20000)
def normalize_word(word):
    lowered = word.lower()
    if len(lowered) < 3 or not CYRILLIC_RE.search(lowered):
        return lowered

    morph = get_morph_analyzer()
    if not morph:
        return lowered

    parsed = morph.parse(lowered)
    return parsed[0].normal_form if parsed else lowered


def normalize_text(text):
    words = TOKEN_RE.findall(text or "")
    return " ".join(normalize_word(word) for word in words)


def enrich_text(text):
    normalized = normalize_text(text)
    if not normalized:
        return text or ""
    return f"{text or ''} {normalized}"
