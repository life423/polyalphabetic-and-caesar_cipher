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



def poly_alphabetic_encrypt_message(message, keyword):
    '''
    Takes in a message and a code word and performs a polyalphabetic cipher on the message
    '''

    alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l',
                'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    keyword_shifts = [alphabet.index(char)+1 for char in keyword]
    string_to_list_before_encryption = [char for char in message if char != ' ']
    spaces_indexes = []
    final_encryption = []
    
    #gets the indexes of all the spaces 
    for i in range(len(message)):
        if message[i] == ' ':
            spaces_indexes.append(i)
    
    # makes sure the list of shifts is long enough for the message
    while len(keyword_shifts) < len(message):
        keyword_shifts.extend(keyword_shifts)
    
    for i in range(len(string_to_list_before_encryption)):
        #calls the caesar cipher function 
        final_encryption.append(encrypt_word(string_to_list_before_encryption[i], keyword_shifts[i]))

    # inserts the shifts back into the message at the appropriate index
    for i in range(len(spaces_indexes)):
        final_encryption.insert(spaces_indexes[i], ' ')

    encrypted_sentence = ('').join(final_encryption)
    return encrypted_sentence

    


# print(poly_alphabetic_encrypt_message('meet me at the store', 'turtle'))


def decrypt_aphabetic(message, keyword):
    '''
    takes in an encrypted message from the polyalphabetic function and uses a the keyword to decrypt the function
    '''
    alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l',
                'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    keyword_shifts = [alphabet.index(char)+1 for char in keyword]
    string_to_list_before_decryption = [char for char in message if char != ' ']
    
    spaces_indexes = []
    final_decryption = []
    
    #gets the indexes of all the spaces
    for i in range(len(message)):
        if message[i] == ' ':
            spaces_indexes.append(i)
            
    while len(keyword_shifts) < len(message):
        keyword_shifts.extend(keyword_shifts)
            
    for i in range(len(string_to_list_before_decryption)):
        #calls the caesar cipher decrypt function 
        final_decryption.append(decrypt_word(
            string_to_list_before_decryption[i], keyword_shifts[i]))
    
    # inserts the shifts back into the message at the appropriate index
    for i in range(len(spaces_indexes)):
        final_decryption.insert(spaces_indexes[i], ' ')
    
    decrypted_sentence = ('').join(final_decryption)
    return decrypted_sentence


# print(decrypt_aphabetic('gzwn yj uo lbq xnjjy', 'turtle'))
