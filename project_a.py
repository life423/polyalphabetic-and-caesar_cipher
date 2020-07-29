#Caeser Cipher


alphabet = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
 
# print(alphabet)
def encrypt(string, shift):
    encoded_message = []
    starting_index_positions = []
    list_to_encode = [char for char in string]
    
    for i in range(len(string)):
        starting_index_positions.append(alphabet.index(list_to_encode[i]))
    shifted_index_positions = [num+shift for num in starting_index_positions]
    for i in range(len(list_to_encode)):
        if shift + alphabet.index(list_to_encode[i]) >25:
            encoded_message.append(alphabet[shifted_index_positions[i]-26])
        else:
            encoded_message.append(alphabet[shifted_index_positions[i]])
        
        
            
    return ''.join(encoded_message)
    
    
    
    
print(encrypt('xyz',1)) 




