from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta
from typing import List
import urllib.request
import urllib.parse
import ssl
import json
from json import JSONEncoder
from pytz import timezone
import time

class PyEcoElement(object):
    def __init__(self, date: str, currency: str, event: str, impact : str, time_utc: str, actual: str, forecast: str, previous: str):
        self.date = date
        self.currency = currency
        self.event = event
        self.impact = impact
        self.time_utc = time_utc
        self.actual = actual
        self.forecast = forecast
        self.previous = previous

class PyEcoRoot(object):
    def __init__(self, eco_elements : List[PyEcoElement]):
        self.eco_elements = eco_elements

class PyEcoCal:
    def GetEconomicCalendar(self, query_date: datetime):

        base_url = "https://www.forexfactory.com/"

        ssl._create_default_https_context = ssl._create_unverified_context

        # ctx = ssl.create_default_context()
        # ctx.check_hostname = False
        # ctx.verify_mode = ssl.CERT_NONE

        # html = urllib.request.urlopen(url, context=ctx).read()

        # get the page and make the soup
        urleco = f"{base_url}calendar?day={query_date.strftime('%b').lower()}{query_date.day}.{query_date.year}"
        print(f"urleco={urleco}")
        # urleco = "https://www.forexfactory.com/calendar?day=sep1.2023"
        date_string = query_date.strftime('%Y-%m-%d')
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        response = opener.open(urleco)
        result = response.read().decode('utf-8', errors='replace')
        soup = BeautifulSoup(result, "html.parser")
        table = soup.find_all("tr", class_="calendar__row")
        eco_day = []
        date_prev = ""
        prev_time = ""

        impact_dict = {
            "red": "high",
            "ora": "mid",
            "yel": "low",
            "gra": "holiday"
        }
        
        for item in table:
            dict = {
                "Date": "",
                "Currency": "",
                "Event": "",
                "Time_UTC": "",
                "Impact": "",
                "Actual": "",
                "Forecast": "",
                "Previous": ""
            }

            check_date = item.find_all("td", {"class": "calendar__cell"})
            if len(check_date) != 0:
                check_exact_date =  check_date[0].text.strip()
                if date_prev and not check_exact_date:
                    dict["Date"] = date_prev
                else:
                    dict["Date"] = check_exact_date
                date_prev = dict["Date"]
            
            check_currency = item.find_all("td", {"class": "calendar__cell calendar__currency"})
            if len(check_currency) != 0:
                dict["Currency"] = check_currency[0].text.strip()  # Currency
            
            check_event= item.find_all("span", {"class": "calendar__event-title"})
            if len(check_event) != 0:
                dict["Event"] = check_event[0].text.strip()  # Event Name
            
            check_time = item.find_all("td", {"class": "calendar__cell calendar__time"})
            if len(check_time) != 0:
                time_eastern = check_time[0].text.strip()
                if time_eastern == "All Day" or time_eastern == "Tentative":
                    dict["Time_UTC"] = time_eastern
                elif time_eastern == "":
                    dict["Time_UTC"] = prev_time
                else:
                    datetime_eastern = datetime.strptime(f"{date_string} {time_eastern}", '%Y-%m-%d %I:%M%p')
                    eastern_tz = timezone('US/Eastern')
                    dict["Time_UTC"] = eastern_tz.localize(datetime(datetime_eastern.year, datetime_eastern.month, \
                                                                datetime_eastern.day, datetime_eastern.hour, \
                                                                datetime_eastern.minute, 0)).strftime("%Y%m%d %H:%M:%S")
                    prev_time = dict["Time_UTC"]

            check_impact = item.find_all("td", {"class": "calendar__cell calendar__impact"})
            if len(check_impact) != 0:
                for icon in range(0, len(check_impact)):
                    check_impact_class = check_impact[icon].find_all("span")
                    if len(check_impact_class) != 0:
                        impact_col = check_impact_class[0]['class'][1].split("-")[4]
                        if impact_col:
                            dict["Impact"] = impact_dict[impact_col]

            check_actual =item.find_all("td", {"class": "calendar__cell calendar__actual"})
            if len(check_actual) != 0:
                actual_value = check_actual[0].text.strip()
                if actual_value is None:
                    actual_value = check_actual[0].span.text.strip()
                dict["Actual"] = actual_value

            check_forecast = item.find_all("td", {"class": "calendar__cell calendar__forecast"})
            if len(check_forecast) != 0:
                dict["Forecast"] = check_forecast[0].text.strip()

            check_previous = item.find_all("td", {"class": "calendar__cell calendar__previous"})
            if len(check_previous) != 0:
                dict["Previous"] = check_previous[0].text.strip()

            eco_day.append(dict)

        events_array = []

        for row_dict in eco_day:
            eco_elem = PyEcoElement(
                row_dict["Date"],
                row_dict["Currency"],
                row_dict["Event"],
                row_dict["Impact"],
                row_dict["Time_UTC"],
                row_dict["Actual"],
                row_dict["Forecast"],
                row_dict["Previous"]
            )
            events_array.append(eco_elem)

        eco_cal = PyEcoRoot(events_array)

        json_object = json.dumps(eco_cal.__dict__, default=lambda o: o.__dict__, indent=3)
        return json_object

if __name__ == "__main__":
    """
    Run this using the command "python `script_name`.py >> `output_name`.csv"
    """
    tic = time.perf_counter()
    eco = PyEcoCal()
    
    json = eco.GetEconomicCalendar(datetime.today() + timedelta(days=2))
    print(json)

    toc = time.perf_counter()
    print(f"Downloaded the tutorial in {toc - tic:0.4f} seconds")