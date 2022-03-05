import socket
import pyaudio
import threading

nickname = input("Choose your nickname: ")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(("127.0.0.1", 5000))
closed = False  # Flag that equals True if connection is closed
mode = 'keyboard'  # There are two modes of input: keyboard and record

chunk_size = 1024  # 512
audio_format = pyaudio.paInt16
channels = 1
rate = 20000

# initialise microphone recording
p = pyaudio.PyAudio()
playing_stream = p.open(
    format=audio_format, channels=channels, rate=rate, output=True, frames_per_buffer=chunk_size, start=True
)
recording_stream = p.open(
    format=audio_format, channels=channels, rate=rate, input=True, frames_per_buffer=chunk_size, start=False
)


def receive():
    global closed
    while True:
        if closed:
            exit(0)
        try:
            # Receive Message From Server
            data = client.recv(1024)

            if mode == "keyboard":
                message = data.decode("utf-8")
                if not message:
                    continue
                if message == "NICK":
                    # If 'NICK' Send Nickname
                    client.send(nickname.encode("utf-8"))
                else:
                    print(message)
        except UnicodeDecodeError:
            playing_stream.write(data)
        except:
            closed = True
            client.close()
            break


def write():
    global mode, closed
    while True:
        if closed:
            exit(0)
        msg_text = input('')
        if msg_text in ("/record", "/keyboard"):
            if msg_text == "/record":
                recording_stream.start_stream()
            else:
                recording_stream.stop_stream()
            mode = msg_text.replace("/", "")
            continue
        if msg_text and mode == "keyboard":
            message = f"{nickname}: {msg_text}"
            client.send(message.encode("utf-8"))
            if msg_text == "/exit":
                closed = True
                client.close()
                exit(0)


def record():
    global closed
    while True:
        if closed:
            exit(0)
        try:
            if mode == "record":
                data = recording_stream.read(1024)
                client.sendall(data)
        except:
            closed = True
            client.close()
            break


receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()

record_thread = threading.Thread(target=record)
record_thread.start()
