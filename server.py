# Server.py
import socket
import threading
import time
from datetime import datetime

class ChatServer:
    def __init__(self, host='127.0.0.1', port=5555):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.clients = {}  # socket: nickname
        
    def broadcast(self, message, sender_socket=None):
        """Send message to all connected clients except the sender"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # If the message is from a client (not a system message)
        if sender_socket and sender_socket in self.clients:
            sender_name = self.clients[sender_socket]
            formatted_message = f"[{timestamp}] {sender_name}: {message}"
        else:
            formatted_message = f"[{timestamp}] {message}"
            
        print(f"Broadcasting: {formatted_message}")
        
        # List of clients to remove after broadcasting
        clients_to_remove = []
        
        # Send to all clients
        for client_socket, nickname in list(self.clients.items()):
            # Don't send message back to the sender
            if client_socket != sender_socket:
                try:
                    client_socket.send(formatted_message.encode('utf-8'))
                except:
                    # Mark for removal but don't modify dictionary during iteration
                    clients_to_remove.append(client_socket)
        
        # Now remove any failed clients
        for client_socket in clients_to_remove:
            self._remove_client(client_socket)
                
    def _remove_client(self, client_socket):
        """Internal method to remove a client"""
        if client_socket in self.clients:
            nickname = self.clients[client_socket]
            print(f"Removing client: {nickname}")
            del self.clients[client_socket]
            try:
                client_socket.close()
            except:
                pass
            
            # Notify others that a client left
            # We don't pass the socket to broadcast since it's already removed
            self.broadcast(f"{nickname} left the chat")
            
    def handle_client(self, client_socket, address):
        """Handle a client connection"""
        try:
            # Get nickname
            nickname = client_socket.recv(1024).decode('utf-8')
            
            # Store client information
            self.clients[client_socket] = nickname
            print(f"New client connected: {nickname} from {address}")
            
            # Welcome the client
            welcome = f"Welcome to the chat, {nickname}!"
            client_socket.send(welcome.encode('utf-8'))
            
            # Announce the new client to others
            self.broadcast(f"{nickname} joined the chat")
            
            # Process client messages
            while True:
                try:
                    message = client_socket.recv(1024).decode('utf-8')
                    if message:
                        print(f"Message from {nickname}: {message}")
                        self.broadcast(message, client_socket)
                    else:
                        # Client disconnected
                        break
                except:
                    # Connection error
                    break
                    
        except Exception as e:
            print(f"Error handling client {address}: {e}")
        
        # Clean up when the client leaves
        self._remove_client(client_socket)
            
    def start(self):
        """Start the server"""
        self.server_socket.listen(5)
        print(f"Server started on {self.host}:{self.port}")
        
        try:
            while True:
                # Accept client connections
                client_socket, address = self.server_socket.accept()
                print(f"New connection from {address}")
                
                # Start a thread to handle this client
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
                
        except KeyboardInterrupt:
            print("Server shutting down...")
        finally:
            # Close the server socket
            for client_socket in list(self.clients.keys()):
                try:
                    client_socket.close()
                except:
                    pass
            self.server_socket.close()
            print("Server closed")
            
if __name__ == "__main__":
    server = ChatServer()
    server.start()
