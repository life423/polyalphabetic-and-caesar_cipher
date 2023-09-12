import tkinter as tk
from tkinter import StringVar

root = tk.Tk()

# Title
title = tk.Label(root, text="Welcome to the Caesar and Polyalphabetic Cipher Tool!", font=('Helvetica', 16, 'bold'))
title.pack(pady=10)

# Encryption/Decryption option
action_label = tk.Label(root, text="Choose 'e' for encryption or 'd' for decryption: ")
action_label.pack()
action_entry = tk.Entry(root)
action_entry.pack()

# Cipher type option
cipher_label = tk.Label(root, text="Enter 'c' for Caesar cipher or 'p' for Polyalphabetic cipher: ")
cipher_label.pack()
cipher_entry = tk.Entry(root)
cipher_entry.pack()

# Keyword/Shift amount
keyword_label = tk.Label(root, text="Enter the keyword (for Polyalphabetic) or shift value (for Caesar): ")
keyword_label.pack()
keyword_entry = tk.Entry(root)
keyword_entry.pack()

# Text to be encrypted/decrypted
text_label = tk.Label(root, text="Enter the text to be encrypted/decrypted: ")
text_label.pack()
text_entry = tk.Entry(root)
text_entry.pack()

root.mainloop()