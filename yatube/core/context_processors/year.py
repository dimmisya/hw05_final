from datetime import date


def year(request):
    return {'year': int(date.today().strftime("%Y"))}
