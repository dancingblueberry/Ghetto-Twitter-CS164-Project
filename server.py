import socket, select, sys
from user import Data

# List to keep track of socket descriptors
RECV_BUFFER = 4096 # Advisable to keep it as an exponent of 2
PORT = 5000
server_socket = ""
my_data = Data()
my_data.load_users()


def login(sock, data):
  result = data.split(':')
  username = result[0]
  password = result[1]
  result = my_data.login(username, password, sock)
  if not result:
    sock.send("LOGIN:FAIL")
  else:
    greeting = 'Welcome Back, ' + username + '\nYou have ' + str(result[0]) + ' new messages from your subscriptions'
    sock.send("LOGIN:SUCCESS:" + greeting)  # send back unread num
    my_data.socket_dict[sock] = result[1]         # add user object to dict

def logout(sock):
  user = my_data.socket_dict.get(sock)
  if user:
    user.logout()
  my_data.update_posts_unread(user)
  my_data.socket_dict.pop(sock, 0)

def get_offline_messages(sock, sender=""):
  user = my_data.socket_dict.get(sock)
  posts_unread = my_data.get_posts_unread(user, sender)
  sock.send("GET_OFFLINE_MESSAGES:" + "\n".join(posts_unread)) 

#Function to send new posts to all online subscribers
def post_message_send (sock, post, send_to):
  send_user = my_data.socket_dict.get(sock)
  offline_subscribers = []
  send_to_users = set()
  if send_to: 
    for username in send_to:
      send_to_users.add(my_data.get_user(username))
  else:
    send_to_users = set(send_user.subscribers)
    for hashtag in post.hashtags:
      if hashtag in my_data.subscriptions_hashtags.keys():
        print my_data.subscriptions_hashtags.get(hashtag)
        send_to_users |= set(my_data.subscriptions_hashtags.get(hashtag))
    send_to_users.discard(send_user)
  for user in list(send_to_users):
    if user.socket:
      try:
        user.socket.send('\r' + post.get_message())
      except:
        logout(user.socket)
    else:
      offline_subscribers.append(user)
  if offline_subscribers:
    my_data.posts_unread[post] = offline_subscribers

def post_message(sock, data): 
  user = my_data.socket_dict.get(sock)
  result = data.split('\nHASHTAGS:', 1)
  message = result[0]
  result = result[1].split('\nSEND_TO:', 1)
  hashtags =  [x.strip() for x in result[0].split(' ') if x != ""]
  send_to =  [x.strip() for x in result[1].split(' ') if x != ""]
  post_message_send(sock, my_data.new_post(user, message, hashtags), send_to) 

def get_subscriptions(sock):
  user = my_data.socket_dict.get(sock)
  subscriptions = [s.username for s in user.subscriptions]
  sock.send("GET_SUBSCRIPTIONS:" + "\n".join(subscriptions))

def get_subscriptions_hashtags(sock):
  user = my_data.socket_dict.get(sock)
  print user.subscriptions_hashtags
  sock.send("GET_SUBSCRIPTIONS_HASHTAGS:" + "\n".join(user.subscriptions_hashtags))

def add_subscription(sock, to_add):
  user = my_data.socket_dict.get(sock)
  user_to_add = my_data.get_user(to_add)
  if user.add_subscription(user_to_add):
    sock.send("ADD_SUBSCRIPTION:SUCCESS")
  else:
    sock.send("ADD_SUBSCRIPTION:FAIL")

def add_subscription_hashtag(sock, to_add):
  user = my_data.socket_dict.get(sock)
  if to_add not in my_data.subscriptions_hashtags:
    my_data.subscriptions_hashtags[to_add] = []
  if user not in my_data.subscriptions_hashtags.get(to_add):
    my_data.subscriptions_hashtags[to_add].append(user)
  if user.add_subscription_hashtag(to_add):
    sock.send("ADD_SUBSCRIPTION_HASHTAG:SUCCESS")
  else:
    sock.send("ADD_SUBSCRIPTION_HASHTAG:FAIL")

def drop_subscription(sock, to_drop):
  user = my_data.socket_dict.get(sock)
  user_to_drop = my_data.get_user(to_drop)
  if user.drop_subscription(user_to_drop):
    sock.send("DROP_SUBSCRIPTION:SUCCESS")
  else:
    sock.send("DROP_SUBSCRIPTION:FAIL")

def drop_subscription_hashtag(sock, hashtag):
  user = my_data.socket_dict.get(sock)
  user.drop_subscription_hashtag(hashtag)
  if hashtag in my_data.subscriptions_hashtags.keys():
    user_list = my_data.subscriptions_hashtags.get(hashtag)
    user_list.remove(user)
    if not user_list: 
      my_data.subscriptions_hashtags.pop(hashtag)
  sock.send("DROP_SUBSCRIPTION_HASHTAG:SUCCESS")

def get_subscribers(sock):
  user = my_data.socket_dict.get(sock)
  subscribers = [s.username for s in user.subscribers]
  sock.send("GET_SUBSCRIBERS:" + "\n".join(subscribers)) 

def search_hashtag(sock, hashtag):
  search_list = my_data.search_hashtag(hashtag)
  if search_list:
    sock.send("SEARCH:" + "\n".join(search_list))
  else:
    sock.send("SEARCH:No results")

def parse_data(sock, data):
  result = None 
  action = None 
  if ':' in data:
    result = data.split(':', 1)
    action = result[0]
    data = result[1]
  else: 
    action = data
    data = ""
  
  if action == "LOGIN":
    login(sock, data)
  elif action == "GET_OFFLINE_MESSAGES_ALL":
    get_offline_messages(sock)
  elif action == "GET_OFFLINE_MESSAGES_FROM":
    get_offline_messages(sock, data)
  elif action == "POST":
    post_message(sock, data)
  elif action == "GET_SUBSCRIPTIONS":
    get_subscriptions(sock)
  elif action == "GET_SUBSCRIPTIONS_HASHTAGS":
    get_subscriptions_hashtags(sock)
  elif action == "ADD_SUBSCRIPTION":
    add_subscription(sock, data)
  elif action == "ADD_SUBSCRIPTION_HASHTAG":
    add_subscription_hashtag(sock, data)
  elif action == "DROP_SUBSCRIPTION":
    drop_subscription(sock, data)
  elif action == "DROP_SUBSCRIPTION_HASHTAG":
    drop_subscription_hashtag(sock, data)
  elif action == "GET_SUBSCRIBERS":
    get_subscribers(sock)
  elif action == "SEARCH":
    search_hashtag(sock, data)
  elif action == "LOGOUT":
    logout(sock)

def exec_command(command):
  if command == "messagecount":
    print "Message Count: " + str(len(my_data.posts_list))
  elif command == "storedcount":
    print "Stored Messages Count: " + str(len(my_data.posts_unread))
  elif command == "usercount":
    online = 0
    for s, user in my_data.socket_dict.items(): 
      if user: 
        online += 1
    print "Online Users Count: " + str(online)
  elif command.startswith("newuser"):
    if 'newuser ' in command and ':' in command:
      command = command.split("newuser ")[1]
      result = command.split(":")
      username = result[0]
      password = result[1]
      my_data.new_user(username, password)
      print "Successfully created new user."
    else:
      print "Usage: newuser username:password"
  else: 
    print "!! Invalid Command !!"
    print "Valid commands: messagecount, usercount, storedcount, newuser"


def main():
  global server_socket
  server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  server_socket.bind(("0.0.0.0", PORT))
  server_socket.listen(10)

  # Add server socket to the list of readable connections
  my_data.socket_dict[server_socket] = None
  my_data.socket_dict[sys.stdin] = None

  print "Ghetto Twitter server started on port " + str(PORT)

  while 1:
    # Get the list sockets which are ready to be read through select
    read_sockets,write_sockets,error_sockets = select.select(my_data.socket_dict,[],[])

    for sock in read_sockets:
      if sock == sys.stdin: 
        command = sys.stdin.readline().strip()
        exec_command(command)
      #New user connection
      elif sock == server_socket:
        sockfd, addr = server_socket.accept()
        my_data.socket_dict[sockfd] = None

      #New incoming message from a user
      else:
        try:
          data = sock.recv(RECV_BUFFER)
          if data:
            parse_data(sock, data)
        except:
          logout(sock)

  server_socket.close()

if __name__ == "__main__":
  main()

