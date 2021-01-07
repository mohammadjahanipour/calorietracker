from ..models import CoachClient


def isCoach(request):
    """
    Returns True/False if request.user is part of any coach-client objects where coach=request.user
    """

    if request.user.is_authenticated:
        coach_client_exists = CoachClient.objects.filter(coach=request.user).exists()

        if coach_client_exists:
            return {"isCoach": True}

    return {"isCoach": False}
