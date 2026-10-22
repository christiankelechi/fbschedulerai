import typing
Username = typing.NewType('Username', str)
rick = Username('Rick')

def print_username(username: Username):
    print(f'Username: {username}')

print_username(rick)
print_username(str(rick))