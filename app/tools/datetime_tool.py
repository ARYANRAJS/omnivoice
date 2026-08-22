from datetime import datetime

def get_current_time() -> str:
    now = datetime.now()
    return f"The current time is {now.strftime('%I:%M %p')}."

def get_current_date() -> str:
    now = datetime.now()
    return f"Today's date is {now.strftime('%A, %B %d, %Y')}."

def get_datetime_info(query: str) -> str:
    q = query.lower()
    if "time" in q:
        return get_current_time()
    if "date" in q or "today" in q or "day" in q:
        return get_current_date()
    return f"{get_current_time()} {get_current_date()}"
