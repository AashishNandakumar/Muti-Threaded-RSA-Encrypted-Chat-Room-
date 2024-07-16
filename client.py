import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP


class Client:
    def init(self, host, port):
        self.send_button = None
        self.msg_entry = None
        self.chat_area = None
        self.window = None
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.username = "Guest"

        # Generate client's key pair
        self.private_key = RSA.generate(2048)
        self.public_key = self.private_key.publickey()
        self.server_public_key = None

        self.gui_init()

    def gui_init(self):
        self.window = tk.Tk()
        self.window.title("Zypher Chronicles Client")

        self.chat_area = scrolledtext.ScrolledText(
            self.window, wrap=tk.WORD, width=70, height=20
        )
        self.chat_area.pack(padx=10, pady=10)

        self.msg_entry = tk.Entry(self.window, width=85)
        self.msg_entry.pack(side=tk.LEFT, padx=10)

        self.send_button = tk.Button(
            self.window, text="Send", command=self.send_message
        )
        self.send_button.pack(side=tk.LEFT, padx=10)

        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Prompt for the username
        self.prompt_username()

    def prompt_username(self):
        dialog = tk.Toplevel(self.window)
        dialog.title("Username")
        dialog.geometry(
            "+{}+{}".format(
                self.window.winfo_rootx() + self.window.winfo_width() // 2 + 308,
                self.window.winfo_rooty() + self.window.winfo_height() // 2 + 225,
            )
        )

        tk.Label(dialog, text="Please enter your name:").pack(pady=20)
        entry = tk.Entry(dialog, width=40)
        entry.pack(pady=10)

        def on_submit():
            self.username = entry.get() or "Anonymous"
            dialog.destroy()

        submit_button = tk.Button(dialog, text="Submit", command=on_submit)
        submit_button.pack(pady=10)

        # Center the dialog window
        dialog.transient(self.window)
        dialog.grab_set()
        self.window.wait_window(dialog)  # Wait for the dialog to close

    def connect(self):
        try:
            self.client_socket.connect((self.host, self.port))
            self.log_message("Connected to server")

            # Exchange public keys
            self.client_socket.send(self.public_key.export_key())
            self.server_public_key = RSA.import_key(self.client_socket.recv(1024))

            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.start()
        except Exception as e:
            self.log_message(f"Error connecting to server: {e}")

    def send_message(self):
        message = self.msg_entry.get()
        if message:
            # Encrypt the message with the server's public key
            cipher = PKCS1_OAEP.new(self.server_public_key)
            encrypted_message = cipher.encrypt(message.encode())
            self.client_socket.send(encrypted_message)
            self.msg_entry.delete(0, tk.END)
            self.log_message(f"{self.username}: {message}")

    def receive_messages(self):
        while True:
            try:
                encrypted_message = self.client_socket.recv(1024)
                if not encrypted_message:
                    break

                # Decrypt the message
                cipher = PKCS1_OAEP.new(self.private_key)
                decrypted_message = cipher.decrypt(encrypted_message)

                self.log_message(f"Received: {decrypted_message.decode()}")
            finally:
                break
        self.client_socket.close()

    def log_message(self, message):
        self.chat_area.insert(tk.END, message + "\n")
        self.chat_area.see(tk.END)

    def on_closing(self):
        self.client_socket.close()
        self.window.destroy()

    def start(self):
        self.connect()
        self.window.mainloop()


if __name__ == "__main__":
    client = Client("192.168.11.112", 5000)
    client.start()
