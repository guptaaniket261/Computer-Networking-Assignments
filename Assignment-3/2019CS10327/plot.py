import sys
from matplotlib import pyplot as plt

def getCwnd(filename):
    file = open(filename, 'r')
    lines = file.readlines()
    time = [int(float(lines[0].strip().split()[0]))]
    cwnd = [0]
    for line in lines:
        curr_time, _ , curr_cwnd = [float(j) for j in line.strip().split()]
        time.append(curr_time)
        cwnd.append(curr_cwnd)
    return time, cwnd

flag = int(sys.argv[1])
if flag == 1:
    filename, heading = sys.argv[2:]
    time, cwnd = getCwnd(filename)
    fig,ax = plt.subplots()
    ax.set_xlabel("Time (in sec)")
    ax.set_ylabel("Congestion Window")
    ax.set_title(heading)
    ax.plot(time, cwnd)
    plt.show()
    imgFilename = filename.split('.')[0] + '.png'
    plt.savefig(imgFilename)

elif flag == 2:
    filename, channelDataRate, appDataRate = sys.argv[2:]
    channelDataRate, appDataRate = float(channelDataRate), float(appDataRate)
    time, cwnd = getCwnd(filename)
    fig,ax = plt.subplots()
    ax.set_xlabel("Time (in sec)")
    ax.set_ylabel("Congestion Window")
    ax.set_title("Channel Data Rate: {0} and Application Data Rate: {1}".format(channelDataRate, appDataRate))
    ax.plot(time, cwnd)
    plt.show()
    imgFilename = filename.split('.')[0] + '.png'
    plt.savefig(imgFilename)

elif flag == 3:
    filename, configuration, connection = sys.argv[2:]
    time, cwnd = getCwnd(filename)
    fig,ax = plt.subplots()
    ax.set_xlabel("Time (in sec)")
    ax.set_ylabel("Congestion Window")
    ax.set_title("Congestion Window VS Time at Connection {0} for Configuration {1}".format(connection, configuration))
    ax.plot(time, cwnd)
    plt.show()
    imgFilename = filename.split('.')[0] + '.png'
    plt.savefig(imgFilename)



