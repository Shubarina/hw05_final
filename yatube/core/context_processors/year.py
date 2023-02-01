from datetime import datetime


def year(request):
    today = datetime.now().year
    return {'year': today}
