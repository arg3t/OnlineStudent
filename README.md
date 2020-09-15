# The Ultimate Online Student 

This is a personal projects that aims to be the perfect online student. It auromatically joins zoom meetings, records classes and mirrors a pre-recorded video to a virtual loopback camera. Keep in mind that this is only meant to work on linux.

## Notes and Installation

You must install v4l2loopback driver to your kernel. This will allow the script to send a prerecorded video into your camera. You must take note that in main.py, `RECORD_TEMPLATE` is customized for my dual monitor setup and you might have to modify it depending on yours. Do not roast me about the quality of my code since this is strictly a personal project that was not initially meant for public use. If your school has a different online web portal, all you need to do is modify get_meetings.py according to your needs.

## Missing Features

* ~Add audio recording through an alsa loopback device.~
* ~Add automatic compression feature at the end of the day in order to save disk space.~
* ~Add automatic backup feature~ (Not Tested)
