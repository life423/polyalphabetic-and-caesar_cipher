"""Interactive CipherCraft CLI: presentation only; cipher operations live in CipherService."""

from src.services.cipher_service import CipherService


# CLI interface implementation
def main():
    """
    Command-line interface for the cipher tool.
    Run this function when the script is executed directly.
    """
    service = CipherService()
    
    print("Welcome to the Cipher Tool CLI")
    print("==============================")
    
    # Get encryption or decryption choice
    choice = input("Choose operation (e=encrypt, d=decrypt): ")
    if choice.lower() not in {'e', 'd'}:
        print("Invalid choice. Please enter 'e' for encryption or 'd' for decryption.")
        return
    
    encrypt = choice.lower() == 'e'
    
    # Get cipher type choice
    print("\nAvailable ciphers:")
    print("c - Caesar")
    print("p - Polyalphabetic (Vigenère)")
    print("s - Substitution")
    print("t - Transposition")
    print("r - Rail Fence")
    print("a - Affine")
    
    cipher_choice = input("\nChoose cipher type: ")
    if cipher_choice.lower() not in {'c', 'p', 's', 't', 'r', 'a'}:
        print("Invalid choice. Please select a valid cipher type.")
        return
    
    # Get input source (text or file)
    source = input("Input source: (1=text, 2=file): ")
    if source not in {'1', '2'}:
        print("Invalid choice. Please enter '1' for text input or '2' for file input.")
        return
    
    # Process based on user choices
    if source == '1':  # Direct text input
        text = input("Enter text: ")
        
        if cipher_choice.lower() == 'c':  # Caesar cipher
            try:
                shift = int(input("Enter shift value (1-25): "))
                if encrypt:
                    result = service.encrypt_caesar(text, shift)
                else:
                    result = service.decrypt_caesar(text, shift)
                print(f"Result: {result}")
            except ValueError:
                print("Error: Shift value must be an integer.")
                
        elif cipher_choice.lower() == 'p':  # Polyalphabetic cipher
            keyword = input("Enter keyword: ")
            if not keyword:
                print("Error: Keyword cannot be empty.")
                return
                
            if encrypt:
                result = service.encrypt_polyalphabetic(text, keyword)
            else:
                result = service.decrypt_polyalphabetic(text, keyword)
            print(f"Result: {result}")
            
        elif cipher_choice.lower() == 's':  # Substitution cipher
            if encrypt:
                use_random = input("Generate random key? (yes/no): ").lower() == 'yes'
                if use_random:
                    seed_prompt = "Enter seed (optional, press Enter to skip): "
                    seed = input(seed_prompt) or None
                    key = service.generate_substitution_key(seed)
                    print(f"Generated key: {key}")
                else:
                    key = input("Enter 26-character substitution key: ")
                    if len(key) != 26:
                        print("Error: Key must be exactly 26 characters long.")
                        return
                result = service.encrypt_substitution(text, key)
            else:
                key = input("Enter 26-character substitution key: ")
                if len(key) != 26:
                    print("Error: Key must be exactly 26 characters long.")
                    return
                result = service.decrypt_substitution(text, key)
            print(f"Result: {result}")
            
        elif cipher_choice.lower() == 't':  # Transposition cipher
            key_prompt = "Enter transposition key (word or comma-separated numbers): "
            key = input(key_prompt)
            if ',' in key:
                # Handle numeric key format
                try:
                    key = [int(k.strip()) for k in key.split(',')]
                except ValueError:
                    print("Error: Numeric key must contain only integers.")
                    return
            
            if encrypt:
                result = service.encrypt_transposition(text, key)
            else:
                result = service.decrypt_transposition(text, key)
            print(f"Result: {result}")
            
        elif cipher_choice.lower() == 'r':  # Rail Fence cipher
            try:
                rails = int(input("Enter number of rails (2 or more): "))
                if rails < 2:
                    print("Error: Number of rails must be at least 2.")
                    return
                
                if encrypt:
                    result = service.encrypt_rail_fence(text, rails)
                else:
                    result = service.decrypt_rail_fence(text, rails)
                print(f"Result: {result}")
            except ValueError:
                print("Error: Number of rails must be an integer.")
                
        elif cipher_choice.lower() == 'a':  # Affine cipher
            try:
                a = int(input("Enter 'a' value (must be coprime to 26): "))
                b = int(input("Enter 'b' value: "))
                
                if encrypt:
                    result = service.encrypt_affine(text, (a, b))
                else:
                    result = service.decrypt_affine(text, (a, b))
                print(f"Result: {result}")
            except ValueError as e:
                print(f"Error: {e}")
            
    else:  # File input
        input_file = input("Path to input file: ")
        output_file = input("Path to output file: ")
        delete_prompt = "Delete input file after processing? (yes/no): "
        delete_input = input(delete_prompt).lower() == 'yes'
        
        if not input_file or not output_file:
            print("Error: File paths cannot be empty.")
            return
        
        try:
            if cipher_choice.lower() == 'c':  # Caesar cipher
                shift = int(input("Enter shift value (1-25): "))
                
                def cipher_func(content):
                    if encrypt:
                        return service.encrypt_caesar(content, shift)
                    else:
                        return service.decrypt_caesar(content, shift)
                
            elif cipher_choice.lower() == 'p':  # Polyalphabetic cipher
                keyword = input("Enter keyword: ")
                if not keyword:
                    print("Error: Keyword cannot be empty.")
                    return
                
                def cipher_func(content):
                    if encrypt:
                        return service.encrypt_polyalphabetic(content, keyword)
                    else:
                        return service.decrypt_polyalphabetic(content, keyword)
                
            elif cipher_choice.lower() == 's':  # Substitution cipher
                if encrypt:
                    random_prompt = "Generate random key? (yes/no): "
                    use_random = input(random_prompt).lower() == 'yes'
                    if use_random:
                        seed_prompt = "Enter seed (optional, press Enter to skip): "
                        seed = input(seed_prompt) or None
                        key = service.generate_substitution_key(seed)
                        print(f"Generated key: {key}")
                    else:
                        key = input("Enter 26-character substitution key: ")
                        if len(key) != 26:
                            print("Error: Key must be exactly 26 characters long.")
                            return
                else:
                    key = input("Enter 26-character substitution key: ")
                    if len(key) != 26:
                        print("Error: Key must be exactly 26 characters long.")
                        return
                
                def cipher_func(content):
                    if encrypt:
                        return service.encrypt_substitution(content, key)
                    else:
                        return service.decrypt_substitution(content, key)
                
            elif cipher_choice.lower() == 't':  # Transposition cipher
                key_prompt = "Enter transposition key (word or comma-separated numbers): "
                key = input(key_prompt)
                if ',' in key:
                    # Handle numeric key format
                    try:
                        key = [int(k.strip()) for k in key.split(',')]
                    except ValueError:
                        print("Error: Numeric key must contain only integers.")
                        return
                
                def cipher_func(content):
                    if encrypt:
                        return service.encrypt_transposition(content, key)
                    else:
                        return service.decrypt_transposition(content, key)
                
            elif cipher_choice.lower() == 'r':  # Rail Fence cipher
                rails = int(input("Enter number of rails (2 or more): "))
                if rails < 2:
                    print("Error: Number of rails must be at least 2.")
                    return
                
                def cipher_func(content):
                    if encrypt:
                        return service.encrypt_rail_fence(content, rails)
                    else:
                        return service.decrypt_rail_fence(content, rails)
                
            elif cipher_choice.lower() == 'a':  # Affine cipher
                a = int(input("Enter 'a' value (must be coprime to 26): "))
                b = int(input("Enter 'b' value: "))
                
                def cipher_func(content):
                    if encrypt:
                        return service.encrypt_affine(content, (a, b))
                    else:
                        return service.decrypt_affine(content, (a, b))
            
            # Process the file with the selected cipher
            result = service.process_file_with_cipher(
                input_file, output_file, cipher_func, delete_input
            )
            print(result)
            
        except ValueError as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
