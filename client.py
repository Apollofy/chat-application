import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox
from datetime import datetime

class ChatClient:
    def __init__(self, host='127.0.0.1', port=5555):
        self.host = host
        self.port = port
        self.nickname = ""
        self.client_socket = None
        self.connected = False
        
        # Initialize GUI
        self.setup_gui()
        
    def setup_gui(self):
        """Create the GUI for the chat client"""
        self.root = tk.Tk()
        self.root.title("Chat Client")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Chat display area
        self.chat_frame = tk.Frame(self.root)
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.chat_area = scrolledtext.ScrolledText(self.chat_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.chat_area.pack(fill=tk.BOTH, expand=True)
        
        # Message input area
        self.message_frame = tk.Frame(self.root)
        self.message_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.message_entry = tk.Entry(self.message_frame)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.message_entry.bind("<Return>", self.send_message)
        self.message_entry.config(state=tk.DISABLED)  # Disabled until connected
        
        self.send_button = tk.Button(self.message_frame, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT, padx=5)
        self.send_button.config(state=tk.DISABLED)  # Disabled until connected
        
        # Connection controls
        self.conn_frame = tk.Frame(self.root)
        self.conn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.conn_button = tk.Button(self.conn_frame, text="Connect", command=self.toggle_connection)
        self.conn_button.pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Disconnected")
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def update_chat(self, message):
        """Update the chat area with a new message"""
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, message + "\n")
        self.chat_area.see(tk.END)  # Scroll to bottom
        self.chat_area.config(state=tk.DISABLED)
    
    def toggle_connection(self):
        """Connect to or disconnect from the server"""
        if self.connected:
            self.disconnect_from_server()
        else:
            self.connect_to_server()
    
    def connect_to_server(self):
        """Connect to the chat server"""
        try:
            # Ask for nickname
            self.nickname = simpledialog.askstring("Nickname", "Enter your nickname:", parent=self.root)
            if not self.nickname:
                return  # User cancelled
            
            # Create socket and connect
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            
            # Send nickname to server
            self.client_socket.send(self.nickname.encode('utf-8'))
            
            # Start receiving thread
            self.connected = True
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
            # Update UI
            self.conn_button.config(text="Disconnect")
            self.message_entry.config(state=tk.NORMAL)
            self.send_button.config(state=tk.NORMAL)
            self.status_var.set(f"Connected as {self.nickname}")
            
            self.update_chat(f"Connected to server at {self.host}:{self.port}")
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to server: {e}")
    
    def disconnect_from_server(self):
        """Disconnect from the chat server"""
        if self.connected:
            self.connected = False
            
            try:
                self.client_socket.close()
            except:
                pass
            
            # Update UI
            self.conn_button.config(text="Connect")
            self.message_entry.config(state=tk.DISABLED)
            self.send_button.config(state=tk.DISABLED)
            self.status_var.set("Disconnected")
            
            self.update_chat("Disconnected from server")
    
    def receive_messages(self):
        """Receive messages from the server"""
        while self.connected:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if message:
                    self.update_chat(message)
                else:
                    # Server closed connection
                    self.connected = False
                    self.update_chat("Lost connection to server")
                    self.conn_button.config(text="Connect")
                    self.message_entry.config(state=tk.DISABLED)
                    self.send_button.config(state=tk.DISABLED)
                    self.status_var.set("Disconnected")
                    break
            except:
                if self.connected:  # Only show error if we didn't disconnect intentionally
                    self.connected = False
                    self.update_chat("Connection to server lost")
                    self.conn_button.config(text="Connect")
                    self.message_entry.config(state=tk.DISABLED)
                    self.send_button.config(state=tk.DISABLED)
                    self.status_var.set("Disconnected")
                break
    
    def send_message(self, event=None):
        """Send a message to the server"""
        message = self.message_entry.get().strip()
        if message and self.connected:
            try:
                # Send message to server
                self.client_socket.send(message.encode('utf-8'))
                
                # Display my own message in the chat
                timestamp = datetime.now().strftime('%H:%M:%S')
                own_message = f"[{timestamp}] {self.nickname} (You): {message}"
                self.update_chat(own_message)
                
                # Clear input field
                self.message_entry.delete(0, tk.END)
            except:
                self.update_chat("Failed to send message")
                self.disconnect_from_server()
    
    def on_closing(self):
        """Handle window closing"""
        if self.connected:
            self.disconnect_from_server()
        self.root.destroy()
    
    def run(self):
        """Run the chat client"""
        self.root.mainloop()

if __name__ == "__main__":
    client = ChatClient()
    client.run()