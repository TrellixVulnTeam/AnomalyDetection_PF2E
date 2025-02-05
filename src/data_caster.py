# AnomalyDetection is a free software developed by Tommaso Fontana for Würth Phoenix S.r.l. under GPL-2 License.

import re
import numpy as np
from time import time
from datetime import datetime
from pprint import pprint

def is_not_all_nan(x):
    try:
        return not np.all(np.isnan(x))
    except TypeError:
        return False

def get_floor_hour(t):
    return (t % (24 * 60 * 60)) // (60 * 60)


def data_caster(data):
    data = {
        key : transpose(value)
        for key, value in data.items()
    }
    casted = {
        K : {
            k : np.array([
                value_caster(k, x)
                for x in v
            ]).reshape(-1, 1)
            for k, v in V.items()
        }
        for K, V in data.items()
    }
    nan_removed = {
        K : {
            k : v 
            for k, v in V.items()
            if is_not_all_nan(v)
        }
        for K, V in casted.items()
    }
    group_by_hours = {
        Kpi : {
            hour :{
                 Selector: values[get_floor_hour(selectors["time"]) == hour]
                for Selector, values in selectors.items()
            }
            for hour in range(24)
        }
        for Kpi, selectors in nan_removed.items()
    }
    return group_by_hours

def value_caster(key, value):
    """THIS IS HORRIBLE, but I need to cast strings to the actual value and I have no info about what those are."""
    if type(value) in [int, float]:
        return value
    if type(value) == str:
        if key == "time":
            result = parse_time_to_epoch(value)
            if result and result != 0:
                return result

        try:
            return float(value)
        except:
            pass

        return np.nan
    else:
        return value

epoch_to_iso = lambda x: datetime.fromtimestamp(x).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

iso_to_epoch = lambda x: datetime.fromisoformat(x).timestamp()

rfc3339_pattern = re.compile(r"(.+?)(\.(\d+))?Z")
time_pattern = re.compile(r"(\d+w)?(\d+d)?(\d+h)?(\d+m)?(\d+.?\d*s)?")
    

def parse_time_to_epoch(string):
    if string.endswith("Z"):
        return rfc3339_to_epoch(string)
    if string.isnumeric():
        return int(string)
    if re.match(time_pattern, string):
        return time_to_epoch(string)
    
    
def rfc3339_to_epoch(string):
    founds = re.findall(rfc3339_pattern, string)
    if len(founds) <= 0:
        return string
    date, _, ns = founds[0]
    dt = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')
    return dt.timestamp() + float("0." + ns) # TIME ZONES OH NO

def epoch_to_time(epoch):
    if epoch == "inf":
        return "inf"

    weeks,  epoch = divmod(epoch, (7 * 24 * 60 * 60))
    days,   epoch = divmod(epoch, (24 * 60 * 60))
    hours,  epoch = divmod(epoch, (60 * 60))
    mins,   sec   = divmod(epoch, (60))
    
    out = ""
    if weeks:
        out += f"{weeks}w"
    if days:
        out += f"{days}d"
    if hours:
        out += f"{hours}h"
    if mins:
        out += f"{mins}m"
    if sec:
        out += f"{sec:.3f}s"
    return out
    
def time_to_epoch(time):
    weeks, days, hours, minuts, sec = re.findall(time_pattern, time)[0]
    result = 0
    if sec:
        result += float(sec[:-1])
    if minuts:
        result += 60 * int(minuts[:-1])
    if hours:
        result += 60 * 60 * int(hours[:-1])
    if days:
        result += 60 * 60 * 24 * int(days[:-1])
    if weeks:
        result += 60 * 60 * 24 * 7 * int(weeks[:-1])
    return result

def transpose(lista):
    """Transpose a list of dictionaries to a dictionary of lists. 
       It assumes all the dictionaries have the sames keys."""
    _dict = {}
    for x in lista:
        for k, v in x.items():
            _dict.setdefault(k,[])
            _dict[k] += [v]
    return _dict
