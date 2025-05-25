import bankai

while True:
    text = input('bankai > ')
    if text.strip().lower() == "exit":
        break
    
    result, error = bankai.run('<stdin>', text)

    if error:
        print(error.as_string())
    else:
        print(result)