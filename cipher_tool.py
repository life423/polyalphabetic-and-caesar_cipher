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

def main():
    # Interact with the user here
    choice = input("Enter 'e' for encryption or 'd' for decryption: ")
    if choice.lower() not in {'e', 'd'}:
        print("Invalid choice. Please enter 'e' for encryption or 'd' for decryption.")

    cipher_choice = input("Enter 'c' for Caesar cipher or 'p' for Polyalphabetic cipher: ")
    if cipher_choice.lower() not in {'c', 'p'}:
        print("Invalid choice. Please enter 'c' for Caesar cipher or 'p' for Polyalphabetic cipher.")

    if cipher_choice == 'c':
        shift = int(input("Please enter a shift value for the Caesar cipher: "))
        if choice == 'e':
            phrase = input("Please enter the phrase to encrypt: ")
            print(caesar_cipher(phrase, shift))
        if choice == 'd':
            phrase = input("Please enter the phrase to decrypt: ")
            print(caesar_cipher(phrase, shift, False))

    if cipher_choice == 'p':
        keyword = input("Please enter a keyword for the Polyalphabetic cipher: ")
        if choice == 'e':
            phrase = input("Please enter the phrase to encrypt: ")
            print(poly_alphabetic_cipher(phrase, keyword))
        if choice == 'd':
            phrase = input("Please enter the phrase to decrypt: ")
            print(poly_alphabetic_cipher(phrase, keyword, False))

if __name__ == "__main__":
    main()