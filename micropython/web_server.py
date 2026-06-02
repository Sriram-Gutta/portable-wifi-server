# Pico W portable wifi server
# brings up the Pico's own wifi network and serves a small html page on port 80
# you can turn the LED on or off, see the temperature, download a test pdf, or shut down

import network
import socket
import machine
import sys
from time import sleep
from tools import read_temperature

SSID = 'PicoW_Server'
PASSWORD = '12345678'

# the onboard LED is wired through the wifi chip on the Pico W
led = machine.Pin("LED", machine.Pin.OUT)


def start_ap():
    # start broadcasting our own wifi network
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=SSID, password=PASSWORD)
    ap.active(True)

    # wait up to 10 seconds for it to actually come up
    tries = 0
    while not ap.active() and tries < 10:
        sleep(1)
        tries += 1

    if not ap.active():
        print("AP did not start")
        sys.exit()

    ip = ap.ifconfig()[0]
    print(f"AP up at http://{ip}")
    return ip


def open_socket():
    # listen on port 80 for HTTP requests
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    return s


def build_page(temp, state):
    # the main html page the browser will show
    return f"""<!DOCTYPE html>
<html>
<head><title>Pico W</title></head>
<body>
<h1>Pico W Server</h1>
<form action="/lighton"><input type="submit" value="LED On"></form>
<form action="/lightoff"><input type="submit" value="LED Off"></form>
<form action="/pdf/test.pdf"><input type="submit" value="Test PDF"></form>
<form action="/close"><input type="submit" value="Shutdown"></form>
<p>LED: {state} | Temp: {temp:.2f}C</p>
</body>
</html>"""


def send_pdf(client, filename):
    # try to open the file - if it isn't there, send a 404 back
    try:
        f = open(filename, 'rb')
    except OSError:
        client.send(b'HTTP/1.0 404 Not Found\r\nContent-Type: text/html\r\n\r\n')
        client.send(b'<h1>404 - file not found</h1>')
        return

    # send the headers, then send the file 1024 bytes at a time
    client.send(b'HTTP/1.0 200 OK\r\nContent-Type: application/pdf\r\n\r\n')
    chunk = f.read(1024)
    while chunk:
        client.send(chunk)
        chunk = f.read(1024)
    f.close()


def serve(conn):
    state = 'OFF'
    led.off()

    while True:
        # wait for a browser to connect
        client, addr = conn.accept()

        try:
            # read what they sent - 1024 bytes is plenty for a GET request
            req = client.recv(1024).decode()
            # the first line looks like:  GET /lighton HTTP/1.1
            # we want the part between the first two spaces
            parts = req.split(' ')
            if len(parts) < 2:
                continue
            path = parts[1]
            # if there's a ?query at the end, cut it off
            if '?' in path:
                path = path.split('?')[0]

            print("request:", path)

            if path == '/favicon.ico':
                # browsers always ask for this, we don't have one
                client.send(b'HTTP/1.0 404 Not Found\r\n\r\n')
            elif path == '/lighton':
                led.on()
                state = 'ON'
                temp = read_temperature()
                client.send(b'HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\n')
                client.send(build_page(temp, state).encode())
            elif path == '/lightoff':
                led.off()
                state = 'OFF'
                temp = read_temperature()
                client.send(b'HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\n')
                client.send(build_page(temp, state).encode())
            elif path == '/close':
                client.send(b'HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\n')
                client.send(b'<html><body><h1>Shutting down...</h1></body></html>')
                client.close()
                break
            elif path.startswith('/pdf/'):
                # path looks like "/pdf/test.pdf" - cut off the "/pdf/" part
                filename = path[5:]
                send_pdf(client, filename)
            else:
                # anything else just shows the main page
                temp = read_temperature()
                client.send(b'HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\n')
                client.send(build_page(temp, state).encode())

        except Exception as e:
            print("error:", e)
        finally:
            client.close()

    conn.close()
    print("server stopped")


# main - start the AP and run the server until someone hits Shutdown
start_ap()
serve(open_socket())
