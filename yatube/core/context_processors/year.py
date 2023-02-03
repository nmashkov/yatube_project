from datetime import datetime as dt


def year(request):
    """Добавляет переменную с текущим годом."""
    current_year = dt.now().year
    return {'year': current_year, }
