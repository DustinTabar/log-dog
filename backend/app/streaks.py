from datetime import date, timedelta


# Each function takes any date and returns the first day of the interval it falls in.

def start_of_day(d: date) -> date:
    return d


def start_of_week(d: date) -> date:
    return d - timedelta(days=d.weekday())  # back up to Monday


def start_of_month(d: date) -> date:
    return d.replace(day=1)


def start_of_year(d: date) -> date:
    return d.replace(month=1, day=1)


# The one place intervals are defined. To add a new one, write a
# start_of_... function above and add a line here.
INTERVALS = {
    "day": start_of_day,
    "week": start_of_week,
    "month": start_of_month,
    "year": start_of_year,
}


def period_start(d: date, interval: str) -> date:
    return INTERVALS[interval](d)


def previous_period_start(start: date, interval: str) -> date:
    # Step back one day into the previous interval, then snap to its start.
    return period_start(start - timedelta(days=1), interval)


def calculate_stats(completion_dates: list[date], interval: str, today: date) -> tuple[int, int]:
    """Return (streak, period_count) for a task's completion dates."""
    current = period_start(today, interval)
    done_periods = {period_start(d, interval) for d in completion_dates}

    period_count = sum(1 for d in completion_dates if period_start(d, interval) == current)

    # Grace rule: if the current interval isn't done yet, count back from the previous one.
    p = current if current in done_periods else previous_period_start(current, interval)
    streak = 0
    while p in done_periods:
        streak += 1
        p = previous_period_start(p, interval)

    return streak, period_count