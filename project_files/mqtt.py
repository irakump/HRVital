import network
from time import sleep
from umqtt.simple import MQTTClient
import ujson
import utime
import ntptime

import micropython
micropython.alloc_emergency_exception_buf(200)


SSID = "KMD751_Group_1"
PASSWORD = "vadelma123"
BROKER_IP = "192.168.1.253"
PORT = 21883


# ehkä kutsu tätä funktiota mainissa?
# Function to connect to WLAN
def connect_wlan():
    # Connecting to the group WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    # Attempt to connect once per second
    while wlan.isconnected() == False:
        print("Connecting... ")
        sleep(1)
    
    # Print the IP address of the Pico
    print("Connection successful. Pico IP:", wlan.ifconfig()[0])


class Mqtt:
    def __init__(self):
        connect_wlan()  # connect to wlan
        self.connect_mqtt()  # connect to mqtt
        
        self.kubios_result = False
        self.kubios_topic_pub = "kubios-request"  # topic to send ppi data to kubios
        self.kubios_topic_sub = "kubios-response"  # topic to listen for response from kubios
        self.basic_hrv_analysis_topic = "hrv_analysis"  # topic to send basic hrv analysis to
    
    # Connect to MQTT
    def connect_mqtt(self):
        try:
            self.mqtt_client = MQTTClient("", BROKER_IP, port=PORT)
            self.mqtt_client.set_callback(self.sub)  # callback for subscribing (listening)
            self.mqtt_client.connect(clean_session=True)
        except Exception as e:
            print(f"Failed to connect to MQTT: {e}")
    
    # do after message has been recieved
    def sub(self, sub, message):
        # decode message and transform it into dict
        json_string = message.decode()
        self.kubios_result = ujson.loads(json_string)
        #print(self.kubios_result)

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

    # send ppis to kubios through mqtt and listen to result
    def get_kubios_analysis_result(self, message):
        self.send_message_to_mqtt(message, self.kubios_topic_pub)
        self.listen_message_from_mqtt(topic=self.kubios_topic_sub)
        return self.kubios_result
    
    def send_basic_hrv_analysis_results_to_mqtt(self, message):
        # send basic hrv analysis results to hrv_analysis topic on mqtt
        # message has to be in dict format so message can be formatted to json and encoded
        message = ujson.dumps(message).encode()
        self.send_message_to_mqtt(message, self.basic_hrv_analysis_topic)
    
    def testi_kubios_tulos(self): #(self, ppis):
        # testifunktio tulosten printtaamiseen näytölle
        ppis = [828, 836, 852, 760, 800, 796, 856, 824, 808, 776, 724, 816, 800, 812, 812, 812, 756, 820, 812, 800]
        result1 = {'sns': 1.767119, 'mean_hr': 74.53416, 'timestamp': '30.4.2025 - 12:59', 'mean_ppi': 805, 'rmssd': 42.90517, 'sdnn': 30.65533, 'pns': -0.3011305}
        result = ['30.4.2025 - 12:59', 74, 805, 43, 31, 1.8, -0.3]
        
        #ppis = [828, 836, 824, 808, 776, 724, 816, 800, 812, 756, 820, 812, 800]
        #result = {'sns': 2.240657, 'mean_hr': 74.91356, 'timestamp': '30.4.2025 - 13:19', 'mean_ppi': 800.9232, 'rmssd': 41.12286, 'sdnn': 30.65182, 'pns': -0.3887478}
        
        #ppis = [818, 836, 824, 848, 776, 754, 816, 800, 732, 756, 820, 872, 802]
        #result = {'sns': 1.353096, 'mean_hr': 74.61257, 'timestamp': '30.4.2025 - 13:20', 'mean_ppi': 804.1537, 'rmssd': 47.97943, 'sdnn': 39.5884, 'pns': -0.2460783}
        return result

# kubios
# joskus tulee ongelma jos ppis ei ole lista vaikka onhan se (jos sen kopioi tähän muualta)
#ppis = [818, 836, 824, 848, 776, 754, 816, 800, 732, 756, 820, 872, 802]
#print(Mqtt().get_kubios_analysis_result(ppis))


# lähetä hrv mqtt:seen
"""
message = {"1": "analysis results", "2": "item"}
Mqtt().send_basic_hrv_analysis_results_to_mqtt(message)
"""
