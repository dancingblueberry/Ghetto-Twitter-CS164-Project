import socket, select, string, sys, os, getpass, base64
from Crypto.Cipher import AES # encryption library

HOST = '10.0.0.4'
PORT = 5000
s = None

def clear():
  os.system('clear')

#Display menu of user's options 
def display_menu(greeting):
  print (greeting)
  print(' --------------------------------------------- ')
  print('|* * * * * * * * * * * * * * * * * * * * * * *|')
  print('|* * * * * * * * * * MENU: * * * * * * * * * *|')
  print('|* * * * * * * * * * * * * * * * * * * * * * *|')
  print('|                                             |')
  print('|           1. See Offline Messages           |')
  print('|           2. Edit Subscriptions             |')
  print('|           3. View Subscribers               |')
  print('|           4. Post a Message                 |')
  print('|           5. Search By Hashtag              |')
  print('|           9. Logout                         |')
  print('|                                             |')
  print('| (NOTE: Enter to cancel and return to menu.) |')
  print(' --------------------------------------------- ')
  sys.stdout.flush()

#Display list of subscriptions
def display_subscriptions():
  s.send("GET_SUBSCRIPTIONS")
  data = get_server_result("GET_SUBSCRIPTIONS:")
  print "** SUBSCRIPTIONS **"
  subscriptions = [x.strip() for x in data.split('\n') if x != ""]
  if subscriptions:
    for i, subscription in enumerate(subscriptions):
      print str(i+1) + ". " + subscription
  else:
    print "No results"
  return subscriptions

#Display list of hashtag subscriptions
def display_subscriptions_hashtags():
  s.send("GET_SUBSCRIPTIONS_HASHTAGS")
  data = get_server_result("GET_SUBSCRIPTIONS_HASHTAGS:")
  print "** HASHTAG SUBSCRIPTIONS **"
  subscriptions = [x.strip() for x in data.split('\n') if x != ""]
  if subscriptions:
    for i, subscription in enumerate(subscriptions):
      print str(i+1) + ". " + subscription
  else:
    print "No results"
  return subscriptions

#Display list of subscribers 
def display_subscribers():
  s.send("GET_SUBSCRIBERS")
  data = get_server_result("GET_SUBSCRIBERS:")
  print "** SUBSCRIBERS **"
  subscribers = [x.strip() for x in data.split('\n') if x != ""]
  if subscribers:
    for i, subscribers in enumerate(subscribers):
      print str(i+1) + ". " + subscribers
  else:
    print "No results"
  return subscribers

#Allow incoming messages while waiting for user input 
def get_user_input(prompt) :
  sys.stdout.write(prompt)
  sys.stdout.flush()
  socket_list = [sys.stdin, s]
  while 1:
    read_sockets, write_sockets, error_sockets = select.select(socket_list , [], [])
    for sock in read_sockets:
      #incoming message from remote server
      if sock == s:
        data = sock.recv(4096).strip()
        if not data :
          print '\nDisconnected from chat server'
          sys.exit()
        else :
          sys.stdout.write("\x1B[2K\r")
          sys.stdout.write(data + "\n")
          sys.stdout.write(prompt)
          sys.stdout.flush()

      #user entered a message
      else :
        return sys.stdin.readline().strip()
 
#Allow incoming messages while waiting for server's response to request
def get_server_result(expecting):
  socket_list = [sys.stdin, s]
  while 1:
    read_sockets, write_sockets, error_sockets = select.select(socket_list , [], [])
    for sock in read_sockets:
      #incoming message from remote server
      if sock == s:
        data = sock.recv(4096).strip()
        if not data :
          print '\nDisconnected from chat server'
          sys.exit()
        else :
          if data.startswith(expecting):
            return data.split(expecting,1)[1]
          else:
            print(data)
            sys.stdout.flush()

#Send request to server to login 
def login():
  BLOCK_SIZE = 32
  # the character used for padding--with a block cipher such as AES, the value
  # you encrypt must be a multiple of BLOCK_SIZE in length.  This character is
  # used to ensure that your value is always a multiple of BLOCK_SIZE
  PADDING = '{'
  # one-liner to sufficiently pad the text to be encrypted
  pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING
  # one-liner encrypt with AES and encode with base64
  EncodeAES = lambda c, s: base64.b64encode(c.encrypt(pad(s)))
  
  # create a cipher object using the random secret
  cipher = AES.new('aaaaaaaaaa123456')

  while 1:
    print("** LOGIN **")
    username = get_user_input("Username: ")
    password = getpass.getpass("Password: ")
    password = EncodeAES(cipher, password)
    s.send("LOGIN:" + username + ":" + password)
    data = get_server_result("LOGIN:")
    if data.startswith("SUCCESS:"):
      greeting = data.split('SUCCESS:', 1)[1]
      clear()
      return greeting 
    else: 
      clear()
      print('!! Incorrect username or password. Please try again. !!')
      sys.stdout.flush()

def select_offline_messages():
  print(' --------------------------------------------- ')
  print('| * * * * * * * * * * * * * * * * * * * * * * | ')
  print("| * * * * * * SEE OFFLINE MESSAGES* * * * * * |")
  print('| * * * * * * * * * * * * * * * * * * * * * * | ')
  print('|                                             |')
  print("|           1. All messages                   |")
  print("|           2. From one subscription          |")
  print('|                                             |')
  print(' --------------------------------------------- ')
  option = get_user_input("Select option: ")
  if not option:
    return
  if option == '1': 
    s.send("GET_OFFLINE_MESSAGES_ALL")
  elif option == '2':
    subscriptions = display_subscriptions()
    while 1:
      to_view = get_user_input("Subscription to view: ")
      if not to_view:
        return
      if to_view.isdigit() and int(to_view) <= len(subscriptions):
        s.send("GET_OFFLINE_MESSAGES_FROM:" + subscriptions[int(to_view) - 1])
        break
  data = get_server_result("GET_OFFLINE_MESSAGES:")
  if data:
    print("** Offline Messages **")
    print(data)
  else:
    print("No unread messages.")
  get_user_input("Press any key to continue.")

#Send request to server to add or drop subscriptions
def select_edit_subscriptions():
  print(' --------------------------------------------- ')
  print('| * * * * * * * * * * * * * * * * * * * * * * | ')
  print("| * * * * * * EDIT SUBSCRIPTIONS* * * * * * * |")
  print('| * * * * * * * * * * * * * * * * * * * * * * | ')
  print('|                                             |')
  print("|           1. Add user subscription          |")
  print("|           2. Add hashtag subscription       |")
  print("|           3. Drop user subscription         |")
  print("|           4. Drop hashtag subscription      |")
  print('|                                             |')
  print(' --------------------------------------------- ')
  option = get_user_input("Select option: ")
  if option == '1':
    username = get_user_input("User to subscribe to: ")
    if not username:
      return
    s.send("ADD_SUBSCRIPTION:" + username)
    data = get_server_result("ADD_SUBSCRIPTION:")
    if data == "SUCCESS":
      print "Successfully added subscription to " + username + "."
    else:
      print "!! An error occurred. !!"
    get_user_input("Press any key to continue.")
  elif option == '2':
    hashtag = get_user_input("Hashtag to subscribe to: ")
    if not hashtag:
      return 
    s.send("ADD_SUBSCRIPTION_HASHTAG:" + hashtag)
    data = get_server_result("ADD_SUBSCRIPTION_HASHTAG:")
    if data == "SUCCESS":
      print "Successfully added subscription to " + hashtag + "."
    else:
      print "!! An error occurred. !!" 
  elif option == '3':
    subscriptions = display_subscriptions()
    while 1:
      to_drop = get_user_input("Subscription to drop: ")
      if not to_drop:
        return
      if to_drop.isdigit() and int(to_drop) <= len(subscriptions):
        s.send("DROP_SUBSCRIPTION:" + subscriptions[int(to_drop) - 1])
        data = get_server_result("DROP_SUBSCRIPTION:")
        if data == "SUCCESS":
          print "Successfully dropped subscription to " + subscriptions[int(to_drop) - 1] + "."
        else:
          print "!! An error occurred. !!"
        get_user_input("Press any key to continue.")
        break;
  elif option == '4':
    subscriptions = display_subscriptions_hashtags()
    while 1:
      to_drop = get_user_input("Hashtag subscription to drop: ")
      if not to_drop:
        return
      if to_drop.isdigit() and int(to_drop) <= len(subscriptions):
        s.send("DROP_SUBSCRIPTION_HASHTAG:" + subscriptions[int(to_drop) - 1])
        data = get_server_result("DROP_SUBSCRIPTION_HASHTAG:")
        if data == "SUCCESS":
          print "Successfully dropped subscription to " + subscriptions[int(to_drop) - 1] + "."
        else:
          print "!! An error occurred. !!"
        get_user_input("Press any key to continue.")
        break;

#Send request to server to view subscribers
def select_view_subscribers():
  display_subscribers()
  get_user_input("Press any key to continue.")

#Send request to server to broadcast messages to subscribers
def select_post_message():
  print("** NEW MESSAGE **")
  while 1:
    message = get_user_input("Message: ")
    if not message:
      return
    hashtags = get_user_input("Hashtags (Enter for no hashtags): ")
    if len(message) + len(hashtags) <= 140:
      break
    print("!! Error: Must be 140 characters or less !!")
  send_to = get_user_input("Send to (Enter for all subscribers): ")
  s.send("POST:" + message + "\nHASHTAGS:" + hashtags + "\nSEND_TO:" + send_to)
  print("Sucessfully posted new message.")
  get_user_input("Press any key to continue.")


def select_search_hashtag():
  print("** SEARCH BY HASHTAG **")
  hashtag = get_user_input("Hashtag: ")
  if not hashtag:
    return
  s.send("SEARCH:" + hashtag)
  data = get_server_result("SEARCH:")
  print(data)
  get_user_input('Press any key to continue.')

def select_logout():
  print "Logging out! BYE"
  s.send("LOGOUT")
  sys.exit()


def select_menu_option(data):
  if data == '1': 
    select_offline_messages()
  elif data == '2':
    select_edit_subscriptions()
  elif data == '3':
    select_view_subscribers()
  elif data == '4':
    select_post_message()
  elif data == '5': 
    select_search_hashtag()
  elif data == '9':
    select_logout()
  else: 
    return False
  return True


#main function
def main():
  clear()
  global s
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.settimeout(2)

  # connect to remote host
  try :
    s.connect((HOST, PORT))
  except :
    print 'Unable to connect'
    sys.exit()

  greeting = login()
  display_menu(greeting)

  while 1:
    data = get_user_input("Select: ")
    valid = select_menu_option(data)
    clear()
    #display_greeting()
    display_menu(greeting)
    if not valid: 
      print("!! Invalid selection. Please try again !!")

if __name__ == "__main__":
  main()




