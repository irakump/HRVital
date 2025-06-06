# HRVital Project


## Hardware 2 Project

HRVital is an IoT-based system developed as a group project during the Hardware 2 course. The goal was to design and implement a device capable of measuring and analyzing physiological signals — particularly heart rate and heart rate variability (HRV) — to assess the user’s physical well-being.

The system combines embedded hardware, network communication, and third-party analysis software (Kubios Cloud) to deliver a functional health-monitoring prototype.

## Requirements
- Thonny IDE - the project is programmed using MicroPython
- Raspberry Pi Pico W - a microcontroller that reads physiological data from the connected pulse sensor
- Raspberry Pi - acts as a backend device for data handling and communication
- Internet - required to connect devices via Wi-Fi and allow real-time communication using MQTT protocol
- MQTT - devices communicate via MQTT over a local Wi-Fi network
- Kubios - the collected HR and HRV data is analyzed using Kubios Cloud, a professional-grade software for heart rate variability analysis

## Setting up the device

### Cloning the repository

Clone the repository with submodules to your computer by running the following command:

```
git clone --recurse-submodules https://gitlab.metropolia.fi/sandraj/hrvital-project.git
```

Update submodules:
```
git submodule update --recursive --remote
```

### Empty Raspberry Pi Pico

Empty your Raspberry Pi Pico by following these steps:
1. Plug the USB cable to computer while holding down BOOTSEL button on Raspberry Pi Pico.
2. A external device will appear on your file manager.
3. Locate **flash_nuke.uf2** file from the cloned repository and copy it to the external device which appeared on step 2.
4. The Raspberry Pi Pico will empty and the external device folder will disappear.

### Setup MicroPython to Raspberry Pi Pico

1. Open Thonny.
2. Select MicroPython (Raspberry Pi Pico) from the bottom right. 
3. Select Install MicroPython.
4. From variant, select Raspberry Pi Pico W / Pico WH.
5. Click Install.
6. Click close when done.

### Run install script

Run install script to input files to Raspberry Pi Pico.

1. Open terminal in the cloned repository.
2. Run the install script.\
    On Windows
    ````
    install.cmd
    ````
    On macOS
    ```
    install.sh
    ```

### Change network settings
Open Thonny and select **mqtt.py** from within Raspberry Pi Pico.
Change **SSID**, **PASSWORD** and **BROKER_IP** on top of the file to match yours. Save the changes.

## Ready

Now you're all ready to use the HRVital. Open **main.py** and run it.
