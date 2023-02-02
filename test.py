from rcon.source import Client
with Client('192.168.1.65', 27027, passwd='123123') as client:
    response = client.run('log')
print(response)