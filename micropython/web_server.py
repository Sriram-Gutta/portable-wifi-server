import network, socket, machine, sys
from time import sleep
from tools import read_temperature

SSID = 'PicoW_Server'
PASSWORD = '12345678'

led = machine.Pin("LED", machine.Pin.OUT)

def start_ap():
    # Configure and start the access point
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=SSID, password=PASSWORD)
    ap.active(True)

    # Wait up to 10 seconds for it to come up
    for _ in range(10):
        if ap.active():
            break
        sleep(1)
    else:
        print("AP failed to start")
        sys.exit()

    ip = ap.ifconfig()[0]
    print(f"AP up at http://{ip}")
    return ip

def open_socket():
    # Binds to port 80 and start listening
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    return s

def webpage(temp, state):
    # Builds and return the HTML status page which user interacts with
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

def serve(conn):
    state = 'OFF'
    led.off()

    while True:
        client, addr = conn.accept()
        try:
            # Parse the request path
            req = client.recv(1024).decode()
            path = req.split(' ')[1].split('?')[0]

            if path == '/favicon.ico':
                continue

            # Handle LED and shutdown routes
            if path == '/lighton':
                led.on()
                state = 'ON'
            elif path == '/lightoff':
                led.off()
                state = 'OFF'
            elif path == '/close':
                client.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
                client.send(b"<html><body><h1>Shutting down...</h1></body></html>")
                client.close()
                break
            elif path.startswith('/pdf/'):
                # Serve the requested PDF file in chunks
                try:
                    with open(path.lstrip('/'), 'rb') as f:
                        client.send('HTTP/1.0 200 OK\r\nContent-Type: application/pdf\r\n\r\n')
                        while chunk := f.read(1024):
                            client.send(chunk)
                except OSError:
                    client.send('HTTP/1.0 404 Not Found\r\nContent-Type: text/html\r\n\r\n')
                    client.send(b"<h1>404</h1>")
                client.close()
                continue

            # Send the main status page
            temp = read_temperature()
            client.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
            client.send(webpage(temp, state).encode())

        except Exception as e:
            print("err:", e)
        finally:
            client.close()

    conn.close()

# Execution part of the web_server file
# Start the AP and continue to the server loop
start_ap()
serve(open_socket())