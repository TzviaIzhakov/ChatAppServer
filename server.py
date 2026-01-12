import socket
import threading

# Server Configuration
SERVER_IP = '127.0.0.1'
SERVER_PORT = 65432

# Dictionary to store connected clients: {username: socket_object}
# Renamed to active_users_map for clarity.
active_users_map = {}

# Lock object to ensure synchronization between threads when accessing the map.
map_access_lock = threading.Lock()


def handle_client_connection(sender_socket, sender_address):
    """
    Manages the lifecycle of a single client connection.
    Handles message routing from the sender to the specific recipient.
    """
    sender_name = None
    try:
        # Edge Case: Username validation and duplication check
        while True:
            sender_name = sender_socket.recv(1024).decode('utf-8').strip()

            with map_access_lock:
                if sender_name in active_users_map:
                    sender_socket.send("ERROR:Username already taken. Try another:".encode('utf-8'))
                else:
                    active_users_map[sender_name] = sender_socket
                    sender_socket.send("OK:Welcome!".encode('utf-8'))
                    break

        print(f"[LOG] User '{sender_name}' joined from {sender_address}")

        # Main communication loop.
        while True:
            # Receive raw data from the client.
            raw_incoming_data = sender_socket.recv(1024).decode('utf-8')

            # If no data is received, the client likely disconnected.
            #?????
            if not raw_incoming_data:
                break
            #?????

            # The protocol expects the format "user_name:message_content".
            if ":" in raw_incoming_data:
                user_name, message_content = raw_incoming_data.split(":", 1)
                user_name = user_name.strip()
                message_content = message_content.strip()

                # Route the message to the recipient.
                with map_access_lock:
                    if user_name in active_users_map:
                        recipient_socket = active_users_map[user_name]
                        try:
                            # Construct the final message for the recipient.
                            formatted_message = f"From {sender_name}: {message_content}"
                            recipient_socket.send(formatted_message.encode('utf-8'))
                        except Exception as e:
                            print(f"[ERROR] Failed to forward message to {user_name}: {e}")
                    else:
                        # Notify the sender if the recipient is not found.
                        error_msg = f"System: User '{user_name}' is not currently online."
                        sender_socket.send(error_msg.encode('utf-8'))
    #?????????????
    except (ConnectionResetError, BrokenPipeError):
        print(f"[LOG] Connection lost with {sender_name}")
    #???????????
    except Exception as e:
        print(f"[ERROR] Connection issue with {sender_name if sender_name else sender_address}: {e}")
    finally:
        #Cleanup resources when the client disconnects.
        with map_access_lock:
            if sender_name in active_users_map:
                del active_users_map[sender_name]
        sender_socket.close()
        print(f"[LOG] User '{sender_name}' has disconnected.")


def start_server():
    """
    Initializes the server socket and listens for incoming connections.
    """
    # Create a TCP/IP socket.
    server_listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Allow immediate reuse of the port after server restart.
    server_listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_listener.bind((SERVER_IP, SERVER_PORT))
        server_listener.listen(5)
        print(f"Server is running and listening on {SERVER_IP}:{SERVER_PORT}...")

        while True:
            # Accept a new connection.
            new_client_socket, client_address = server_listener.accept()

            # Create a dedicated thread for the new client.
            client_handler_thread = threading.Thread(
                target=handle_client_connection,
                args=(new_client_socket, client_address)
            )
            # Set as daemon so it closes when the main thread exits.
            #????
            client_handler_thread.daemon = True
            #?????
            client_handler_thread.start()

    #??????
    except KeyboardInterrupt:
        print("\n[SYSTEM] Server shutting down manually.")
    #??????
    except Exception as e:
        print(f"[SYSTEM] Fatal server error: {e}")
    finally:
        server_listener.close()


if __name__ == "__main__":
    start_server()