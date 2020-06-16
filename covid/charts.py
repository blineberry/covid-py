from datetime import datetime

class ChartSet():
    def __init__(self):
        self.charts = []

    def add_chart(self, chart):
        self.charts.append(chart)
    
    def get_max_cases(self):
        max_cases = 0

        for chart in self.charts:
            for datum in chart.data:
                if datum.seven_day_average_cases > max_cases:
                    max_cases = datum.seven_day_average_cases

        return max_cases
    
    def get_max_days(self):
        max_days = 0

        for chart in self.charts:
            l = len(chart.data) 
            if l > max_days:
                max_days = l
        
        return max_days

class Chart():
    def __init__(self, data, name=""):
        self.data = data
        self.name=name
        self.period_of_uncertainty = []
        self.svg_points = []
        self.svg_uncertain_points = []

    def get_data_subset(self, include_last_two_weeks=False):
        subset = []

        start = len(self.data)

        for index,datum in enumerate(self.data):
            if datum.seven_day_average_cases >= 30:
                start = index
                break
        if include_last_two_weeks:
            return self.data[start:]

        last_datum = self.data[-1]

        days_past = (datetime.now().date() - last_datum.date).days

        if days_past > 14:
            return self.data[start:]

        return self.data[start:days_past-14]

    def get_last_two_weeks(self):
        last_datum = self.data[-1]

        days_past = (datetime.now().date() - last_datum.date).days

        if days_past > 14:
            return []

        last_two_weeks = self.data[days_past - 15::]

        return last_two_weeks

    def get_svg_background(self):
        if len(self.data) <= 0:
            return "white"

        peak = 0

        for datum in self.data:
            peak = max(peak, datum.seven_day_average_cases)

        last_two_weeks = self.get_last_two_weeks()
        last_confident_datum = self.data[-len(last_two_weeks)]

        highest_uncertain_cases = 0

        for datum in last_two_weeks:
            highest_uncertain_cases = max(highest_uncertain_cases, datum.seven_day_average_cases)

        reference_cases = max(last_confident_datum.seven_day_average_cases, highest_uncertain_cases)

        if reference_cases < peak / 2:
            return "#BAE8BA"

        if reference_cases < peak * .75:
            return "#BAE0E8"

        if reference_cases < peak * .9:
            return "#F5CE8C"

        return "#E8BABA"