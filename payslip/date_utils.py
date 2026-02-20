from datetime import datetime

MONTH_YEAR_FORMAT = "%b-%Y"


def parse_month_year(value):
    try:
        return datetime.strptime(value, MONTH_YEAR_FORMAT)
    except (TypeError, ValueError):
        return None


def build_month_year_filters(period_values):
    parsed_periods = []
    for period in period_values:
        parsed = parse_month_year(period)
        if parsed:
            parsed_periods.append(parsed)

    sorted_periods = sorted(set(parsed_periods), reverse=True)

    month_options = []
    seen_months = set()
    for period in sorted_periods:
        month_name = period.strftime("%b")
        if month_name not in seen_months:
            seen_months.add(month_name)
            month_options.append(month_name)

    year_options = sorted({str(period.year) for period in sorted_periods}, reverse=True)
    return sorted_periods, month_options, year_options
