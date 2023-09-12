import os
import tkinter as tk
from tkinter import StringVar
from tkinter import filedialog 
from cipher_tool import caesar_cipher, poly_alphabetic_cipher, process_file 

root = tk.Tk()

# Title
title = tk.Label(root, text="Welcome to the Caesar and Polyalphabetic Cipher Tool!", font=('Helvetica', 16, 'bold'))
title.pack(pady=10)

# Cipher type option
cipher_label = tk.Label(root, text="Enter 'c' for Caesar cipher or 'p' for Polyalphabetic cipher: ")
cipher_label.pack()
cipher_entry = tk.Entry(root)
cipher_entry.pack()

# Encryption/Decryption option
action_label = tk.Label(root, text="Choose 'e' for encryption or 'd' for decryption: ")
action_label.pack()
action_entry = tk.Entry(root)
action_entry.pack()

# Keyword/Shift amount
keyword_label = tk.Label(root, text="Enter the keyword (for Polyalphabetic) or shift value (for Caesar): ")
keyword_label.pack()
keyword_entry = tk.Entry(root)
keyword_entry.pack()

# Text or file to be encrypted/decrypted
input_label = tk.Label(root, text="Enter the text or file path to be encrypted/decrypted: ")
input_label.pack()
input_entry = tk.Entry(root)
input_entry.pack()

# Output path or leave blank
output_label = tk.Label(root, text="Enter the file path to save the output or leave blank to display below: ")
output_label.pack()
output_entry = tk.Entry(root)
output_entry.pack()

result_label = tk.Label(root, text="Result: ")
result_label.pack()
result_text = tk.Text(root)
result_text.pack()

# Buttons
input_file_button = tk.Button(root, text="Select input file...", command=select_input_file)
input_file_button.pack()
output_file_button = tk.Button(root, text="Select output file...", command=select_output_file)
output_file_button.pack()
process_button = tk.Button(root, text="Process Text", command=process_text)
process_button.pack(pady=10)


def select_input_file():
    filename = tk.filedialog.askopenfilename()
    input_entry.delete(0, tk.END)
    input_entry.insert(0, filename)

def select_output_file():
    filename = tk.filedialog.asksaveasfilename()
    output_entry.delete(0, tk.END)
    output_entry.insert(0, filename)


input_file_button = tk.Button(root, text="Select input file...", command=select_input_file)
input_file_button.pack()
output_file_button = tk.Button(root, text="Select output file...", command=select_output_file)
output_file_button.pack()
process_button = tk.Button(root, text="Process Text", command=process_text)
process_button.pack(pady=10)

def process_text():
    result_text.delete('1.0', tk.END)
    # Retrieve input values
    action = action_entry.get()
    cipher_type = cipher_entry.get()
    keyword_shift = keyword_entry.get()
    input_data = input_entry.get()
    output_data = output_entry.get()

    # Validate inputs
    if not (action in {'e', 'd'} and cipher_type in {'c', 'p'} and keyword_shift and input_data):
        print("Invalid input. Please check all fields and try again.")
        return

    if cipher_type == 'c':
        shift = int(keyword_shift)
        # Check whether to perform encryption or decryption
        if action == 'e':
            if os.path.isfile(input_data):
                output = process_file(input_data, output_data, lambda x: caesar_cipher(x, shift)) if os.path.isfile(input_data) else caesar_cipher(input_data, shift)
            else:
                output = caesar_cipher(input_data, shift)
        elif action == 'd':
            if os.path.isfile(input_data):
                output = process_file(input_data, output_data, lambda x: caesar_cipher(x, shift, False)) if os.path.isfile(input_data) else caesar_cipher(input_data, shift, False)
            else:
                output = caesar_cipher(input_data, shift, False)
    elif cipher_type == 'p':
        keyword = keyword_shift
        # Check whether to perform encryption or decryption
        if action == 'e':
            if os.path.isfile(input_data):
                output = process_file(input_data, output_data, lambda x: poly_alphabetic_cipher(x, keyword)) if os.path.isfile(input_data) else poly_alphabetic_cipher(input_data, keyword)
            else:
                output = poly_alphabetic_cipher(input_data, keyword)
        elif action == 'd':
            if os.path.isfile(input_data):
                output = process_file(input_data, output_data, lambda x: poly_alphabetic_cipher(x, keyword, False)) if os.path.isfile(input_data) else poly_alphabetic_cipher(input_data, keyword, False)
            else:
                output = poly_alphabetic_cipher(input_data, keyword, False)

    result_text.insert(tk.END, output)

# Button to start processing
process_button = tk.Button(root, text="Process Text", command=process_text)
process_button.pack(pady=10)

root.mainloop()