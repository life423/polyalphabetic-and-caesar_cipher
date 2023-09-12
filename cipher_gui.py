import tkinter as tk
from tkinter import StringVar
from cipher_tool import caesar_cipher, poly_alphabetic_cipher, process_file 

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

result_label = tk.Label(root, text="Result: ")
result_label.pack()

result_text = tk.Text(root)
result_text.pack()

def process_text():
    result_text.delete('1.0', tk.END)
    # Retrieve input values
    action = action_entry.get()
    cipher_type = cipher_entry.get()
    keyword_shift = keyword_entry.get()
    text = text_entry.get()

    # Validate inputs
    if not (action in {'e', 'd'} and cipher_type in {'c', 'p'} and keyword_shift and text):
        print("Invalid input. Please check all fields and try again.")
        return

    # Execute the selected cipher and operation
    encrypted_decrypted_text = ''
    if cipher_type == 'c':
        shift = int(keyword_shift)
        # Check whether to perform encryption or decryption
        if action == 'e':
            encrypted_decrypted_text = caesar_cipher(text, shift)
        elif action == 'd':
            encrypted_decrypted_text = caesar_cipher(text, shift, False)
    elif cipher_type == 'p':
        keyword = keyword_shift
        # Check whether to perform encryption or decryption
        if action == 'e':
            encrypted_decrypted_text = poly_alphabetic_cipher(text, keyword)
        elif action == 'd':
            encrypted_decrypted_text = poly_alphabetic_cipher(text, keyword, False)

    # Print the result
    result_text.insert(tk.END, encrypted_decrypted_text)

# Button to start processing
process_button = tk.Button(root, text="Process Text", command=process_text)
process_button.pack(pady=10)

root.mainloop()