# Caesar Cipher

def encrypt_word(word, shift):
    ''' 
    Encrypts a word using a Caesar cipher.
    
    Args:
    word (str): The word to be encrypted.
    shift (int): The number of positions each letter in the word should be shifted to the right in the alphabet.
    
    Returns:
    str: The encrypted word.
    '''

    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    encoded_message = [alphabet[(alphabet.index(c) + shift) % 26] if c.isalpha() else c for c in word]

    return ''.join(encoded_message)


def make_encrypted_sentence(string_to_encode, shift_to_right):
    '''
    Encrypts a sentence using a Caesar cipher.
    
    Args:
    string_to_encode (str): The sentence to be encrypted.
    shift_to_right (int): The number of positions each letter in the sentence should be shifted to the right in the alphabet.
    
    Returns:
    str: The encrypted sentence.
    '''

    encrypted_sentence = ' '.join([encrypt_word(word, shift_to_right) for word in string_to_encode.split()])

    return encrypted_sentence


def decrypt_word(word, key):
    '''
    Decrypts a word that was encrypted using a Caesar cipher.
    
    Args:
    word (str): The encrypted word.
    key (int): The decryption key.
    
    Returns:
    str: The decrypted word.
    '''

    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    decrypted_word = [alphabet[(alphabet.index(c) - key) % 26] if c.isalpha() else c for c in word]

    return ''.join(decrypted_word)


def decrypt_sentence(sentence, key):
    '''
    Decrypts a sentence that was encrypted using a Caesar cipher.
    
    Args:
    sentence (str): The encrypted sentence.
    key (int): The decryption key.
    
    Returns:
    str: The decrypted sentence.
    '''

    decrypted_sentence = ' '.join([decrypt_word(word, key) for word in sentence.split()])

    return decrypted_sentence


def poly_alphabetic_encrypt_message(message, keyword):
    '''
    Encrypts a message using a Polyalphabetic cipher.
    
    Args:
    message (str): The message to be encrypted.
    keyword (str): The keyword used for encryption.
    
    Returns:
    str: The encrypted message.
    '''

    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    keyword = (keyword * (len(message) // len(keyword) + 1)).lower()
    encrypted_message = []

    for m, k in zip(message, keyword):
        if m.isalpha():
            shift = alphabet.index(k)
            if m.isupper():
                encrypted_message.append(chr((ord(m) - 65 + shift) % 26 + 65))
            else:
                encrypted_message.append(chr((ord(m) - 97 + shift) % 26 + 97))
        else:
            encrypted_message.append(m)
            keyword = keyword[1:]  # shift the keyword for non-alphabet characters

    return ''.join(encrypted_message)


def decrypt_aphabetic(message, keyword):
    '''
    Decrypts a message that was encrypted using a Polyalphabetic cipher.
    
    Args:
    message (str): The encrypted message.
    keyword (str): The keyword used for decryption.
    
    Returns:
    str: The decrypted message.
    '''

    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    keyword = (keyword * (len(message) // len(keyword) + 1)).lower()
    decrypted_message = []

    for m, k in zip(message, keyword):
        if m.isalpha():
            shift = alphabet.index(k)
            if m.isupper():
                decrypted_message.append(chr((ord(m) - 65 - shift) % 26 + 65))
            else:
                decrypted_message.append(chr((ord(m) - 97 - shift) % 26 + 97))
        else:
            decrypted_message.append(m)
            keyword = keyword[1:]  # shift the keyword for non-alphabet characters

    return ''.join(decrypted_message)
