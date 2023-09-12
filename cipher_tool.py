import os
def caesar_cipher(sentence, shift, encrypt=True):
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    shifted_sentence = ''
    for char in sentence:
        if char.isalpha():  # Check if character is an alphabet
            offset = 65 if char.isupper() else 97
            new_index = (ord(char) - offset + shift) % 26
            if not encrypt:
                new_index = (ord(char) - offset - shift) % 26
            shifted_char = chr(new_index + offset)
            shifted_sentence += shifted_char
        else:
            shifted_sentence += char  # Non-alphabet characters are added as it is
    return shifted_sentence

def poly_alphabetic_cipher(message, keyword, encrypt=True):
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    keyword = (keyword * (len(message) // len(keyword) + 1)).lower()
    result_message = []

    for m, k in zip(message, keyword):
        if m.isalpha():
            shift = alphabet.index(k)
            if m.isupper():
                if not encrypt:
                    shift = -shift
                result_message.append(chr((ord(m) - 65 + shift) % 26 + 65))
            else:
                if not encrypt:
                    shift = -shift
                result_message.append(chr((ord(m) - 97 + shift) % 26 + 97))
        else:
            result_message.append(m)
            keyword = keyword[1:]  # shift the keyword for non-alphabet characters

    return ''.join(result_message)

def process_file(infile, outfile, cipher_function):
    try:
        with open(infile, 'r') as file, open(outfile, 'w') as file1:
            for x in file:
                file1.write(cipher_function(x))
        # After successful encryption/decryption, delete the infile
        os.remove(infile)
    except FileNotFoundError:
        print(f'The file {infile} does not exist.')
    except Exception as e:
        print(f"Couldn't process the file due to {str(e)}")

def delete_txt_files():
    files_in_dir = os.listdir()
    txt_files = [file for file in files_in_dir if file.endswith(".txt")]

    for file in txt_files:
        os.remove(file)

def main():
    cleanup_confirm = input("Would you like to delete all .txt files from current directory before proceeding? (yes/no): ")
    if cleanup_confirm.lower() == 'yes':
        delete_txt_files()

    # Rest of main function follows...
    choice = input("Enter 'e' for encryption or 'd' for decryption: ")
    if choice.lower() not in {'e', 'd'}:
        print("Invalid choice. Please enter 'e' for encryption or 'd' for decryption.")
        
    cipher_choice = input("Enter 'c' for Caesar cipher or 'p' for Polyalphabetic cipher: ")
    if cipher_choice.lower() not in {'c', 'p'}:
        print("Invalid choice. Please enter 'c' for Caesar cipher or 'p' for Polyalphabetic cipher.")
        
    source = input("Do you want to (1) enter a phrase or (2) use a text file? (Enter 1 or 2): ")
    if source not in {'1', '2'}:
        print("Invalid choice. Please enter '1' to input a phrase or '2' to use a text file.")
    elif source == '1':
        # Handle phrase input
        phrase = input("Please enter the phrase: ")
        if cipher_choice == 'c':
            shift = int(input("Please enter a shift value for the Caesar cipher: "))
            if choice == 'e':
                print(caesar_cipher(phrase, shift))
            if choice == 'd':
                print(caesar_cipher(phrase, shift, False))
        if cipher_choice == 'p':
            keyword = input("Please enter a keyword for the Polyalphabetic cipher: ")
            if choice == 'e':
                print(poly_alphabetic_cipher(phrase, keyword))
            if choice == 'd':
                print(poly_alphabetic_cipher(phrase, keyword, False))
    elif source == '2':
        # Handle text file input
        infile = input("Please input the path to the file to read from: ")
        outfile = input("Please input the path to the file to write to: ")
        if cipher_choice == 'c':
            shift = int(input("Please enter a shift value for the Caesar cipher: "))
            if choice == 'e':
                process_file(infile, outfile, lambda x: caesar_cipher(x, shift))
            if choice == 'd':
                process_file(infile, outfile, lambda x: caesar_cipher(x, shift, False))
        if cipher_choice == 'p':
            keyword = input("Please enter a keyword for the Polyalphabetic cipher: ")
            if choice == 'e':
                process_file(infile, outfile, lambda x: poly_alphabetic_cipher(x, keyword))
            if choice == 'd':
                process_file(infile, outfile, lambda x: poly_alphabetic_cipher(x, keyword, False))              
if __name__ == "__main__":
    main()