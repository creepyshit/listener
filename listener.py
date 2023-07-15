import sys
import socket
import getopt
import threading
import subprocess

listen = False
command = False
upload = False
execute = ""
target = ""
upload_destination = ""
port = 0

def usage():
    print("NET TOOL")
    print()
    print("Usage: listener.py -t target_host -p port")
    print("-l --listen - listen on [host]:[port] for incoming connections")
    print("-e --execute=file_to_run - execute the given file upon receiving a connection")
    print("-c --command - initialize a command shell")
    print("-u --upload=destination - upon receiving connection upload a file and write to [destination]")
    sys.exit(0)

def main():
    global listen 
    global port
    global execute
    global command
    global upload_destination
    global target

    if not len(sys.argv[1:]):
        usage()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hle:t:p:cu:", ["help", "listen", "execute", "target", "port", "command", "upload"])
    except getopt.GetoptError as err:
        print(str(err))
        usage()

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
        elif opt in ("-l", "--listen"):
            listen = True
        elif opt in ("-e", "--execute"):
            execute = arg
        elif opt in ("-c", "--command"):
            command = True
        elif opt in ("-u", "--upload"):
            upload_destination = arg
        elif opt in ("-t", "--target"):
            target = arg
        elif opt in ("-p", "--port"):
            port = int(arg)
        else:
            assert False, "Unhandled Option"

    if not listen and len(target) and port > 0:
        buffer = sys.stdin.read()
        client_sender(buffer)

    if listen:
        server_loop()

def client_sender(buffer):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((target, port))

        if len(buffer):
            client.send(buffer.encode())

        while True:
            recv_len = 1
            response = ""

            while recv_len:
                data = client.recv(4096)
                recv_len = len(data)
                response += data.decode()

                if recv_len < 4096:
                    break

            print(response, end="")

            buffer = input("")
            buffer += "\n"
            client.send(buffer.encode())

    except Exception as e:
        print("[*] Exception! Exiting.", str(e))
        client.close()

def server_loop():
    global target

    if not len(target):
        target = "0.0.0.0"

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))
    server.listen(5)

    while True:
        client_socket, addr = server.accept()
        client_thread = threading.Thread(target=client_handler, args=(client_socket,))
        client_thread.start()

def run_command(command):
    command = command.rstrip()
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        return output.decode()
    except subprocess.CalledProcessError as e:
        return "Failed to execute command. " + str(e.output.decode())

def client_handler(client_socket):
    global upload_destination
    global execute
    global command

    if len(upload_destination):
        file_buffer = b""
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            file_buffer += data

        try:
            with open(upload_destination, "wb") as file_descriptor:
                file_descriptor.write(file_buffer)
            client_socket.send(b"Successfully saved file to {}\r\n".format(upload_destination).encode())
        except Exception as e:
            client_socket.send(b"Failed to save file to {}: {}\r\n".format(upload_destination, str(e)).encode())

    if len(execute):
        output = run_command(execute)
        client_socket.send(output.encode())

    if command:
        while True:
            client_socket.send(b"<NT:#> ")
            cmd_buffer = b""
            while b"\n" not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024)
            response = run_command(cmd_buffer.decode())
            client_socket.send(response.encode())

if __name__ == "__main__":
    main()