
from actstream.models import target_stream

def notifications_count(request):
    """
    Returns the amount of notifications for where the user is a target
    """


    if request.user.is_authenticated:
        notifications = target_stream(request.user)
        return {"notifications_count": len(notifications)}

    else:
        return {"notifications": None}



def notifications(request):
    """
    Returns all Notifications for a user
    specifically returns all where user is the target
    """

    if request.user.is_authenticated:
        notifications = target_stream(request.user)
        return {"notifications": notifications}
    else:
        return {"notifications": None}
