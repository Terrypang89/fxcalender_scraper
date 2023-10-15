import datetime
import logging
import urllib.parse, urllib.request
import pandas as pd
import json
from bs4 import BeautifulSoup
import warnings

def setLogger():
    logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='logs_test_file',
                    filemode='w')
    console = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

def is_date_parsing(time_str, format_val):
    try:
        return datetime.datetime.strptime(f"{time_str}", format_val)
    except ValueError:
        return False

def last_day_of_month(date):
    if date.month == 12:
        return date.replace(day=31)
    return date.replace(month=date.month+1, day=1) - datetime.timedelta(days=1)


def getEconomicCalendar(
        default_view=None,
        impacts=None,
        currencies=None,
        event_types=None,
        begin_date=None,
        end_date=None,
        showDetails=False,
    ):

    valid_defaullt_views = [ "today", "tomorrow", "today_and_tomorrow", "yesterday", "this_week"]
    valid_impacts = [0,1,2,3]
    valid_currencies = [1,2,3,4,5,6,7,8,9]
    valid_event_types = [1,2,3,4,5,6,7,8,9,10,11]
    date_format_list = ['%b %d, %Y', '%B %d, %Y', '%b %-d, %Y', '%B %-d, %Y']
    # warnings.filterwarnings('ignore')
    if default_view is None:
        default_view = valid_defaullt_views[4]
        warnings.warn(f"the introduced default_view value is None, set to string {default_view}")
    elif  not isinstance(default_view, str):
        raise ValueError(
            "ERR#0001: the introduced default_view value is not valid since ince it must be a"
            " specific string, ."
        )
    else:
        if not any(valid_view == default_view for valid_view in valid_defaullt_views):
            raise ValueError(
                "ERR#0002: the introduced default_view value is not valid since ince it must be a"
                " string: today, tomorrow, today_and_tomorrow, yesterday, this_week, ."
            )
    
    if impacts is None:
        impacts = valid_impacts
        warnings.warn(f"the introduced impacts value is None, set to list of numbers {valid_impacts}")
    elif not isinstance(impacts, list):
        raise ValueError(
            "ERR#0101: the introduced impacts value is not valid since ince it must be a"
            " list of numbers unless it is None."
        )
    elif len(impacts) > 5:
        raise ValueError(
            "ERR#0102: the introduced impacts value is not valid since ince it must be a"
            " list of numbers less than 4 and list length less than 5 unless it is None."
        )
    else:
        for val in impacts:
            if not isinstance(val, (int, float, complex)) or not any(valid_impact == val for valid_impact in valid_impacts):
                    raise ValueError(
                    "ERR#0103: the introduced impacts value is not valid since ince it must be a"
                    " list of numbers with each value must less than 4 unless it is None."
                )

    if currencies is None:
        currencies = valid_currencies
        warnings.warn(f"the introduced currencies value is None, set to list of numbers {valid_currencies}")
    elif not isinstance(currencies, list):
        raise ValueError(
            "ERR#0201: the introduced currencies value is not valid since ince it must be a"
            " list of numbers unless it is None."
        )
    elif len(currencies) > 9:
        raise ValueError(
            "ERR#0202: the introduced currencies value is not valid since ince it must be a"
            " list of numbers length must less than 10 unless it is None."
        )
    else:
        for cur in currencies:
            if not isinstance(cur, (int, float, complex)) or not any(valid_cur == cur for valid_cur in valid_currencies):
                    raise ValueError(
                    "ERR#0203: the introduced currencies value is not valid since ince it must be a"
                    " list of numbers with each value must less than 10 unless it is None."
                )
                
    if event_types is None:
        event_types = valid_event_types
        warnings.warn(f"the introduced event_types value is None, set to list of numbers {valid_event_types}")
    elif not isinstance(event_types, list):
        raise ValueError(
            "ERR#0301: the introduced event_types value is not valid since ince it must be a"
            " list of numbers unless it is None."
        )
    elif len(event_types) > 11:
        raise ValueError(
            "ERR#0302: the introduced event_types value is not valid since ince it must be a"
            " list of numbers length less than 12 unless it is None."
        )
    else:
        for eve in event_types:
            if not isinstance(eve, (int, float, complex)) or not any(valid_eve == eve for valid_eve in valid_event_types):
                raise ValueError(
                    "ERR#0303: the introduced event_types value is not valid since ince it must be a"
                    " list of numbers with each value less than 12 unless it is None."
                )
    
    if begin_date is None:
        begin_date = datetime.datetime.now().strftime('%b %d, %Y')
        warnings.warn(f"the introduced begin_date value is None, set to {begin_date}")
    elif not isinstance(begin_date, str):
         raise ValueError(
            "ERR#0401: the introduced begin_date value is not valid since ince it must be a"
            " date string"
        )
    elif not any(is_date_parsing(begin_date, date_format) for date_format in date_format_list):
        raise ValueError(
            f"ERR#0402: the introduced begin_date value is not valid since ince it must be a date string with format {date_format_list}"
        )

    if end_date is None:
        end_date = datetime.datetime.now().strftime('%b %d, %Y')
        warnings.warn(f"the introduced end_date value is None, set to {end_date}")
    elif not isinstance(end_date, str):
         raise ValueError(
            "ERR#0501: the introduced end_date value is not valid since ince it must be a"
            " date string"
        )
    elif not any(is_date_parsing(end_date, date_format) for date_format in date_format_list):
        raise ValueError(
            f"ERR#0502: the introduced end_date value is not valid since ince it must be a date string with format {date_format_list}"
        )

    data_send = {
        "default_view": default_view,
        "impacts": impacts,
        "event_types": event_types,
        "currencies": currencies,
        "begin_date": begin_date,
        "end_date": end_date
    }

    baseURL = "https://www.forexfactory.com/"
    rangelink = baseURL + "calendar?range=" + begin_date.replace(" ", "").replace(',', '.') + "-" + end_date.replace(" ", "").replace(',', '.')
    startlink = "calendar/apply-settings/1?navigation=0"
    detailURL= "calendar/details/0-"

    ecolink = baseURL + startlink
    # detaillink = baseURL + detailURL
    logging.info("Scraping data for link: {}".format(rangelink))
    
    req = urllib.request.Request(ecolink, method="POST")
    req.add_header("User-Agent", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
)
    data = json.dumps(data_send)
    data = data.encode()
    r = urllib.request.urlopen(req, data=data)
    content = r.read()
    result_obj = json.loads(content)
    # print(f"result_obj={json.dumps(result_obj, indent=6)} \n")

    data_array = []
    data = {}
    list_datas = result_obj["days"]
    if list_datas:
        for val_data in list_datas:
            if val_data["events"]:
                datetime_date = datetime.datetime.fromtimestamp(val_data["dateline"])
                for event_data in val_data["events"]:
                    data = event_data
                    datelime_date = datetime.datetime.fromtimestamp(event_data["dateline"])
                    data["date_time"] = datetime_date
                    data["datelime_date"] = datelime_date
                    if showDetails:
                        event_id = str(data['id'])
                        iddetaillink = baseURL + detailURL + event_id
                        req2 = urllib.request.Request(iddetaillink)
                        req2.add_header("User-Agent", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
)
                        r2 = urllib.request.urlopen(req2)
                        content2 = r2.read()
                        detail_obj = json.loads(content2)

                        if detail_obj:
                            data_list = detail_obj["data"]
                            spec_list = data_list["specs"]
                            history_list = data_list["history"]
                            # print(f"tested event_id = {detail_obj['data']['event_id']} and has_data_values = {history_list['has_data_values']}")
                            if spec_list:
                                for detail_val in spec_list:
                                    if detail_val["title"] == "Source": 
                                        soup = BeautifulSoup(detail_val["html"], "html.parser")
                                        val_a = soup.select("a")[0].text.strip()
                                        # print(f"soup={soup} \n and val_a = {val_a}\n")
                                        data["detail_source"] = val_a 
                                    if detail_val["title"] == "Measures": data["detail_measure"] = detail_val["html"]
                                    if detail_val["title"] == "Usual Effect": data["detail_effect"] = detail_val["html"]
                                    if detail_val["title"] == "Frequency": data["detail_frequency"] = detail_val["html"]
                            if history_list and history_list['has_data_values']:
                                events_titles = ["event_id", "date", "url", "actual", "previous", "revision", "forecast", "actualBetterWorse", "revisionBetterWorse"]
                                for num, history_val in enumerate(history_list["events"]):
                                    for event_title in events_titles:
                                        # print(f"{event_title} = {history_val[f'{event_title}']}")
                                        if  history_val[f"{event_title}"]: data[f"{event_title}_{num}"] = history_val[f"{event_title}"]

                        # print(f" detail_obj={json.dumps(detail_obj, indent=6)}\n")                    
                    data_array.append(data)

    dt_array = pd.DataFrame(data_array)
    # print(f"headers = {dt_array.columns}")
    if showDetails:
        headers = ['id', 'ebaseId', 'name', 'dateline', 'date', 'country', 'currency',
        'hasLinkedThreads', 'hasNotice', 'hasGraph', 'checkedIn',
        'isMasterList', 'firstInDay', 'showGridLine', 'greyed', 'upNext',
        'releaser', 'checker', 'impactClass', 'impactTitle', 'timeLabel',
        'actual', 'previous', 'revision', 'forecast', 'leaked',
        'actualBetterWorse', 'revisionBetterWorse', 'isSubscribable',
        'isSubscribed', 'showDetails', 'showGraph', 'enableDetailComponent',
        'enableExpandComponent', 'enableActualComponent', 'showExpanded',
        'siteId', 'editUrl',  'url', 'date_time', 'datelime_date',
        'detail_source', 'detail_measure', 'detail_effect', 'detail_frequency',
        'event_id_0', 'date_0', 'url_0', 'actual_0', 'previous_0', 'forecast_0',
        'actualBetterWorse_0', 'revision_0', 'revisionBetterWorse_0', 
        'event_id_1', 'date_1', 'url_1', 'actual_1', 'previous_1', 'forecast_1', 
        'actualBetterWorse_1', 'revision_1', 'revisionBetterWorse_1', 
        'event_id_2', 'date_2', 'url_2', 'actual_2', 'previous_2', 'forecast_2',
        'actualBetterWorse_2', 'revision_2', 'revisionBetterWorse_2', 
        'event_id_3', 'date_3', 'url_3', 'actual_3', 'previous_3', 
        'forecast_3', 'revision_3', 'actualBetterWorse_3', 'revisionBetterWorse_3', 
        'event_id_4', 'date_4', 'url_4', 'actual_4', 'previous_4', 
        'forecast_4', 'revision_4', 'actualBetterWorse_4', 'revisionBetterWorse_4']
    else:
        headers = ['id', 'ebaseId', 'name', 'dateline', 'country', 'currency',
       'hasLinkedThreads', 'hasNotice', 'hasGraph', 'checkedIn',
       'isMasterList', 'firstInDay', 'showGridLine', 'greyed', 'upNext',
       'releaser', 'checker', 'impactClass', 'impactTitle', 'timeLabel',
       'actual', 'previous', 'revision', 'forecast', 'leaked',
       'actualBetterWorse', 'revisionBetterWorse', 'isSubscribable',
       'isSubscribed', 'showDetails', 'showGraph', 'enableDetailComponent',
       'enableExpandComponent', 'enableActualComponent', 'showExpanded',
       'siteId', 'editUrl', 'date', 'url', 'date_time', 'datelime_date']
    # dt_array = dt_array[['id', 'date_time', 'date', 'timeLabel', 'name', 'dateline', 'datelime_date', 'country', 'currency', 'firstInDay', 'showGridLine', 'greyed', 'upNext', 'actual', 'previous', 'revision', 'forecast', 'leaked', 'actualBetterWorse', 'revisionBetterWorse', 'impactClass', 'impactTitle', 'hasLinkedThreads', 'hasNotice', 'hasGraph', 'checkedIn', 'isMasterList', 'releaser', 'checker', 'isSubscribable', 'isSubscribed', 'showDetails', 'showGraph', 'enableDetailComponent', 'enableExpandComponent', 'enableActualComponent', 'showExpanded', 'siteId', 'editUrl', 'url']]
    dt_array = dt_array[headers]
    return dt_array

if __name__ == "__main__":
    """
    Run this using the command "python `script_name`.py >> `output_name`.csv"
    """
    setLogger()

    # start checking if the value exist
    return_data = getEconomicCalendar(default_view="this_week",impacts=[3],event_types=[1,2,3,4,5,6,7,8,9,10,11],currencies=[9],begin_date="Oct 1, 2023",end_date="Oct 31, 2023", showDetails=False)
    print(f"return_data= \n {return_data.to_string()}")
    # https://www.forexfactory.com/calendar?range=sep15.2023-sep28.2023
    # getEconomicCalendar()
