import get_meetings
import subprocess
import datetime
import os
import json
import time
import sys
from smb.SMBConnection import SMBConnection

RECORD_PATH = "recordings"
LISTENING_VIDEO_PATH = "listening.mkv"
VIRTUAL_CAMERA_PATH = "/dev/video2"
PULSEAUDIO_INDEX = 5
X_OFFSET = sys.argv[1]
PULSEAUDIO_INDEX = sys.argv[2]

RECORD_TEMPLATE = ["ffmpeg", "-nostdin", "-video_size", "1920x1080", "-f", "x11grab", "-i", ":0.0+{},0".format(X_OFFSET), "-f", "pulse", "-ac", "2", "-i", str(PULSEAUDIO_INDEX), "-vcodec", "libx264", "-crf", "0", "-preset", "ultrafast", "-acodec", "pcm_s16le"]
CAMERA_TEMPLATE = ["ffmpeg", "-re", "-i", LISTENING_VIDEO_PATH, "-map", "0:v", "-f", "v4l2", VIRTUAL_CAMERA_PATH]
COMPRESSION_TEMPLATE = ["ffmpeg", "-i", None, "-vcodec", "libx265", "-crf", "28", None]

if not os.path.exists(VIRTUAL_CAMERA_PATH):
	os.system("sudo modprobe -r v4l2loopback")
	os.system("sudo modprobe v4l2loopback")

if not os.path.exists(RECORD_PATH):
	os.mkdir(RECORD_PATH)

with open("config.json", "r") as f:
        config = json.loads(f.read())
        creds = config["creds"]
        backup_creds = config["backup"]

next_day = datetime.datetime.today()

def backup(directory):
    conn = SMBConnection(backup_creds["user"], backup_creds["password"],
                         backup_creds["server_name"], backup_creds["server_name"], use_ntlm_v2 = True)
    conn.connect(backup_creds["ip"])
    files = conn.listPath(backup_creds["share"], "/")
    exists = False
 
    for f in files:
        if f.filename == backup_creds["path"]:
            if f.isDirectory:
                exists = True
                break
            else:
                conn.close()
                return 1

    if not exists:
        try:
            conn.createDirectory(backup_creds["share"],backup_creds["path"])
        except Exception as e:
            print(e)
            return 1
    folder = conn.getAttributes(backup_creds["share"], backup_creds["path"])
    if folder.isReadOnly:
        print("BACKUP PATH IS READONLY")
        return 1

    local_path = os.path.join(RECORD_PATH, directory) 
    remote_path = os.path.join(backup_creds["path"], directory)

    conn.createDirectory(backup_creds["share"], remote_path) 
    for i in os.listdir(local_path):
        with open(os.path.join(local_path, i), "rb") as f:
            conn.storeFile(backup_creds["share"], 
                           os.path.join(remote_path, i),
                           f)
    conn.close()

while True:
	now = datetime.datetime.today()
	while now < next_day:
		time.sleep(7200)
		now = datetime.datetime.today()
	print("NEW DAY")
	print("GENERATING MEETING LIST")
	meetings = get_meetings.get_meetings(creds["TC"], creds["passwd"])
	print("DONE\n")
	day = datetime.datetime.today().strftime("%d_%m_%Y")
	next_day = datetime.datetime.strptime("{} 00:00:00".format(day), '%d_%m_%Y %H:%M:%S') + datetime.timedelta(days = 1)
	if not os.path.exists(os.path.join(RECORD_PATH, day)):
		os.mkdir(os.path.join(RECORD_PATH, day))
	video_recording = None
	camera_mirroring = None
	k = None
	for k,i in enumerate(meetings):
		now = datetime.datetime.today()
		meeting_time = datetime.datetime.strptime("{} {}:00".format(day, i["time"]), '%d_%m_%Y %H:%M:%S')
		if video_recording:
			end_time = datetime.datetime.strptime("{} {}:00".format(day, meetings[k-1]["time"]), '%d_%m_%Y %H:%M:%S')+ datetime.timedelta(minutes = 30)
			while now < end_time:
				time.sleep(30)
				now = datetime.datetime.today()
			print("CLASS FINISHED, TERMINATING PREVIOUS RECORDINGS\n")
			video_recording.terminate()
			camera_mirroring.terminate()
		print(i["time"])
		print(i["class"])
		while now < meeting_time:
			time.sleep(30)
			now = datetime.datetime.today()
		print("STARTING")
		subprocess.Popen(["xdg-open", i["meeting_url"]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		cmd = RECORD_TEMPLATE + [os.path.join(RECORD_PATH, day, "{}.{}.mkv".format(k, i["class"]))]
		if os.path.exists(os.path.join(RECORD_PATH, day, "{}.{}.mkv".format(k, i["class"]))):
			os.remove(os.path.join(RECORD_PATH, day, "{}.{}.mkv".format(k, i["class"])))
#		 print(" ".join(cmd))
		video_recording = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		camera_mirroring = subprocess.Popen(CAMERA_TEMPLATE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	if k:
		end_time = datetime.datetime.strptime("{} {}:00".format(day, meetings[k]["time"]), '%d_%m_%Y %H:%M:%S')+ datetime.timedelta(minutes = 30)
		while now < end_time:
			time.sleep(30)
			now = datetime.datetime.today()
		print("CLASS FINISHED, TERMINATING PREVIOUS RECORDINGS\n")
		video_recording.terminate()
		camera_mirroring.terminate()
	print("\nALL CLASSES RECORDED\n")
	todays_recordings_path = os.path.join(RECORD_PATH, day)
	recordings = os.listdir(todays_recordings_path)
	for r in recordings:
		COMPRESSION_TEMPLATE[2] = os.path.join(todays_recordings_path, r)
		COMPRESSION_TEMPLATE[-1] = os.path.join(todays_recordings_path, r[:-3] + ".mp4")
		print("COMPRESSING " + r)
		compression_process = subprocess.Popen(COMPRESSION_TEMPLATE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		exit_code = compression_process.wait()
		print("FFMPEG EXITED WITH STATUS CODE {}".format(exit_code))
		if exit_code == 0:
			os.remove(COMPRESSION_TEMPLATE[2])
		


	
