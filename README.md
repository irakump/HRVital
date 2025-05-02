# HRVital Project


## Hardware 2 Project

HRVital is the final project of the Hardware 2 course. The project objective was to make a device which measures physiological signals and analyses them to determine the physical well being of the subject.

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

1. Open Thonny and select Micropython (Raspberry Pi Pico) from the bottom right. 
2. Select Install micropython
3. From variant, select Raspberry Pi Pico W / Pico WH
4. Click install.
5. Click close when done.


### Install MQTT client

Install MQTT client to Raspberry Pi Pico by running **install_mqtt.py** script. Open it in Thonny, change the **SSID**, **PASSWORD**, **BROKER_IP** on top of the file and click run.


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

## Ready

Now you're all ready to use all the features of the HRVital! 
All of the necessary files are on Raspberry Pi Pico and they will run when the Pico is connected to a power source.
