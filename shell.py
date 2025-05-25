import bankai

while True:
    text = input('bankai > ')
    result, error = bankai.run('<stdin>', text)

    if error:
        print(error.as_string())
    else:
        print(result)