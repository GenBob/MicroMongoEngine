# MicroMongoEngine
A simple tool to easely map Python Objects to MongoDB Documents and back.



    # initialize Documents  
    import document  
    document.database = <some_mongodb_database>  
      
    class User(document.Document):  
      
      _collection = "user" # the collection in which the object will be saved  
      _id_field = "user_id" # the field for a unique identifier for this object  
      
      _marshaled = ["name", "age"] # a filter for json dumps  
      
      user_id: str = None # all fields have to be initialized with None or a default value  
      
      name: str = None  
      age: int = None  
      
      created: datetime = None  
      
    # crate a new User  
    user = User(  
        user_id="some_id",  
      name="Hans",  
      age=5,  
      created=datetime.utcnow()  
    )  
      
    # save the object into the collection  
    user.save()  
      
    # request a user of the collection by its user_id  
    user1 = User.get(user_id="some_id")  
    user == user1  
      
    # request all user with an age of 5  
    user_list = User.get_all(age=5)  
      
    # get the count of users with age = 5 without loading them  
    count = User.count(age=5)  
      
    # update a user  
    user.age = 6  
    user.update()  
      
    # or  
    user.update_data(age=6)  
      
    # delete the user  
      
    user.delete()

