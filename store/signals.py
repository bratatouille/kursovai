from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Product, ProductSpec
from .search_engine import delete_product_from_index, update_product_index


@receiver(post_save, sender=Product)
def update_product_document(sender, instance, **kwargs):
    update_product_index(instance)


@receiver(post_delete, sender=Product)
def delete_product_document(sender, instance, **kwargs):
    delete_product_from_index(instance.id)


@receiver(post_save, sender=ProductSpec)
def update_product_document_specs(sender, instance, **kwargs):
    update_product_index(instance.product)


@receiver(post_delete, sender=ProductSpec)
def update_product_document_after_specs_delete(sender, instance, **kwargs):
    update_product_index(instance.product)
