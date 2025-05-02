from collect_data_v2 import collect_data_n_seconds
from basic_hrv_analysis import HeartRate, BasicHRVAnalysis
from mqtt import Mqtt
import ujson
import utime

import micropython
micropython.alloc_emergency_exception_buf(200)


class Kubios:
    def __init__(self):
        self.timezone_time = 3  # input your timezone for accurate kubios timestamp
    
    # this is done as pico board timezone is UTC (+0)
    def get_local_date_time(self, timestamp):
        # split timestamp to date and time parts
        date, time = timestamp.split("T")
        time = time.split(".")[0]
    
        # split date to year, month and day
        # split time to hour, minute, second
        year, month, day = map(int, date.split("-"))
        hour, minute, second = map(int, time.split(":"))
    
        # get time in seconds, add timezone offset in seconds to it and transform back into date and time
        date_time_seconds = utime.mktime((year, month, day, hour, minute, second, 0, 0))
        offset = self.timezone_time * 3600  # timezone * seconds in hour
        local_date_time = utime.localtime(date_time_seconds + offset)
    
        # format date and time to readable form
        formatted_date_time = "{}.{}.{} {}:{}".format(
            local_date_time[2], local_date_time[1], local_date_time[0],
            local_date_time[3], local_date_time[4],
        )
        return formatted_date_time
    
    def input_ppis_to_kubios_request_message(self, ppis):
        # kubios request format
        dataset = {
            'id': 123,
            'type': 'RRI',
            'data': ppis,
            'analysis': {'type': 'readiness'}
        }
        # transform dict to json format and encode to bytes
        return ujson.dumps(dataset).encode()
    
    def format_kubios_response(self, kubios_result):
        analysis_data = kubios_result["data"]["analysis"]
        
        # format timestamp to more readable format
        timestamp = analysis_data["create_timestamp"]
        local_date_time = self.get_local_date_time(timestamp)
        
        # save results to dict
        analysis_data_list = {
            "timestamp": local_date_time,
            "mean_hr": analysis_data["mean_hr_bpm"],
            "mean_ppi": analysis_data["mean_rr_ms"],
            "rmssd": analysis_data["rmssd_ms"],
            "sdnn": analysis_data["sdnn_ms"],
            "pns": analysis_data["pns_index"],
            "sns": analysis_data["sns_index"]
        }
        return analysis_data_list
    
    def analyze_data_with_kubios(self):
        # collect 30s of live data, then calculate peaks and ppis and send ppis to kubios for analysis
        data = collect_data_n_seconds(seconds=30)
        if not data:  # data collection canceled
            return "Data collection cancelled"
        #print(len(data))
        
        hr_class = HeartRate()
        peak_indexes = hr_class.find_peaks(data)
        #print('peaks', len(peak_indexes), peak_indexes)
        
        all_ppis = BasicHRVAnalysis().get_ppis(peak_indexes)  # in ms
        print('all_ppis', len(all_ppis), all_ppis)
        
        message = self.input_ppis_to_kubios_request_message(all_ppis)
        
        #mqtt = Mqtt()
        kubios_result = Mqtt().get_kubios_analysis_result(message)
        #print(kubios_result)
        
        # return string telling analysis could not be performed if data has value "Invalid request"
        # this happens when there aren't enough ppis to perform the analysis
        # otherwise return formatted response
        if not kubios_result or kubios_result["data"] == "Invalid request":
            return "Could not perform Kubios analysis"
            #return {'invalid_request': "Could not perform Kubios analysis"}
        return self.format_kubios_response(kubios_result)


print(Kubios().analyze_data_with_kubios())
