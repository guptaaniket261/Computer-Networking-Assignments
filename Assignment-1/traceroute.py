import subprocess
import sys
import getopt
import socket
import matplotlib.pyplot as plt
import os
import struct
import time


def printHelp():
    print("Usage: python traceroute.py [-h maximum_hops] [-w timeout] target_name")
               

def isReply(line):
    byteToStr = line.decode()
    l = byteToStr.strip().split()
    if(len(l)<1):
        return False
    if(l[0] == "Reply"):
        return True
    return False


def printStat(ttl, routerIP, rtt):
    print('{0} {1:6} {2:6} {3:6} {4}'.format(ttl, rtt[0], rtt[1], rtt[2], routerIP))


def ping(ipAddr, waitTime, ttl):
    cmd = 'ping -i {0} -n 3 -w {1} {2}'.format(str(ttl), str(waitTime), str(ipAddr))
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    routerIP = '*'
    rtt = []
    for line in process.stdout:
        if(isReply(line)):
            s = line.decode().strip().split()
            if(len(s)<5):
                continue
            if(routerIP == '*'):
                routerIP = s[2][:-1]
            if(s[3] == 'TTL'):
                rtt.append('*')
            else:
                rtt.append(s[4][5:])

    while(len(rtt)<3):
        rtt.append("*")
    return (routerIP, rtt)


def traceroute(dest, waitTime, maxHops):
    plot_rtt = []
    plot_hops = []
    ttl = 1
    try:
        dest_ip = socket.gethostbyname(dest)  #string 
    except socket.error as e:
        print("Enter valid destination")
        return
    # need to handle error here
    print("Tracing route to {0} with maximum of {1} hops".format(dest, maxHops))
    while(ttl<=maxHops):
        routerIP, rtt = ping(dest_ip, waitTime, ttl)
        if(routerIP !='*'):
            routerIP, rtt = ping(routerIP, waitTime, maxHops)
        printStat(ttl, routerIP, rtt)


        plot_hops.append(ttl)
        curr_rtt = int(waitTime)
        for i in range(3):
            if(rtt[i]!='*' and len(rtt)>2):
                curr_rtt = min(int(rtt[i][:-2]), curr_rtt)
        if(routerIP == '*'):
            curr_rtt = 0
        plot_rtt.append(curr_rtt)


        if(routerIP == dest_ip):
            break
        ttl +=1
    
    print("Trace completed")
    plt.plot(plot_hops, plot_rtt)
    plt.title("RTT vs HOPS for {0}".format(dest))
    plt.savefig('rtt_vs_hops_{0}.png'.format(dest.strip()),dpi=300, bbox_inches='tight')
    plt.show()
    

def main():
    args = sys.argv[1:]
    if(len(args)<1):
        printHelp()
        return
    try:
        flags, arg = getopt.getopt(args, "h:w:", [])
    except getopt.GetoptError:
        printHelp()
        return
    
    if(len(arg)==0):
        print("IP address must be specified.")
        return
    
    dest = arg[0].strip()
    waitTime = 2000
    maxHops = 30
    for flag, val in flags:
        if(flag == '-w'):
            waitTime = int(val.strip())
        elif (flag == '-h'):
            maxHops = int(val.strip()) 
    
    traceroute(dest, waitTime, maxHops)
    return



if __name__ == "__main__":
    main()