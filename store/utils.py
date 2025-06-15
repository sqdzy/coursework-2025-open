from django.utils import timezone
from django.db.models import OuterRef, Subquery, DecimalField, Min, Q, Value, Case, When, F, Prefetch
from django.db.models.functions import Coalesce

from .models import PromotionalProduct


def annotate_product_prices(queryset):
    """Добавляет аннотации actual_price и current_promotional_price к Product queryset."""
    now = timezone.now()

    active_promo_price_subquery = PromotionalProduct.objects.filter(
        product_id=OuterRef('pk'),
        promotion__is_active=True,
        promotion__start_date__lte=now,
        promotion__end_date__gte=now
    ).order_by('promotional_price').values('promotional_price')[:1]

    return queryset.annotate(
        current_promotional_price=Subquery(
            active_promo_price_subquery,
            output_field=DecimalField(max_digits=12, decimal_places=2)
        ),
        actual_price=Coalesce(
            Case(
                When(current_promotional_price__isnull=False, current_promotional_price__lt=F('price'),
                     then=F('current_promotional_price')),
                default=F('price'),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            ),
            F('price'),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        )
    )
