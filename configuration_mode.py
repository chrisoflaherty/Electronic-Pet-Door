# Configuration Mode
# Christopher O'Flaherty

import usocket as socket
from ure import sub
import network
import gc
from machine import RTC
import ntptime

#######################################
######## Access point MODE ############
#######################################

# HTML web page the user will see
def ap_web_page():
    html_webpage = """<!DOCTYPE HTML><html>
    <head>
      <title>Electronic Pet Door</title>
      <center><h1>Electronic Pet Door</h1></center>
      <center><h2><small> Enter your network ID and password </small></h2></center>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <style>
      body {background-color: grey}
      #subbutt{
        background-color: blue;
        color: white;
        padding: 16px 32px;
        text-decoration: none;
        margin: 4px 2px;
        border: 1px solid black;
        border-radius: 0px;
        -moz-border-radius: 5px;
      }
      </style>
      
    </head>
    <body>
    
      <form action="/action_page.php" method="get">
      
      <center>SSID: <input type="text" name=ssid></center><br>
      <center>Password: <input type="text" name=password></center><br>
      <center><input type="submit" value="Submit" id="subbutt"></center>
    </form>
    </body>
    </html>"""
    return html_webpage

def access_point():
    gc.collect()
    
    # Access Point credentials
    ssid = 'Electronic Pet Door'
    password = '123456789'

    # Local network credentials placeholders
    USERNAME = ''
    PASSWORD = ''

    header = {}

    # Creates an Acess Point for the user to connect to
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=ssid,authmode=network.AUTH_WPA_WPA2_PSK, password=password)
    while ap.active() == False:
      pass
    print('Connection successful')
    print(ap.ifconfig())
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 80))
    s.listen(5)

    # Looks for a connection and received HTTP GETs
    while True:
        conn, addr = s.accept()
        print('Got a connection from %s' % str(addr))
        request = conn.recv(1024)
        request = str(request)
        if request[:6] == "b'GET " and request.find("ssid=") > 0:
            print("Closing Access Point. Storing Credentials.")
            break
        print('Content = %s' % request)
        response = ap_web_page()
        conn.send('HTTP/1.1 200 OK\n')
        conn.send('Content-Type: text/html\n')
        conn.send('Connection: close\n\n')
        conn.sendall(response)
        conn.close()

    # Closes connection
    conn.close()
    ap.active(False)
    s.close()

    # Greps the USERNAME and PASSWORD
    USERNAME = request[int(request.find("ssid="))+5: int(request.find("&password="))]
    PASSWORD = request[int(request.find("&password="))+10: request.find(" HTTP/1.1\r\nHost:")]
    PASSWORD = PASSWORD.split(" ")
    PASSWORD = PASSWORD[0]
    USERNAME = sub("\+", " ", USERNAME)
    PASSWORD = sub("\+", " ", PASSWORD)
    print("Username= " + USERNAME + "\nPassword= " + PASSWORD)

    # Write the USERNAME and PASSWORD to the file
    with open("credentials.txt", "w") as file:
        file.write(USERNAME)
        file.write("\n")
        file.write(PASSWORD)
        
    gc.collect()
    
    
#####################################
######## WEB SERVER MODE ############
#####################################
    
# Web Server global dictionaries
sched = {} # Schedule dictionary
pop= {} # Web page dictionary
    
# Reset button
#reset_button = 
    
# For the reset button
def reset_credentials():
    with open("credentials.txt", "w") as file:
        pass

# Prints the current time from the RTC
def printTime(currtime):
    if currtime[4] < 4:
        hour = currtime[4]
        hour = hour - 5 + 24
    else:
        hour = currtime[4]
        hour = hour - 5
    print('Date: ' + str(currtime[1]) + '/' + str(currtime[2]) + '/' + str(currtime[0]))
    print('Time: ' + str(hour) + ':' + str(currtime[5]) + ':' + str(currtime[6]) + ' HRS')

# Creates a template schedule
def populate_schedule():
    with open("schedule.txt", "w+") as f:
        for x in range(2):
            f.write("0\n")
            f.write("0\n")
            for i in range(1,12,1):
                if i < 10:
                    f.write("0\n")
                    f.write("0\n")
                else:
                    f.write("0\n")
                    f.write("0\n")

# Writes the schedule to the schedule.txt file
def export_schedule(sched):
    with open("schedule.txt", "w") as f:
        for x in range(2):
            if x == 0:
                ampm = 'AM'
            else:
                ampm = 'PM'
            f.write(str(sched["1200"+ampm]) + "\n")
            f.write(str(sched["1230"+ampm]) + "\n")
            for i in range(1,12,1):
                if i < 10:
                    f.write(str(sched["0" + str(i) + "00" + ampm]) + "\n")
                    f.write(str(sched["0" + str(i) + "30" + ampm]) + "\n")
                else:
                    f.write(str(sched[str(i) + "00" + ampm]) + "\n")
                    f.write(str(sched[str(i) + "30" + ampm]) + "\n")

# Retrieves the schedule data from the schedule.txt file
def get_schedule():
    sched = {}
    with open("schedule.txt", "r") as f:
        for x in range(2):
            if x == 0:
                ampm = 'AM'
            else:
                ampm = 'PM'
            q = f.readline()
            if q == '0':
                sched["1200"+ampm] = 0
            else:
                sched["1200"+ampm] = 1
            q = f.readline()
            if q == '0':
                sched["1230"+ampm] = 0
            else:
                sched["1230"+ampm] = 0
            
            for i in range(1,12,1):
                if i < 10:
                    q = f.readline()
                    if q == '0':
                        sched["0" + str(i) + "00" + ampm] = 0
                        pop["0" + str(i) + "00" + ampm] = ""
                    else:
                        sched["0" + str(i) + "00" + ampm] = 1
                        pop["0" + str(i) + "00" + ampm] = "checked"
                    q = f.readline()
                    if q == '0':
                        sched["0" + str(i) + "30" + ampm] = 0
                        pop["0" + str(i) + "30" + ampm] = ""
                    else:
                        sched["0" + str(i) + "30" + ampm] = 1
                        pop["0" + str(i) + "30" + ampm] = "checked"
                else:
                    q = f.readline()
                    if q == '0':
                        sched[str(i) + "00" + ampm] = 0
                        pop[str(i) + "00" + ampm] = ""
                    else:
                        sched[str(i) + "00" + ampm] = 1
                        pop[str(i) + "00" + ampm] = "checked"
                    
                    q = f.readline()
                    if q == '0':
                        sched[str(i) + "30" + ampm] = 0
                        pop[str(i) + "30" + ampm] = ""
                    else:
                        sched[str(i) + "30" + ampm] = 1
                        pop[str(i) + "30" + ampm] = "checked"

    return sched

# Updates the schedule and webpage dictionaries base on the HTTP GET return
def update_schedule(request):
    request = request.split()
    request = request[1]
    if request.find("/action_page.php?") == 0:
        for time in sched.keys():
            if request.find(time) > 0:
                if request[int(request.find(time))+7:int(request.find(time))+9] == "on":
                    pop[time] = "checked"
                    sched[time] = 1
            else:
                pop[time] = ""
                sched[time] = 0

# HTML web page shown to the user
def ws_web_page():
    html_webpage = """<!DOCTYPE HTML><html>
    <head>
      <title>Electronic Pet Door</title>
      <center><h1>Electronic Pet Door</h1></center>
      <center><h2><small> Enter your network ID and password </small></h2></center>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <style>
      body {background-color: grey}
      #subbutt{
        background-color: blue;
        color: white;
        padding: 16px 32px;
        text-decoration: none;
        margin: 4px 2px;
        border: 0px solid black;
        border-radius: 18px;
        -moz-border-radius: 5px;
      }
      #closebutt{
        background-color: red;
        color: white;
        padding: 16px 32px;
        text-decoration: none;
        margin: 4px 2px;
        border: 0px solid black;
        border-radius: 8px;
        -moz-border-radius: 5px;
      }
      </style>
      
    </head>
    <body>
    
      <form action="/action_page.php" method="get">
      
      <title> AM <\title>
      <center>12:00 AM: <input type="checkbox" name=1200AM id=AM1200 """ + pop["1200AM"] + """> 6:00 AM: <input type="checkbox" name=0600AM id=AM0600 """ + pop["0600AM"] + """> 12:00 PM: <input type="checkbox" name=1200PM id=PM1200 """ + pop["1200PM"] + """> 6:00 PM: <input type="checkbox" name=0600PM id=PM0600 """ + pop["0600PM"] + """></center><br>
      <center>12:30 AM: <input type="checkbox" name=1230AM id=AM1230 """ + pop["1230AM"] + """> 6:30 AM: <input type="checkbox" name=0630AM id=AM0630 """ + pop["0630AM"] + """> 12:30 PM: <input type="checkbox" name=1230PM id=PM1230 """ + pop["1230PM"] + """> 6:30 PM: <input type="checkbox" name=0630PM id=PM0630 """ + pop["0630PM"] + """></center><br>
      <center>1:00 AM: <input type="checkbox" name=0100AM id=AM0100 """ + pop["0100AM"] + """> 7:00 AM: <input type="checkbox" name=0700AM id=AM0700 """ + pop["0700AM"] + """> 1:00 PM: <input type="checkbox" name=0100PM id=PM0100 """ + pop["0100PM"] + """> 7:00 PM: <input type="checkbox" name=0700PM id=PM0700 """ + pop["0700PM"] + """></center><br>
      <center>1:30 AM: <input type="checkbox" name=0130AM id=AM0130 """ + pop["0130AM"] + """> 7:30 AM: <input type="checkbox" name=0730AM id=AM0730 """ + pop["0730AM"] + """> 1:30 PM: <input type="checkbox" name=0130PM id=PM0130 """ + pop["0130PM"] + """> 7:30 PM: <input type="checkbox" name=0730PM id=PM0730 """ + pop["0730PM"] + """></center><br>
      <center>2:00 AM: <input type="checkbox" name=0200AM id=AM0200 """ + pop["0200AM"] + """> 8:00 AM: <input type="checkbox" name=0800AM id=AM0800 """ + pop["0800AM"] + """> 2:00 PM: <input type="checkbox" name=0200PM id=PM0200 """ + pop["0200PM"] + """> 8:00 PM: <input type="checkbox" name=0800PM id=PM0800 """ + pop["0800PM"] + """></center><br>
      <center>2:30 AM: <input type="checkbox" name=0230AM id=AM0230 """ + pop["0230AM"] + """> 8:30 AM: <input type="checkbox" name=0830AM id=AM0830 """ + pop["0830AM"] + """> 2:30 PM: <input type="checkbox" name=0230PM id=PM0230 """ + pop["0230PM"] + """> 8:30 PM: <input type="checkbox" name=0830PM id=PM0830 """ + pop["0830PM"] + """></center><br>
      <center>3:00 AM: <input type="checkbox" name=0300AM id=AM0300 """ + pop["0300AM"] + """> 9:00 AM: <input type="checkbox" name=0900AM id=AM0900 """ + pop["0900AM"] + """> 3:00 PM: <input type="checkbox" name=0300PM id=PM0300 """ + pop["0300PM"] + """> 9:00 PM: <input type="checkbox" name=0900PM id=PM0900 """ + pop["0900PM"] + """></center><br>
      <center>3:30 AM: <input type="checkbox" name=0330AM id=AM0330 """ + pop["0330AM"] + """> 9:30 AM: <input type="checkbox" name=0930AM id=AM0930 """ + pop["0930AM"] + """> 3:30 PM: <input type="checkbox" name=0330PM id=PM0330 """ + pop["0330PM"] + """> 9:30 PM: <input type="checkbox" name=0930PM id=PM0930 """ + pop["0930PM"] + """></center><br>
      <center>4:00 AM: <input type="checkbox" name=0400AM id=AM0400 """ + pop["0400AM"] + """> 10:00 AM: <input type="checkbox" name=1000AM id=AM1000 """ + pop["1000AM"] + """> 4:00 PM: <input type="checkbox" name=0400PM id=PM0400 """ + pop["0400PM"] + """> 10:00 PM: <input type="checkbox" name=1000PM id=PM1000 """ + pop["1000PM"] + """></center><br>
      <center>4:30 AM: <input type="checkbox" name=0430AM id=AM0430 """ + pop["0430AM"] + """> 10:30 AM: <input type="checkbox" name=1030AM id=AM1030 """ + pop["1030AM"] + """> 4:30 PM: <input type="checkbox" name=0430PM id=PM0430 """ + pop["0430PM"] + """> 10:30 PM: <input type="checkbox" name=1030PM id=PM1030 """ + pop["1030PM"] + """></center><br>
      <center>5:00 AM: <input type="checkbox" name=0500AM id=AM0500 """ + pop["0500AM"] + """> 11:00 AM: <input type="checkbox" name=1100AM id=AM1100 """ + pop["1100AM"] + """> 5:00 PM: <input type="checkbox" name=0500PM id=PM0500 """ + pop["0500PM"] + """> 11:00 PM: <input type="checkbox" name=1100PM id=PM1100 """ + pop["1100PM"] + """></center><br>
      <center>5:30 AM: <input type="checkbox" name=0530AM id=AM0530 """ + pop["0530AM"] + """> 11:30 AM: <input type="checkbox" name=1130AM id=AM1130 """ + pop["1130AM"] + """> 5:30 PM: <input type="checkbox" name=0530PM id=PM0530 """ + pop["0530PM"] + """> 11:30 PM: <input type="checkbox" name=1130PM id=PM1130 """ + pop["1130PM"] + """></center><br>

      <center>6:00 AM: <input type="checkbox" name=0600AM id=AM0600 """ + pop["0600AM"] + """></center><br>
      <center>6:30 AM: <input type="checkbox" name=0630AM id=AM0630 """ + pop["0630AM"] + """></center><br>
      <center>7:00 AM: <input type="checkbox" name=0700AM id=AM0700 """ + pop["0700AM"] + """></center><br>
      <center>7:30 AM: <input type="checkbox" name=0730AM id=AM0730 """ + pop["0730AM"] + """></center><br>
      <center>8:00 AM: <input type="checkbox" name=0800AM id=AM0800 """ + pop["0800AM"] + """></center><br>
      <center>8:30 AM: <input type="checkbox" name=0830AM id=AM0830 """ + pop["0830AM"] + """></center><br>
      <center>9:00 AM: <input type="checkbox" name=0900AM id=AM0900 """ + pop["0900AM"] + """></center><br>
      <center>9:30 AM: <input type="checkbox" name=0930AM id=AM0930 """ + pop["0930AM"] + """></center><br>
      <center>10:00 AM: <input type="checkbox" name=1000AM id=AM1000 """ + pop["1000AM"] + """></center><br>
      <center>10:30 AM: <input type="checkbox" name=1030AM id=AM1030 """ + pop["1030AM"] + """></center><br>
      <center>11:00 AM: <input type="checkbox" name=1100AM id=AM1100 """ + pop["1100AM"] + """></center><br>
      <center>11:30 AM: <input type="checkbox" name=1130AM id=AM1130 """ + pop["1130AM"] + """></center><br>
      <title> PM </title>
      <center>12:00 PM: <input type="checkbox" name=1200PM id=PM1200 """ + pop["1200PM"] + """></center><br>
      <center>12:30 PM: <input type="checkbox" name=1230PM id=PM1230 """ + pop["1230PM"] + """></center><br>
      <center>1:00 PM: <input type="checkbox" name=0100PM id=PM0100 """ + pop["0100PM"] + """></center><br>
      <center>1:30 PM: <input type="checkbox" name=0130PM id=PM0130 """ + pop["0130PM"] + """></center><br>
      <center>2:00 PM: <input type="checkbox" name=0200PM id=PM0200 """ + pop["0200PM"] + """></center><br>
      <center>2:30 PM: <input type="checkbox" name=0230PM id=PM0230 """ + pop["0230PM"] + """></center><br>
      <center>3:00 PM: <input type="checkbox" name=0300PM id=PM0300 """ + pop["0300PM"] + """></center><br>
      <center>3:30 PM: <input type="checkbox" name=0330PM id=PM0330 """ + pop["0330PM"] + """></center><br>
      <center>4:00 PM: <input type="checkbox" name=0400PM id=PM0400 """ + pop["0400PM"] + """></center><br>
      <center>4:30 PM: <input type="checkbox" name=0430PM id=PM0430 """ + pop["0430PM"] + """></center><br>
      <center>5:00 PM: <input type="checkbox" name=0500PM id=PM0500 """ + pop["0500PM"] + """></center><br>
      <center>5:30 PM: <input type="checkbox" name=0530PM id=PM0530 """ + pop["0530PM"] + """></center><br>

      <center>6:00 PM: <input type="checkbox" name=0600PM id=PM0600 """ + pop["0600PM"] + """></center><br>
      <center>6:30 PM: <input type="checkbox" name=0630PM id=PM0630 """ + pop["0630PM"] + """></center><br>
      <center>7:00 PM: <input type="checkbox" name=0700PM id=PM0700 """ + pop["0700PM"] + """></center><br>
      <center>7:30 PM: <input type="checkbox" name=0730PM id=PM0730 """ + pop["0730PM"] + """></center><br>
      <center>8:00 PM: <input type="checkbox" name=0800PM id=PM0800 """ + pop["0800PM"] + """></center><br>
      <center>8:30 PM: <input type="checkbox" name=0830PM id=PM0830 """ + pop["0830PM"] + """></center><br>
      <center>9:00 PM: <input type="checkbox" name=0900PM id=PM0900 """ + pop["0900PM"] + """></center><br>
      <center>9:30 PM: <input type="checkbox" name=0930PM id=PM0930 """ + pop["0930PM"] + """></center><br>
      <center>10:00 PM: <input type="checkbox" name=1000PM id=PM1000 """ + pop["1000PM"] + """></center><br>
      <center>10:30 PM: <input type="checkbox" name=1030PM id=PM1030 """ + pop["1030PM"] + """></center><br>
      <center>11:00 PM: <input type="checkbox" name=1100PM id=PM1100 """ + pop["1100PM"] + """></center><br>
      <center>11:30 PM: <input type="checkbox" name=1130PM id=PM1130 """ + pop["1130PM"] + """></center><br>

      <center><input type="submit" value="Submit" id="subbutt" name=submit> <input type="submit" value="Submit and Close" id="closebutt" name=closed></center>
    </form> <form action="/action_page.php" method="get"></form>
    </body>
    </html>"""
    return html_webpage

# Connects the ESP32 to the local network
def do_connect(wlan):
    with open("credentials.txt", "r") as creds:
        SSID = creds.readline()
        SSID = SSID[:-1]
        print(SSID)
        PASSWORD = creds.readline()
        print(PASSWORD)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            pass
    print('Oh Yes! Get connected')
    print('Connected to ' + SSID)
    print('IP Address: ', str(wlan.ifconfig()[0]))

# Main function of the web server:
# Calls do_connect() to set up the connection to the local network
# Sets up the socket and retrieves the schedule
# Requests and responds with the web page
# Gets the time from the internet and closes the connection
def web_server():
    gc.collect()
    wlan = network.WLAN(network.STA_IF)  
    do_connect(wlan)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 80))
    s.listen(5)
    sched = get_schedule()

    while True:
        with open("credentials.txt", "r") as creds:
            if creads.read == "":
                print("Reset button clicked.\n")
                break
        conn, addr = s.accept()
        print('Got a connection from %s' % str(addr))
        request = conn.recv(1024)
        request = str(request)
        update_schedule(request)
        print('Content = %s' % request)
        tempor = request.split()
        if tempor[1].find("closed=Submit+and+Close") > 0:
            ntptime.settime() #function to pass to external rtc
            rtc = RTC()
            with open("gottime.txt", "w") as gottime:
                gottime.write("1")
            printTime(rtc.datetime())
            export_schedule(sched)
            
            conn.close()
            print("Closing Web Server\n")
            break
        response = ws_web_page()
        conn.send('HTTP/1.1 200 OK\n')
        conn.send('Content-Type: text/html\n')
        conn.send('Connection: close\n\n')
        conn.sendall(response)
        
        conn.close()
            
    wlan.active(False)
    wlan.disconnect()
    s.close()
    gc.collect()


###################################
######## Main Function ############
###################################
    
def config_main():
    # First must figure out if there are WiFi credentials
    
    with open("credentials.txt", "r") as creds:
        if creds.read() == "":
            # Access Point mode
            access_point()
            
        else:
            # Web Server mode
            reset_button.irq(trigger=Pin.IRQ_RISING, handler=reset_credentials)
            web_server()


        


