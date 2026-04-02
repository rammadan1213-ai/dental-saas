from django.core.cache import cache


def notifications_count(request):
    if request.user.is_authenticated:
        try:
            from notifications.models import Notification

            cache_key = f"notifications_count_{request.user.id}"
            count = cache.get(cache_key)
            if count is None:
                count = Notification.objects.filter(
                    user=request.user, is_read=False
                ).count()
                cache.set(cache_key, count, 300)
            return {"unread_notifications_count": count}
        except:
            return {"unread_notifications_count": 0}
    return {"unread_notifications_count": 0}
