import socket
import threading

HOST = '127.0.0.1'
PORT = 5000
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

connections = []
members = []
addresses = []
chatrooms = []
chat_num = 0


def broadcast(message, conn=None, chatroom=0):
    for i in range(len(connections)):
        if chatrooms[i] == chatroom and connections[i] != conn:
            connections[i].send(message)


def leave(connection):
    index = connections.index(connection)
    connections.remove(connection)
    addresses.pop(index)
    chatrooms.pop(index)
    connection.close()
    nickname = members[index]
    broadcast("{} left!".format(nickname).encode("utf-8"))
    members.remove(nickname)


def get_members(chatroom):
    msg = "Members of chat"
    if chatroom:
        msg = f"Members of \"{chatroom[1]}\""
    for i in range(len(members)):
        if chatrooms[i] == chatroom:
            msg += f"\n - {members[i]} {addresses[i]}"
    return msg


def handle_keyboard(data, conn, conn_index):
    global chat_num
    msg_text = data.decode("utf-8").split(": ")[1]
    if msg_text == "/exit":
        leave(conn)
        return 1
    elif msg_text == "/members":
        conn.send(get_members(chatrooms[conn_index]).encode("utf-8"))
    elif msg_text.startswith("/create_chat"):
        chat_title = msg_text.split(" ")[1]
        chat_num += 1
        chatrooms[conn_index] = (chat_num, chat_title)
        conn.send(
            f"Chatroom \"{chat_title}\" was created! You can invite "
            f"members with command /invite (member/members separated with by spaces)".encode("utf-8")
        )
    elif msg_text.startswith("/invite") and chatrooms[conn_index] != 0:
        invited_members = msg_text.split(" ")[1:]
        if not invited_members:
            conn.send("You haven't invited anyone".encode("utf-8"))
        for i in range(len(members)):
            if members[i] in invited_members and i != conn_index and chatrooms[i] == 0:
                chatrooms[i] = chatrooms[conn_index]
                connections[i].send(
                    f"You were invited to \"{chatrooms[conn_index][1]}\". "
                    f"If you want to leave this chatroom, use command /leave".encode("utf-8"))
    elif msg_text == "/leave" and chatrooms[conn_index] != 0:
        broadcast(f"{members[conn_index]} left this chatroom!".encode("utf-8"), conn, chatrooms[conn_index])
        chatrooms[conn_index] = 0
    elif msg_text == "/help":
        conn.send("Here is a list of commands:\n"
                  " - /members - get list of members of chatroom\n"
                  " - /exit - disconnect from server\n"
                  " - /create_chat {chat_title} - create a chatroom\n"
                  " - /invite - invite a member to the chatroom (only in created chatrooms)\n"
                  " - /leave - leave a chatroom (only in created chatrooms)\n"
                  " - /record - use microphone as source of input\n"
                  " - /keyboard - use keyboard as source of input".encode("utf-8"))
    elif msg_text.startswith("/"):
        conn.send("There is no such command. Use /help to get list of commands".encode("utf-8"))
    else:
        broadcast(data, conn, chatrooms[conn_index])


def handle_record(data, conn, conn_index):
    broadcast(data, conn, chatrooms[conn_index])


def handle(conn):
    global chat_num
    while True:
        try:
            # Handling requests
            data = conn.recv(1024)
            conn_index = connections.index(conn)
            ret = handle_keyboard(data, conn, conn_index)
            if ret:
                break
        except (UnicodeDecodeError, IndexError):
            handle_record(data, conn, conn_index)
        except:
            # Removing and closing connections
            leave(conn)
            break


def receive():
    while True:
        # Accept connection
        conn, address = server.accept()
        print("Connected with {}".format(str(address)))

        # Request and store nickname
        conn.send("NICK".encode("utf-8"))
        nickname = conn.recv(1024).decode("utf-8")
        members.append(nickname)
        connections.append(conn)
        addresses.append(address)
        chatrooms.append(0)

        # Print and broadcast nickname
        print("Nickname is {}".format(nickname))
        broadcast("{} joined!".format(nickname).encode("utf-8"))

        # Start handling thread for connection
        thread = threading.Thread(target=handle, args=(conn,))
        thread.start()


receive()
