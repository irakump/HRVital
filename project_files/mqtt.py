import network
from time import sleep
from umqtt.simple import MQTTClient
import ujson
import utime
import ntptime

import micropython
micropython.alloc_emergency_exception_buf(200)


timezone_time = 2  # input your timezone for accurate kubios timestamp


# this is done as pico board timezone is UTC (+0)
def get_local_date_time(timestamp):
    # split timestamp to date and time parts
    date, time = timestamp.split("T")
    time = time.split(".")[0]
    
    # split date to year, month and day
    # split time to hour, minute, second
    year, month, day = map(int, date.split("-"))
    hour, minute, second = map(int, time.split(":"))
    
    # get time in seconds, add timezone offset in seconds to it and transform back into date and time
    date_time_seconds = utime.mktime((year, month, day, hour, minute, second, 0, 0))
    offset = timezone_time * 3600  # timezone * seconds in hour
    local_date_time = utime.localtime(date_time_seconds + offset)
    
    # format date and time to readable form
    formatted_date_time = "{}.{}.{} - {}:{}".format(
        local_date_time[2], local_date_time[1], local_date_time[0],
        local_date_time[3], local_date_time[4],
    )
    return formatted_date_time


class Mqtt:
    SSID = "KMD751_Group_1"
    PASSWORD = "vadelma123"
    BROKER_IP = "192.168.1.253"
    PORT = 21883
    
    kubios_topic_pub = "kubios-request"  # topic to send ppi data to kubios
    kubios_topic_sub = "kubios-response"  # topic to listen for response from kubios
    basic_hrv_analysis_topic = "hrv_analysis"  # topic to send basic hrv analysis to

    def __init__(self):
        self.connect_mqtt()
        self.kubios_result = False
    
    # Connect to MQTT
    def connect_mqtt(self):
        try:
            self.mqtt_client = MQTTClient("", self.BROKER_IP, port=self.PORT)
            self.mqtt_client.set_callback(self.sub)  # callback for subscribing (listening)
            self.mqtt_client.connect(clean_session=True)
        except Exception as e:
            print(f"Failed to connect to MQTT: {e}")
    
    # do after message has been recieved
    def sub(self, sub, message):
        # decode message and transform it into dict
        json_string = message.decode()
        self.kubios_result = ujson.loads(json_string)

    # Send MQTT message
    def send_message_to_mqtt(self, message, topic):
        try:
            self.mqtt_client.publish(topic, message)
            
        except Exception as e:
            print(f"Failed to send MQTT message: {e}")

    # Listen to MQTT message
    def listen_message_from_mqtt(self, topic="#"):  # listen to all topics by default
        try:
            self.mqtt_client.subscribe(topic)
            
            # check for response while no result
            while not self.kubios_result:
                self.mqtt_client.check_msg()
        
        except Exception as e:
            print(f"Failed to get MQTT message: {e}")


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
    
    def format_kubios_response(self):
        analysis_data = self.kubios_result["data"]["analysis"]
        
        # format timestamp to more readable format
        timestamp = analysis_data["create_timestamp"]
        local_date_time = get_local_date_time(timestamp)
        
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

    # send ppis to kubios through mqtt and listen to result
    def get_kubios_analysis_result(self, ppis):
        message = self.input_ppis_to_kubios_request_message(ppis)
        
        self.send_message_to_mqtt(message, self.kubios_topic_pub)
        self.listen_message_from_mqtt(topic=self.kubios_topic_sub)
        
        return self.format_kubios_response()
    
    def send_basic_hrv_analysis_results_to_mqtt(self, message):
        # send basic hrv analysis results to hrv_analysis topic on mqtt
        # message has to be in dict format so message can be formatted to json and encoded
        message = ujson.dumps(message).encode()
        self.send_message_to_mqtt(message, self.basic_hrv_analysis_topic)
    
    def testi_kubios_tulos(self, ppis):
        # testifunktio tulosten printtaamiseen
        ppis = [828, 836, 852, 760, 800, 796, 856, 824, 808, 776, 724, 816, 800, 812, 812, 812, 756, 820, 812, 800]
        result = {'sns': 1.767119, 'mean_hr': 74.53416, 'timestamp': '30.4.2025 - 12:59', 'mean_ppi': 805, 'rmssd': 42.90517, 'sdnn': 30.65533, 'pns': -0.3011305}
        
        #ppis = [828, 836, 824, 808, 776, 724, 816, 800, 812, 756, 820, 812, 800]
        #result = {'sns': 2.240657, 'mean_hr': 74.91356, 'timestamp': '30.4.2025 - 13:19', 'mean_ppi': 800.9232, 'rmssd': 41.12286, 'sdnn': 30.65182, 'pns': -0.3887478}
        
        #ppis = [818, 836, 824, 848, 776, 754, 816, 800, 732, 756, 820, 872, 802]
        #result = {'sns': 1.353096, 'mean_hr': 74.61257, 'timestamp': '30.4.2025 - 13:20', 'mean_ppi': 804.1537, 'rmssd': 47.97943, 'sdnn': 39.5884, 'pns': -0.2460783}
        return result

# kubios
"""
# joskus tulee ongelma jos ppis ei ole lista vaikka onhan se (jos sen kopioi tähän muualta)
ppis = [818, 836, 824, 848, 776, 754, 816, 800, 732, 756, 820, 872, 802]
print(Mqtt().get_kubios_analysis_result(ppis))
"""

# lähetä hrv mqtt:seen
"""
message = {"1": "analysis results", "2": "item"}
Mqtt().send_basic_hrv_analysis_results_to_mqtt(message)
"""
