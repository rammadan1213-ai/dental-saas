from django.core.cache import cache


def get_unread_count(user):
    try:
        from notifications.models import Notification

        cache_key = f"notifications_count_{user.id}"
        count = cache.get(cache_key)
        if count is None:
            count = Notification.objects.filter(user=user, is_read=False).count()
            cache.set(cache_key, count, 300)
        return count
    except:
        return 0


def notifications_count(request):
    if request.user.is_authenticated:
        return {"unread_notifications_count": get_unread_count(request.user)}
    return {"unread_notifications_count": 0}
