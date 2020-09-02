from polyalphabetic_cipher import poly_alphabetic_encrypt_message, decrypt_aphabetic

file = open('message_to_encrypt.txt', 'r')
string =  ''
for x in file:
    string += poly_alphabetic_encrypt_message(x,'penguin')



file.close()

file1 = open('encrypted_message.txt', 'w')

file1.write(string)

file1.close()

file = open('encrypted_message.txt', 'r')

decrypted_string = ''

for word in file:
    decrypted_string += decrypt_aphabetic(word,'penguin')
    
file.close()

file = open('decrypted_message.txt', 'w')
file.write(decrypted_string)
file.close()