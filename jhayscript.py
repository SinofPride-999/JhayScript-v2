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

    elif text.strip() == "":
      continue

    elif text.startswith("build "):
      filename = text[6:].strip()
      try:
          with open(filename, 'r') as f:
              code = f.read()
          result, error = basic.validate(code)
          if error:
              print(f"Build failed:\n{error.as_string()}")
          else:
              print(f"✅ {result} - No syntax errors")
      except FileNotFoundError:
          print(f"Error: File '{filename}' not found")
      continue
  
    result, error = basic.run('<stdin>', text)

    if error:
        print(error.as_string())
    elif result:
        if len(result.elements) == 1:
            print(repr(result.elements[0]))
    else:
        print(repr(result))
