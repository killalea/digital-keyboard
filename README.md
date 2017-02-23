# Digital Keyboard

Welcome to the Digital Keyboard project! We are focused on allowing people with physical limitations to play music on a digital keyboard using universal design principles.


## Instructions to run source on linux

Install dependencies:
* Clone our repo: `git clone https://github.com/killalea/digital-keyboard.git`
* Be sure you are running Python 2.7
* Install python requirements: `pip install -r requirements.txt`
* Install pyqt: `sudo apt-get install python-pyqt5`

Get audio priveleges:
* Output your username: `whoami`
* Give your user audo privileges `sudo adduser [your username] audio`
* Then you have to reboot
* Check that you have proper privileges: `ulimit -r -l`

Credit where it's due, the audio privilege part comes from here: https://ubuntuforums.org/archive/index.php/t-1637399.html

To run
* `python digital-keyboard.py`

## Our roots

This project is built off of this repository: https://github.com/kosterjo/eecs481DigitalInsturment and was originally developed by:
Brendan Killalea (Me), John Koster, Brian Lim, and Thomas Finch. 

