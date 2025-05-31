import basic
import os
import platform

def clear_screen():
    # Clear screen command based on the operating system
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

clear_screen()

while True:
    text = input('echo > ')
    
    if text.strip().lower() == "exit":
        break
    elif text.strip().lower() == "scatter":
        clear_screen()
        continue  # Skip the rest of the loop and show fresh prompt
    
    result, error = basic.run('<stdin>', text)

    if error:
        print(error.as_string())
    elif result:
        print(repr(result))
    else:
        print("No result returned")