import RPi._GPIO as GPIO
import time
import ADC0832
import os
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import json
import Adafruit_DHT

sensor = Adafruit_DHT.DHT11
moisture_threshold = 30.00
channel= 23
temp_pin = 25
temp_threshold = 25
fan_pin = 16
lamp_led = 4

clientID = "755908897785"
endpoint = "a5inpkw6al4tt-ats.iot.us-east-1.amazonaws.com" #Use the endpoint from the settings page in the IoT console
port = 8883
topic = "raspberry/templigh"
#

GPIO.setmode(GPIO.BCM)

# Init MQTT client
mqttc = AWSIoTMQTTClient(clientID)
mqttc.configureEndpoint(endpoint,port)
mqttc.configureCredentials("certs/AmazonRootCA1.pem","certs/raspberry-private.pem.key","certs/raspberry-certificate.pem.crt")

def send_data(message):
    mqttc.publish(topic, json.dumps(message), 0)
    print("Message Published")
def init():
    ADC0832.setup()
    GPIO.setup(channel, GPIO.OUT)
    GPIO.setup(temp_pin,GPIO.OUT)
    GPIO.setup(fan_pin,GPIO.OUT)
    GPIO.setup(lamp_led, GPIO.OUT)

def relay_on(pin):
     GPIO.output(pin, GPIO.LOW)
     
     
def relay_off(pin):
     GPIO.output(pin, GPIO.HIGH)
    
def soilMoisture():
    res = ADC0832.getADC(1)
    vol = 3.3/255 * res
    print("vol", vol)
    moisture_percentage = ((3.3-vol))*100
    time.sleep(0.2)
    print(f'Moisture: {moisture_percentage:.2f}%')
    
    return moisture_percentage
def photoresistor():
    res = ADC0832.getADC(0)
    print(res)
    vol = 3.3/255 * res
   # time.sleep(0.2)
    print ('voltage: %.2fV' %(vol))
    #If lux >10
    if res <128:
        GPIO.output(lamp_led, GPIO.HIGH)
        print("It is Dark")
       
    else:
        GPIO.output(lamp_led, GPIO.LOW)
        print("It is Day")
   
    return "{:.2f}".format(vol)
    
def temp():
    humidity, temperature = Adafruit_DHT.read_retry(sensor,temp_pin )
    if humidity is not None and temperature is not None:
        print(f"Temperature: {temperature:.2f}°C, Humidity: {humidity:.2f}%")
        if temperature > temp_threshold:
            GPIO.output(fan_pin, GPIO.HIGH)
            time.sleep(30)
            print("Fan is on")
            GPIO.output(fan_pin, GPIO.LOW)
        else:
            GPIO.output(fan_pin, GPIO.LOW)
            print("Fan is off")

    
    else:
        print("Failed to retrieve data from the sensor")


   

def loop():
    while True:
        try:
            moisture =soilMoisture()
            print(moisture)
            if moisture < moisture_threshold:
                relay_on(channel)
                time.sleep(3.0)
                relay_off(channel)
            else:
                print("Sensor is in water")
                relay_off(channel)
            # message = {
                #'humidity' : moisture
               # }
               
            
            # Send data to topic
            #send_data(message)
            temp()
            photoresistor()
           
        except RuntimeError as error:     # Errors happen fairly often, DHT's are hard to read, just keep going
            print(error.args[0])
        


if __name__ == '__main__':
    #print("Starting program...")
    init()
   # mqttc.connect()
   # print("Connect OK!")
    try:

        loop()
    except KeyboardInterrupt: 
        ADC0832.destroy()
        GPIO.cleanup()
       # mqttc.disconnect()
        exit()
       