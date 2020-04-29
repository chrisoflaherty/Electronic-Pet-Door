import usocket as socket
import ure
import network
import esp32
import gc
import urequests
from time import sleep
import ntptime



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
    
      <form action="/" method="post">
      
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
    while True:
        try:
            s.bind(('', 80))
            print("Socket work.")
            break
        except:
            s.close()
            print("Socket no work. Retry.\n")
            return "oserror"
            
            gc.collect()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.listen(5)

    while True:
           try:
               conn, addr = s.accept()
               req = conn.readline()
           except KeyboardInterrupt:
               raise OSError('Interrupt')
           except Exception as e:
               print(e)
               return

           l = 0
           while True:
               h = conn.readline()
               if not h or h == b'\r\n':
                   break
               if 'Content-Length: ' in h:
                   try:
                       l = int(h[16:-2])
                       print ('Content Length is : ', l)
                   except:
                       continue

           if l :
               postquery = conn.read(l)
               postquery = str(postquery)
               postquery = postquery.split("&")
               USERNAME = postquery[0][7:]
               PASSWORD = postquery[1][9:-1]
               print(USERNAME)
               print(PASSWORD)
               conn.close()
               break
           response = ap_web_page()
           conn.send('HTTP/1.1 200 OK\n')
           conn.send('Content-Type: text/html\n')
           conn.send('Connection: close\n\n')
           conn.sendall(response)
           conn.close()

    # Closes connection
    ap.active(False)
    while ap.active() == True:
        pass
    sleep(5)
    s.close()
    gc.collect()
    # Greps the USERNAME and PASSWORD
    USERNAME = ure.sub("\+", " ", USERNAME)
    USERNAME = ure.sub("\%91", "\'", USERNAME)
    USERNAME = ure.sub("\%92", "\'", USERNAME)
    USERNAME = ure.sub("\%2B", "+", USERNAME)
    print(USERNAME)
    PASSWORD = ure.sub("\+", " ", PASSWORD)
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
            if q == '0\n':
                sched["1200"+ampm] = 0
                pop["1200"+ampm] = ""
            else:
                sched["1200"+ampm] = 1
                pop["1200"+ampm] = "checked"
            q = f.readline()
            if q == '0\n':
                sched["1230"+ampm] = 0
                pop["1230"+ampm] = ""
            else:
                sched["1230"+ampm] = 1
                pop["1230"+ampm] = "checked"
            
            for i in range(1,12,1):
                if i < 10:
                    q = f.readline()
                    if q == '0\n':
                        sched["0" + str(i) + "00" + ampm] = 0
                        pop["0" + str(i) + "00" + ampm] = ""
                    else:
                        sched["0" + str(i) + "00" + ampm] = 1
                        pop["0" + str(i) + "00" + ampm] = "checked"
                    q = f.readline()
                    if q == '0\n':
                        sched["0" + str(i) + "30" + ampm] = 0
                        pop["0" + str(i) + "30" + ampm] = ""
                    else:
                        sched["0" + str(i) + "30" + ampm] = 1
                        pop["0" + str(i) + "30" + ampm] = "checked"
                else:
                    q = f.readline()
                    if q == '0\n':
                        sched[str(i) + "00" + ampm] = 0
                        pop[str(i) + "00" + ampm] = ""
                    else:
                        sched[str(i) + "00" + ampm] = 1
                        pop[str(i) + "00" + ampm] = "checked"
                    
                    q = f.readline()
                    if q == '0\n':
                        sched[str(i) + "30" + ampm] = 0
                        pop[str(i) + "30" + ampm] = ""
                    else:
                        sched[str(i) + "30" + ampm] = 1
                        pop[str(i) + "30" + ampm] = "checked"

    return sched

# Updates the schedule and webpage dictionaries base on the HTTP GET return
def update_schedule(request, sched):
    for time in sched.keys():
        for r in request:
            if r[:6] == time:
                if r[7:] == "on":
                    pop[time] = "checked"
                    sched[time] = 1
                    break
            else:
                pop[time] = ""
                sched[time] = 0
        
            
    return sched

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
          /* Create two equal columns that floats next to each other */
          .column {
            float: left;
            width: 50%;
            padding: 10px;
          }

          /* Clear floats after the columns */
          .row:after {
            content: "";
            display: table;
            clear: both;
          }

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

        <div class="row">
          <div class="column">

          <center><font size=5><b><u>AM</u></b></font></center><br>
          <form action="/submit" method="post">
          <center>12:00 AM: <input type="checkbox" name=1200AM id=AM1200   """+ pop["1200AM"] + """></center><br>
          <center>12:30 AM: <input type="checkbox" name=1230AM id=AM1230   """+ pop["1230AM"] + """></center><br>
          <center>1:00 AM: <input type="checkbox" name=0100AM id=AM0100   """+ pop["0100AM"] + """></center><br>
          <center>1:30 AM: <input type="checkbox" name=0130AM id=AM0130   """+ pop["0130AM"] + """></center><br>
          <center>2:00 AM: <input type="checkbox" name=0200AM id=AM0200   """+ pop["0200AM"] + """></center><br>
          <center>2:30 AM: <input type="checkbox" name=0230AM id=AM0230   """+ pop["0230AM"] + """></center><br>
          <center>3:00 AM: <input type="checkbox" name=0300AM id=AM0300   """+ pop["0300AM"] + """></center><br>
          <center>3:30 AM: <input type="checkbox" name=0330AM id=AM0330   """+ pop["0330AM"] + """></center><br>
          <center>4:00 AM: <input type="checkbox" name=0400AM id=AM0400   """+ pop["0400AM"] + """></center><br>
          <center>4:30 AM: <input type="checkbox" name=0430AM id=AM0430   """+ pop["0430AM"] + """></center><br>
          <center>5:00 AM: <input type="checkbox" name=0500AM id=AM0500   """+ pop["0500AM"] + """></center><br>
          <center>5:30 AM: <input type="checkbox" name=0530AM id=AM0530   """+ pop["0530AM"] + """></center><br>

          <center>6:00 AM: <input type="checkbox" name=0600AM id=AM0600   """+ pop["0600AM"] + """></center><br>
          <center>6:30 AM: <input type="checkbox" name=0630AM id=AM0630   """+ pop["0630AM"] + """></center><br>
          <center>7:00 AM: <input type="checkbox" name=0700AM id=AM0700   """+ pop["0700AM"] + """></center><br>
          <center>7:30 AM: <input type="checkbox" name=0730AM id=AM0730   """+ pop["0730AM"] + """></center><br>
          <center>8:00 AM: <input type="checkbox" name=0800AM id=AM0800   """+ pop["0800AM"] + """></center><br>
          <center>8:30 AM: <input type="checkbox" name=0830AM id=AM0830   """+ pop["0830AM"] + """></center><br>
          <center>9:00 AM: <input type="checkbox" name=0900AM id=AM0900   """+ pop["0900AM"] + """></center><br>
          <center>9:30 AM: <input type="checkbox" name=0930AM id=AM0930   """+ pop["0930AM"] + """></center><br>
          <center>10:00 AM: <input type="checkbox" name=1000AM id=AM1000   """+ pop["1000AM"] + """></center><br>
          <center>10:30 AM: <input type="checkbox" name=1030AM id=AM1030   """+ pop["1030AM"] + """></center><br>
          <center>11:00 AM: <input type="checkbox" name=1100AM id=AM1100   """+ pop["1100AM"] + """></center><br>
          <center>11:30 AM: <input type="checkbox" name=1130AM id=AM1130   """+ pop["1130AM"] + """></center><br>

           </div>
          <center><font size=5><b><u>PM</u></b></font></center><br>
          <center>12:00 PM: <input type="checkbox" name=1200PM id=PM1200   """+ pop["1200PM"] + """></center><br>
          <center>12:30 PM: <input type="checkbox" name=1230PM id=PM1230   """+ pop["1230PM"] + """></center><br>
          <center>1:00 PM: <input type="checkbox" name=0100PM id=PM0100   """+ pop["0100PM"] + """></center><br>
          <center>1:30 PM: <input type="checkbox" name=0130PM id=PM0130   """+ pop["0130PM"] + """></center><br>
          <center>2:00 PM: <input type="checkbox" name=0200PM id=PM0200   """+ pop["0200PM"] + """></center><br>
          <center>2:30 PM: <input type="checkbox" name=0230PM id=PM0230   """+ pop["0230PM"] + """></center><br>
          <center>3:00 PM: <input type="checkbox" name=0300PM id=PM0300   """+ pop["0300PM"] + """></center><br>
          <center>3:30 PM: <input type="checkbox" name=0330PM id=PM0330   """+ pop["0330PM"] + """></center><br>
          <center>4:00 PM: <input type="checkbox" name=0400PM id=PM0400   """+ pop["0400PM"] + """></center><br>
          <center>4:30 PM: <input type="checkbox" name=0430PM id=PM0430   """+ pop["0430PM"] + """></center><br>
          <center>5:00 PM: <input type="checkbox" name=0500PM id=PM0500   """+ pop["0500PM"] + """></center><br>
          <center>5:30 PM: <input type="checkbox" name=0530PM id=PM0530   """+ pop["0530PM"] + """></center><br>

          <center>6:00 PM: <input type="checkbox" name=0600PM id=PM0600   """+ pop["0600PM"] + """></center><br>
          <center>6:30 PM: <input type="checkbox" name=0630PM id=PM0630   """+ pop["0630PM"] + """></center><br>
          <center>7:00 PM: <input type="checkbox" name=0700PM id=PM0700   """+ pop["0700PM"] + """></center><br>
          <center>7:30 PM: <input type="checkbox" name=0730PM id=PM0730   """+ pop["0730PM"] + """></center><br>
          <center>8:00 PM: <input type="checkbox" name=0800PM id=PM0800   """+ pop["0800PM"] + """></center><br>
          <center>8:30 PM: <input type="checkbox" name=0830PM id=PM0830   """+ pop["0830PM"] + """></center><br>
          <center>9:00 PM: <input type="checkbox" name=0900PM id=PM0900   """+ pop["0900PM"] + """></center><br>
          <center>9:30 PM: <input type="checkbox" name=0930PM id=PM0930   """+ pop["0930PM"] + """></center><br>
          <center>10:00 PM: <input type="checkbox" name=1000PM id=PM1000   """+ pop["1000PM"] + """></center><br>
          <center>10:30 PM: <input type="checkbox" name=1030PM id=PM1030   """+ pop["1030PM"] + """></center><br>
          <center>11:00 PM: <input type="checkbox" name=1100PM id=PM1100   """+ pop["1100PM"] + """></center><br>
          <center>11:30 PM: <input type="checkbox" name=1130PM id=PM1130   """+ pop["1130PM"] + """></center><br>

          
        </div>
          <center><input type="submit" value="Submit" id="subbutt" name=submit>
          <center><input type="submit" value="Save and Close" id="closebutt" name=closed></center>
        </form>

          
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
    sched = {}
    gc.collect()
    wlan = network.WLAN(network.STA_IF)
    do_connect(wlan)
    
    for x in range(5):
        try:
            ntptime.settime()
            print("NTP do work.\n")
            with open("gottime.txt", "w") as gottime:
                gottime.write("1")
            break
        except:
            with open("gottime.txt", "w") as gottime:
                gottime.write("0")
            sleep(5)
            print("NTP no work. Hold on trying again.\n")
    

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            s.bind(('', 80))
            print("Socket work.")
            break
        except:
            s.close()
            print("Socket no work. Retry.\n")
            return "oserror"
            
            gc.collect()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.listen(5)
    sched = get_schedule()

    while True:
           try:
               conn, addr = s.accept()
               req = conn.readline()
           except KeyboardInterrupt:
               raise OSError('Interrupt')
           except Exception as e:
               print(e)
               return

           l = 0
           while True:
               h = conn.readline()
               if not h or h == b'\r\n':
                   break
               if 'Content-Length: ' in h:
                   try:
                       l = int(h[16:-2])
                       print ('Content Length is : ', l)
                   except:
                       continue

           if l :
               postquery = conn.read(l)
               postquery = str(postquery)
               postquery = postquery[2:-1]
               print(postquery)
               postquery = postquery.split("&")
               print(postquery)
               sched = update_schedule(postquery, sched)
               if(postquery[-1] == 'closed=Save+and+Close'):
                   export_schedule(sched)
                   conn.close()
                   break
           response = ws_web_page()
           conn.send('HTTP/1.1 200 OK\n')
           conn.send('Content-Type: text/html\n')
           conn.send('Connection: close\n\n')
           try:
               conn.sendall(response)
           except:
               conn.close()
               
           conn.close()
            
    wlan.active(False)
    s.close()
    gc.collect()


def config_main():
    x = ""
    with open("credentials.txt", "r") as file:
        x = file.read()
    if x == "":
        while access_point() == "oserror":
            sleep(10)
        sleep(5)
    
    while web_server() == "oserror":
        sleep(10)
    
config_main()
