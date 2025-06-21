from celery import shared_task
from django.utils import timezone
from .models import Promotion
import logging

logger = logging.getLogger(__name__)


@shared_task
def deactivate_expired_promotions():
    """
    Находит все активные акции, у которых истек срок действия,
    и деактивирует их.
    """
    now = timezone.now()

    expired_promotions = Promotion.objects.filter(
        is_active=True,
        end_date__isnull=False,
        end_date__lt=now
    )

    count = expired_promotions.count()

    if count > 0:
        updated_count = expired_promotions.update(is_active=False)
        message = f"Successfully deactivated {updated_count} expired promotions."
        logger.info(message)
        return message

    message = "No expired promotions to deactivate."
    logger.info(message)
    return message
