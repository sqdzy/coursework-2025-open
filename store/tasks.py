from decimal import Decimal

from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Promotion, Order
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


@shared_task
def send_order_confirmation_email(order_id: int, total_amount_str: str):
    """
    Отправляет email-уведомление пользователю после успешного создания заказа.
    Принимает ID заказа и его итоговую сумму в виде строки.
    """
    try:
        order = Order.objects.select_related(
            'user', 'status', 'payment', 'delivery_method'
        ).prefetch_related(
            'items__product'
        ).get(pk=order_id)
    except Order.DoesNotExist:
        logger.warning(f"Order with ID {order_id} does not exist. Cannot send email.")
        return f"Order {order_id} not found."

    user = order.user
    if not user.email:
        logger.info(f"User {user.username} has no email address. Skipping email for order #{order.id}.")
        return f"User {user.username} has no email."

    subject = f"Ваш заказ #{order.id} в GameGear успешно оформлен!"

    context = {
        'user': user,
        'order': order,
        'calculated_total': Decimal(total_amount_str),
        'site_url': 'https://gg.familycore.ru'
    }

    html_message = render_to_string('emails/order_confirmation.html', context)
    plain_message = render_to_string('emails/order_confirmation.txt', context)

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Successfully sent order confirmation email for order #{order.id} to {user.email}")
        return f"Email sent for order {order.id}."
    except Exception as e:
        logger.error(f"Failed to send order confirmation email for order #{order.id}: {e}")
        raise