from Crypto.Cipher import AES # encryption library
import base64

class Post:
  def __init__(self, user, message, hashtags):
    self.user = user
    self.message = message
    self.hashtags = hashtags

  def get_message(self):
    return "<" + self.user.username + ">" + self.message + " " + " ".join(self.hashtags)


class User:
  def __init__(self, username, password): 
    self.username = username 
    self.password = password 
    self.subscriptions = []
    self.subscriptions_hashtags = []
    self.subscribers = []
    self.socket = None

  #add user as subscription and drop self as subscriber
  def add_subscription(self, user):
    if not user:
      return False
    if user not in self.subscriptions:
      self.subscriptions.append(user) 
    if self not in user.subscribers:
      user.subscribers.append(self) 
    return True
    
  #add hashtag as subscription 
  def add_subscription_hashtag(self, hashtag):
    if hashtag not in self.subscriptions_hashtags:
      self.subscriptions_hashtags.append(hashtag)
    return True
  
  #drop user from subscription and drop self from subscriber 
  def drop_subscription(self, user):
    if not user:
      return False
    if user in self.subscriptions:
      self.subscriptions.remove(user)
    if self in user.subscribers:
      user.subscribers.remove(self)
    return True
 
  #add hashtag as subscription 
  def drop_subscription_hashtag(self, hashtag):
    if hashtag in self.subscriptions_hashtags:
      self.subscriptions_hashtags.remove(hashtag)
    return True
  
  #login by setting the connected socket 
  def login(self, socket):
    self.socket = socket

  #logout by closing the socket and nulling socket
  def logout(self):
    if self.socket:
      self.socket.close()
      self.socket = None


class Data:
  def __init__(self):
    self.socket_dict = {}
    self.users_list = []
    self.posts_list = []
    self.posts_unread = {}
    self.subscriptions_hashtags = {}

  def new_user(self, username, password):
    user = User(username, password)
    self.users_list.append(user)
    return user
  
  #load default, hardcoded users
  def load_users(self):
    user_a = self.new_user('a', 'a')
    user_b = self.new_user('b', 'b')
    user_c = self.new_user('c', 'c')
    user_a.add_subscription(user_b)
    user_a.add_subscription(user_c)
    user_b.add_subscription(user_a)
    user_c.add_subscription(user_b)

  #get user object from users_list, given username
  def get_user(self, username):
    for user in self.users_list:
      if user.username == username:
        return user

  #create new post and add to posts_list
  def new_post(self, user, message, hashtags):
    new_post = Post(user, message, hashtags)
    self.posts_list.append(new_post)
    return new_post

  #search and return posts with given hashtag
  def search_hashtag(self, hashtag):
    result = []
    for post in self.posts_list:
      if hashtag in post.hashtags:
        result.append(post.get_message())
    return result[:10]

  #update posts_unread when someone logs out
  def update_posts_unread(self, user):
    for post,users_list in self.posts_unread.items(): 
      if user in users_list: 
        users_list.remove(user)
        if not users_list:
          self.posts_unread.pop(post)
  
  #get unread posts from all (default) or from sender if specified
  def get_posts_unread(self, user, sender=None):
    result = []
    for post,users_list in self.posts_unread.items(): 
      if sender and sender != post.user.username:
        continue
      if user in users_list: 
        result.append(post.get_message())
    return result 

  #search for given username and password and login if found 
  def login(self, username, password, socket): 
    
    BLOCK_SIZE = 32

    # the character used for padding--with a block cipher such as AES, the value
    # you encrypt must be a multiple of BLOCK_SIZE in length.  This character is
    # used to ensure that your value is always a multiple of BLOCK_SIZE
    PADDING = '{'

    # one-liner to sufficiently pad the text to be encrypted
    pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING
    # one-liners to decrypt/decode a string
    DecodeAES = lambda c, e: c.decrypt(base64.b64decode(e)).rstrip(PADDING)

    # create a cipher object using the random secret
    cipher = AES.new('aaaaaaaaaa123456')
    password = DecodeAES(cipher, password)
    user = self.get_user(username)
    if user and user.password == password:
      user.login(socket)
      return (len(self.get_posts_unread(user)), user)
    return None


