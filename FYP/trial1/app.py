from flask import Flask, render_template, request, redirect, flash, get_flashed_messages
from FYP.trial1.plotters.newPlotter import Plotter
import matplotlib.pyplot as plt
import os
import random
import glob
import paramiko
import uuid
import socket
import subprocess
app = Flask(__name__)
app.secret_key = 'secret123'


@app.route('/', methods=['GET', 'POST'])
def index():
    selected = None
    activities = ["standing", "walking", "static", "falling"]

    result = False
    # if not result:
    #     result = runCommandOnPi()
    messages = get_flashed_messages()
    print(messages)
    if request.method == 'POST':
        selectedActivity = selected = request.form['activity']
        randomPcapFile = getPcapFileBasedOnActivity(selectedActivity)
        createPlotter(randomPcapFile)
        plotPath = os.path.join('static/images','generated.png')
        return render_template('index.html', plot_path=plotPath, selected=selected)


    return render_template('index.html', activities=activities,  messages=messages)

def createPlotter(pcapFile):
    plotter = Plotter(pcapFile, 200, 80)
    plotter.heatmap()
    plt.savefig('static/images/generated.png')

def getPcapFileBasedOnActivity(activity):
    baseDir = os.path.abspath(os.path.dirname(__file__))
    # /{activity}-*.pcap
    pattern = f"data\{activity}-*.pcap"
    folderPath = os.path.join(baseDir, pattern)
    fileList = glob.glob(folderPath)
    randomPcapFile = random.choice(fileList)

    return os.path.join(folderPath, randomPcapFile)

def getMacAddress():
    hostname = socket.gethostname()
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e + 2] for e in range(0, 12, 2)])

@app.route('/run-command', methods=['POST'])
def runCommandOnPi():
    rpiIP = "192.168.1.154"
    macOfDevice =getMacAddress().upper()

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(rpiIP, username="pi", password="pi1234")

    # stdin, stdout, stderr = ssh.exec_command(f"mcp -C 1 -N 1 -c 36/80 -m {macOfDevice}")

    # debugging
    stdin, stdout, stderr = ssh.exec_command(f"mcp -C 1 -N 1 -c 36/80")
    result = stdout.read().decode()

    results = []
    commands = [
        "sudo ifconfig wlan0 up",
        f"nexutil -Iwlan0 -s500 -b -l34 -v{result}",
        "iw dev wlan0 interface add mon0 type monitor",
        "sudo ip link set mon0 up"
    ]
    for command in commands:
        stdin, stdout, stderr = ssh.exec_command(command)
        r = stdout.read().decode()
        results.append(r)
    ssh.close()
    flash('Command executed successfully.')
    return redirect('/')

@app.route('/record-activity', methods=['POST'])
def recordActivity():
    activity = request.form['activity'].lower()
    rpiIP = "192.168.1.154"
    macOfDevice = getMacAddress().upper()

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(rpiIP, username="pi", password="pi1234")
    results = []
    commands = [
        # f"sudo tcpdump -i wlan0 dst port 5500 -vv -w {activity}-%s.pcap -G 3 -W 1 -Z root",
        f"sudo tcpdump -i wlan0 dst port 5500 -vv -w {activity}.pcap -G 3 -W 1 -Z root",
        "ls"
    ]
    for command in commands:
        stdin, stdout, stderr = ssh.exec_command(command)
        r = stdout.read().decode()
        results.append(r)

    # transferring recorded activity pcap file
    sftp = ssh.open_sftp()
    filePath = f'generated/data/{activity}.pcap'
    sftp.get(f'{activity}.pcap', filePath)
    sftp.close()

    createPlotter(filePath)
    # stdin, stdout, stderr = ssh.exec_command(f"sudo tcpdump -i wlan0 dst port 5500 -vv -w test-%s.pcap -G 3 -W 1 -Z root")
    # result = stdout.read().decode()
    plotPath = os.path.join('static/images', 'generated.png')
    return render_template('index.html', plot_path=plotPath)
if __name__ == '__main__':
    app.run(debug=True)