# Caeser Cipher


def encrypt_word(word, shift):
    ''' 
    Takes two parameters, first is the word or letter to be encrypted and the second is 
    how many letters right in the alphabet to move each letter in the word
    '''

    alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l',
                'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    encoded_message = []
    starting_index_positions = []
    list_to_encode = [char for char in word]

    for i in range(len(word)):
        starting_index_positions.append(alphabet.index(list_to_encode[i]))
    shifted_index_positions = [num+shift for num in starting_index_positions]

    for i in range(len(list_to_encode)):
        if shift + alphabet.index(list_to_encode[i]) > 25:
            encoded_message.append(alphabet[shifted_index_positions[i]-26])
        else:
            encoded_message.append(alphabet[shifted_index_positions[i]])

    return ''.join(encoded_message)


def make_encrypted_sentence(string_to_encode, shift_to_right):
    '''
    Takes a sentence as the first parameter and the second parameter is how many letters each word in the setence should be shifted right
    '''
    split_string = string_to_encode.split(' ')
    encrypted_sentence = ''
    for word in split_string:
        encrypted_sentence += encrypt_word(word, shift_to_right) + ' '

    return encrypted_sentence


# print(make_encrypted_sentence('lets go to the store', 1))


def decrypt_word(word, key):
    '''
    Takes in an encrypted word and a key (as an integer) as parameters and decrypts a caesar cipher for one word
    '''
    alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l',
                'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    encrypted_indexes = []
    unencrypted_indexes = []

    for i in range(len(word)):
        encrypted_indexes.append(alphabet.index(word[i]))
        unencrypted_indexes.append(alphabet[encrypted_indexes[i]-key])

    return ''.join(unencrypted_indexes)


def decrypt_sentence(sentence, key):
    '''
    Takes in an encyrpted caesar cihper sentence and a key (which is a positive integer) and decrypts the sentence with the key
    '''
    decrypted_list = []
    split_string = sentence.split(' ')
    for word in split_string:
        decrypted_list.append(decrypt_word(word, key))

    return ' '.join(decrypted_list)


# print(decrypt_sentence('uncb px odlt xdcbrmn ', 9))

# Polyalphabetic Cipher
def poly_alphabetic_encrypt_message(message, keyword):
    '''
    This function takes a message and a keyword as inputs, 
    and returns the message encrypted using a Polyalphabetic cipher. 
    The function handles upper case letters and special characters.
    '''
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    keyword = (keyword * (len(message) // len(keyword) + 1)).lower()

    encrypted_message = ''.join([chr((ord(m) - 65 + alphabet.index(k)) % 26 + 65) if m.isupper() else 
                                 chr((ord(m) - 97 + alphabet.index(k)) % 26 + 97) if m.islower() else m 
                                 for m, k in zip(message, keyword)])

    return encrypted_message

    


# print(poly_alphabetic_encrypt_message('Meet me at the store.', 'turtle'))

def decrypt_aphabetic(message, keyword):
    '''
    This function takes an encrypted message and a keyword as inputs, 
    and returns the decrypted message using a Polyalphabetic cipher. 
    The function handles upper case letters, lower case letters, and special characters.
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



print(decrypt_aphabetic('fyvm qx rm xay lesky', 'turtle'))
