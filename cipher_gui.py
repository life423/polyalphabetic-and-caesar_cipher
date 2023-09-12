import tkinter as tk
from cipher_tool import caesar_cipher, poly_alphabetic_cipher, process_file

root = tk.Tk()

# Create an informative label
info_label = tk.Label(root, text="Welcome to the Caesar and Polyalphabetic Cipher Tool!")
info_label.pack()  # Place the label onto the window

def clicked():
    # What happens when the button is clicked
    print('Button clicked!')

click_me_button = tk.Button(root, text="Click me!", command=clicked)
click_me_button.pack()  # Place the button onto the window

root.mainloop()