# Android Task runner
Automated experiment execution on Android devices

## Install
This tool is only tested on Ubuntu, but it should work in other linux distributions.
You'll need:
- Python 2.7
- Android Debug Bridge (`sudo apt install android-tools-adb`)
- Android SDK Tools (`sudo apt install monkeyrunner`)
- JDK 8 (NOT JDK 9) (`sudo apt install openjdk-8-jre`)
- lxml (`sudo apt install python-lxml`)

## Quick start
To run an experiment, run:
```bash
python android_runner your_config.json
```
There is an example configuration file in `example/example_config.json`

## Structure
### devices.json
A JSON config that maps devices names to their ADB ids for easy reference in config files.

### Experiment Configuration
Below is a reference to the fields for the experiment configuration. It is not always updated.

**type** *string*  
Type of the experiment. Can be `web` or `native`

**replications** *positive integer*  
Number of times an experiment is run.

**devices** *Array\<String\>*  
The names of devices to use. They will be translated into ids defined in devices.json.

**paths** *Array\<String\>*  
The paths to the APKs/URLs to test with.

**browsers** *Array\<String\>*  
*Dependent on type = web*  
The names of browser(s) to use. Currently supported values are `chrome`.

**profilers** *JSON*   
A JSON object to describe the profilers to be used and their arguments. Below is an example:
```json
  "profilers": {
    "trepn": {
      "sample_interval": 100
    }
  }
```

**scripts** *JSON*  
A JSON list of types and paths of scripts to run. Below is an example:
```json
"scripts": {
  "before_experiment": "before_experiment.py",
  "before_run": "before_run.py",
  "interaction": "interaction.py",
  "after_run": "after_run.py",
  "after_experiment": "after_experiment.py"
}
```
Below are the supported types:
- before_experiment  
  executes once before the first run
- before_run  
  executes before every run
- interaction  
  executes between the start and end of a run
- after_run  
  executes after a run completes
- after_experiment  
  executes once after the last run

## FAQ
### Devices have no permissions (udev requires plugdev group membership)
This happens when the user calling adb is not in the plugdev group.
#### Fix
`sudo usermod -aG plugdev $LOGNAME`
#### References
https://developer.android.com/studio/run/device.html  
http://www.janosgyerik.com/adding-udev-rules-for-usb-debugging-android-devices/