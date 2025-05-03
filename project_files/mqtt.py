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
