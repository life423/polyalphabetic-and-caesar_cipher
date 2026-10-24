"""Interactive CipherCraft terminal interface.

Input/output interaction belongs here; CipherService owns operations.
"""
from src.services.cipher_service import CipherService


CIPHERS = {
    "c": ("Caesar", "caesar"),
    "p": ("Polyalphabetic (Vigenère)", "polyalphabetic"),
    "s": ("Substitution", "substitution"),
    "t": ("Transposition", "transposition"),
    "r": ("Rail Fence", "rail_fence"),
    "a": ("Affine", "affine"),
}


def _read_key(service, choice, encrypt):
    """Ask once for a key, regardless of whether input comes from text or a file."""
    if choice == "c":
        return int(input("Enter shift value (1-25): "))
    if choice == "p":
        key = input("Enter keyword: ")
        if not key:
            raise ValueError("Keyword cannot be empty.")
        return key
    if choice == "s":
        if encrypt and input("Generate random key? (yes/no): ").strip().lower() == "yes":
            seed = input("Enter seed (optional, press Enter to skip): ") or None
            key = service.generate_substitution_key(seed)
            print(f"Generated key: {key}")
            return key
        return input("Enter 26-character substitution key: ")
    if choice == "t":
        key = input("Enter transposition key (word or comma-separated numbers): ")
        return [int(part.strip()) for part in key.split(",")] if "," in key else key
    if choice == "r":
        rails = int(input("Enter number of rails (2 or more): "))
        if rails < 2:
            raise ValueError("Number of rails must be at least 2.")
        return rails
    if choice == "a":
        a = int(input("Enter 'a' value (must be coprime to 26): "))
        b = int(input("Enter 'b' value: "))
        return a, b
    raise ValueError("Unsupported cipher type")


def main():
    """Run one interactive encryption/decryption operation."""
    service = CipherService()
    print("Welcome to CipherCraft CLI")
    print("==========================")

    choice = input("Choose operation (e=encrypt, d=decrypt): ").strip().lower()
    if choice not in {"e", "d"}:
        print("Invalid choice. Please enter 'e' for encryption or 'd' for decryption.")
        return

    print("\nAvailable ciphers:")
    for short, (title, _) in CIPHERS.items():
        print(f"{short} - {title}")
    cipher_choice = input("\nChoose cipher type: ").strip().lower()
    if cipher_choice not in CIPHERS:
        print("Invalid choice. Please select a valid cipher type.")
        return

    source = input("Input source: (1=text, 2=file): ").strip()
    if source not in {"1", "2"}:
        print("Invalid choice. Please enter '1' for text input or '2' for file input.")
        return

    if source == "1":
        text = input("Enter text: ")
    else:
        input_file = input("Path to input file: ")
        output_file = input("Path to output file: ")
        delete_input = input("Delete input file after processing? (yes/no): ").strip().lower() == "yes"
        if not input_file or not output_file:
            print("Error: File paths cannot be empty.")
            return

    try:
        key = _read_key(service, cipher_choice, choice == "e")
        name = CIPHERS[cipher_choice][1]
        action = "encrypt" if choice == "e" else "decrypt"
        transform = getattr(service, f"{action}_{name}")
        if source == "1":
            print(f"Result: {transform(text, key)}")
        else:
            result = service.process_file_with_cipher(
                input_file, output_file, lambda content: transform(content, key),
                delete_input,
            )
            print(result)
    except ValueError as exc:
        print(f"Error: {exc}")


if __name__ == "__main__":
    main()
