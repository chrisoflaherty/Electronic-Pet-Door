# Access Point
# Christopher O'Flaherty

import usocket as socket
import ure
import network
import esp32
import gc
import urequests
import ujson

# HTML web page the user will see
def web_page():
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
        response = web_page()
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
    USERNAME = ure.sub("\+", " ", USERNAME)
    PASSWORD = ure.sub("\+", " ", PASSWORD)
    print("Username= " + USERNAME + "\nPassword= " + PASSWORD)

    # Write the USERNAME and PASSWORD to the file
    with open("credentials.txt", "w") as file:
        file.write(USERNAME)
        file.write("\n")
        file.write(PASSWORD)
        
    gc.collect()
