#Caeser Cipher

def encrypt_word(word, shift):
    ''' 
    Takes two parameters, first is the word to be encrypted and the second is 
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
        if shift + alphabet.index(list_to_encode[i]) >25:
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
        encrypted_sentence+= encrypt_word(word,shift_to_right) + ' '
    
    return encrypted_sentence


# print(make_encrypted_sentence('meet at the bridge', 7)) -> tlla ha aol iypknl

    





