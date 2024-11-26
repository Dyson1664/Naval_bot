import base64

with open('credentials.json', 'rb') as f:
    credentials = f.read()

encoded_credentials = base64.b64encode(credentials).decode('utf-8')

with open('credentials_base64.txt', 'w') as f:
    f.write(encoded_credentials)

print("Credentials have been base64-encoded and saved to 'credentials_base64.txt'")








