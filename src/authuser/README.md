# authuser

Both source files should live in the same place   
password.py is imported in user.py

#### The pickle location must be set in the source in user.py

```python
PICKLE_LOCATION = "user.pickle"
```


## Example usage

##### Add a user 

```python
from user import User
user_object = User()
user_object.add_user("rnd1","notacleverpassword")
```

##### Adding an already existing user

```python
user_object.add_user("rnd1","notacleverpassword")
```

will raise an exception

```python
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/home/vineeth/authuser/user.py", line 33, in add_user
    raise Exception("User exists")
Exception: User exists
```

##### Deleting a non existing user

```python
user_object.delete_user("rnd2")
```

will raise an exception

```python
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/home/vineeth/authuser/user.py", line 69, in delete_user
    raise Exception("User does not exist")
Exception: User does not exist
```

##### Modifying an existing user = change password
```python
user_object.modify_user("rnd1","yetanotherstupidpassword")

user_object.modify_user("rnd2","somepass")
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/home/vineeth/authuser/user.py", line 59, in modify_user
    raise Exception("User does not exist")
Exception: User does not exist

```

##### Authenticate a user - returns a Boolean 
```python
user_object.authenticate_user("rnd1","yetanotherstupidpassword")
True

user_object.authenticate_user("rnd1","someothertext")
False
```

