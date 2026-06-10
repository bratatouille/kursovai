from haystack import indexes

from .morphology import enrich_text
from .models import Product


class ProductIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True)
    name = indexes.CharField(model_attr='name', boost=1.5)
    description = indexes.CharField(model_attr='description', null=True)
    category = indexes.CharField(model_attr='category__name')
    category_slug = indexes.CharField(model_attr='category__slug', indexed=False)
    product_line = indexes.CharField(model_attr='category__product_line__name')
    price = indexes.DecimalField(null=True)

    def get_model(self):
        return Product

    def index_queryset(self, using=None):
        return self.get_model().objects.select_related('category__product_line').prefetch_related('specs__specification')

    def prepare_price(self, obj):
        return obj.final_price

    def prepare_text(self, obj):
        specs = ' '.join(
            f'{spec.specification.name} {spec.value}'
            for spec in obj.specs.select_related('specification').all()
        )
        return enrich_text(' '.join([
            obj.name,
            obj.description or '',
            obj.category.name,
            obj.category.slug,
            obj.category.product_line.name,
            specs,
        ]))
