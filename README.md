# HRVital Project


## Hardware 2 Project

HRVital is the final project of the Hardware 2 course. The project objective was to make a device which measures physiological signals and analyses them to determine the physical well being of the subject.

## Requirements
- Thonny
- Raspberry Pi Pico
- Raspberry Pi
- Internet
- MQTT
- Kubios

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
