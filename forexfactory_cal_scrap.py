from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta
from typing import List
import urllib.request
import urllib.parse
import ssl
from pytz import timezone
import time
from pprint import pprint
import threading as th
import logging
from time import sleep
import pandas as pd
from  dateutil import parser

class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.num = 0
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)
        print("done thread " + str(self.num))

    def start(self):
        if not self.is_running:
            self._timer = th.Timer(self.interval, self._run)
            self._timer.name = self.num
            print("thread id=" + self._timer.name)
            self._timer.start()
            self.is_running = True
            self.num = self.num + 1

    def stop(self):
        self._timer.cancel()
        self.is_running = False

class PyEcoCal:

    def is_date_parsing(self, date_str, time_str):
        try:
            return datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %I:%M%p')
            # return bool(parser.parse(date_str))
        except ValueError:
            return False
    
    def GetEconomicCalendar(self, query_date: datetime):

        base_url = "https://www.forexfactory.com/"

        ssl._create_default_https_context = ssl._create_unverified_context

        # ctx = ssl.create_default_context()
        # ctx.check_hostname = False
        # ctx.verify_mode = ssl.CERT_NONE

        # html = urllib.request.urlopen(url, context=ctx).read()

        # get the page and make the soup
        urleco = f"{base_url}calendar?day={query_date.strftime('%b').lower()}{query_date.day}.{query_date.year}"

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
            "ora": "medium",
            "yel": "low",
            "gra": "None"
        }
        
        for item in table:
            dict = {
                "Date": "",
                "Time": "",
                "Currency": "",
                "Event": "",
                "Impact": "",
                "Actual": "",
                "Pending": "",
                "Result": "",
                "Forecast": "",
                "Previous": "",
                "upnext": ""
            }

            # check_id = item,find_all("td", {"class": ""})

            # print(f"item = {item}")
            check_date = item.find_all("td", {"class": "calendar__cell"})
            if len(check_date) != 0:
                check_exact_date =  check_date[0].text.strip()
                if date_prev and not check_exact_date:
                    dict["Date"] = date_prev
                else:
                    dict["Date"] = check_exact_date
                date_prev = dict["Date"]
            
            check_time = item.find_all("td", {"class": "calendar__cell calendar__time"})
            if len(check_time) != 0:
                time_eastern = check_time[0].text.strip()
                datetime_eastern = self.is_date_parsing(date_string, time_eastern)
                if not time_eastern:
                    dict["Time"] = prev_time
                elif isinstance(datetime_eastern, datetime):
                    dict["Time"] = datetime_eastern
                    prev_time = dict["Time"]
                else:
                    dict["Time"] = time_eastern

            check_currency = item.find_all("td", {"class": "calendar__cell calendar__currency"})
            if len(check_currency) != 0:
                dict["Currency"] = check_currency[0].text.strip()  # Currency
            
            check_event= item.find_all("span", {"class": "calendar__event-title"})
            if len(check_event) != 0:
                dict["Event"] = check_event[0].text.strip()  # Event Name

            check_upnext = item.find_all('span', {"class": "icon icon--upnext"})
            if len(check_upnext) != 0:
                upnext_val = check_upnext[0]['class']
                if len(upnext_val) > 1:
                    dict["upnext"] = upnext_val[1]
            # print(f"check_upnext = {dict['upnext']} \n")

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

            check_pending =item.find_all("div", {"class": "calendar__actual-wait"})
            if len(check_pending) != 0:
                actual_value = check_pending[0].text.strip()
                dict["Pending"] = actual_value
            
            check_result = item.select("span.worse")
            if not check_result:
                check_result = item.select("span.better")
            if len(check_result) > 0:
                filter_result = check_result[0]["class"]
                if len(filter_result) == 1:
                    dict['Result'] = filter_result[0]

            check_forecast = item.find_all("td", {"class": "calendar__cell calendar__forecast"})
            if len(check_forecast) != 0:
                dict["Forecast"] = check_forecast[0].text.strip()

            check_previous = item.find_all("td", {"class": "calendar__cell calendar__previous"})
            if len(check_previous) != 0:
                dict["Previous"] = check_previous[0].text.strip()

            # check_snap = item.find_all("snap", {"class": "icon icon--upnext"})
            # if len(check_snap) != 0:
            #     dict["snap"] = check_snap[0].text.strip()
            

            eco_day.append(dict)

        events_array = []
        for row_dict in eco_day:
            if not row_dict["Time"]:
                continue

            events_array.append(
                {
                    "date": row_dict["Date"],
                    "time": row_dict["Time"],
                    "currency": row_dict["Currency"],
                    "importance": row_dict["Impact"],
                    "event": row_dict["Event"],
                    "actual": row_dict["Actual"],
                    "pending": row_dict["Pending"],
                    "result": row_dict["Result"],
                    "forecast": row_dict["Forecast"],
                    "previous": row_dict["Previous"],
                    "upnext": row_dict["upnext"]
                }
            )

        return pd.DataFrame(events_array)

def setLogger():
    logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - \n %(message)s',
                    filename='logs_file',
                    filemode='w')
    console = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - \n %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)


def run_main():
    tic = time.perf_counter()
    setLogger()
    eco = PyEcoCal()
    
    jsons = eco.GetEconomicCalendar(datetime.today() - timedelta(days=2))
    # data.head()
    logging.info(jsons.to_string())
    toc = time.perf_counter()
    print(f"Downloaded the tutorial in {toc - tic:0.4f} seconds")


if __name__ == "__main__":
    """
    Run this using the command "python `script_name`.py >> `output_name`.csv"
    """
    print("starting...")

    rt = RepeatedTimer(1, run_main) # it auto-starts, no need of rt.start()
    try:
        sleep(1000) # your long-running job goes here...
    finally:
        rt.stop() # better in a try/finally block to make sure the program ends!
