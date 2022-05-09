from email import message
from venv import create
from flask import Flask, render_template, request, redirect, abort, flash, url_for, make_response, session, escape
from flask_mysqldb import MySQL
from sqlalchemy import false
import os
from werkzeug.utils import secure_filename
from flask import Response

from flask_ckeditor import CKEditor
from datetime import date, timedelta, datetime



#region Flask & MySQL settings
UPLOAD_FOLDER = 'static/img'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
ckeditor = CKEditor(app)


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root' 
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'flask'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

mysql = MySQL(app)
#endregion Flask & MySQL settings

#region Login page

@app.route("/panel/login", methods=['POST', 'GET'])
def login(message = "", messageType = ""):
   try:
      if session["username"]:
         return redirect(url_for('loggedIn'))
   except Exception as ex:
      print(f"Session Error [{login.__name__}]: ", ex)
      return render_template("/panel/login/login.html", message = message, messageType = messageType)

#endregion Login page

#region Logged in successfully

@app.route('/panel', methods=['POST', 'GET'])
def loggedIn():
   data = ""
   if request.method == "POST": 
      username = request.form.get('username') 
      password = request.form.get('password')
   try:
      if session['username'] != "":
         username = session['username']
         password = session['password']
         dataPermission = session['permission']
         print("Logged in: ", session['username'])
         login_status = True
         return redirect(url_for('homepage'))
         
      else:
         try:
            login_status = False
            cursor = mysql.connection.cursor()
            query = "SELECT * FROM login WHERE username = %s and password = %s"
            cursor.execute(query, (username, password,))
            data = [item[0] for item in cursor.fetchall()]
            mysql.connection.commit()
            cursor.close()
         except Exception as ex:
            print(f"MySQL Error [{loggedIn.__name__}] [1]: ", ex)
   except Exception as ex:
      print(f"Session Error [{loggedIn.__name__}] [1]: ", ex)
      try:
         cursor = mysql.connection.cursor()
         query = "SELECT * FROM login WHERE username = %s and password = %s"
         cursor.execute(query, (username, password,))
         data = [item[0] for item in cursor.fetchall()]

         queryPermission = "SELECT permission FROM login WHERE username = %s and password = %s"
         cursor.execute(queryPermission, (username, password,))
         dataPermission = cursor.fetchall()

         for item in dataPermission:
            dataPermission = item[0]

         mysql.connection.commit()
         cursor.close()
         

      except Exception as ex:
         print(f"MySQL Error [{loggedIn.__name__}] [1]: ", ex)
  
   if data:
      session['username'] = username
      session['password'] = password
      session['permission'] = dataPermission
      login_status = True
      return redirect(url_for('homepage'))
   else:
      if request.method == "POST":
         message = "User not found!"
         messageType = "danger"
         
         return render_template("/panel/login/login.html",message = message, messageType = messageType)
      else:
         message = "Not Logged In!"
         messageType = "danger"
         return render_template("/panel/login/login.html",message = message, messageType = messageType)

#endregion Logged in successfully

#region adminpanel

def getPosts(message, messageType, post_link = ""):
   
   query = ""
   try:
      cursor = mysql.connection.cursor()
      
      if post_link == "":
         query = f"SELECT id, title, content, summary, link, author, created_date, last_modified_date, tags from posts ORDER BY created_date DESC"
      else:
         query = f"SELECT id, title, content, summary, link, author, created_date, last_modified_date, tags from posts WHERE link = '{post_link}' "
      cursor.execute(query)
      data = cursor.fetchall()
      
      cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='flask' AND `TABLE_NAME`='posts';")
      columns= [item[0] for item in cursor.fetchall()]
      
      if not data:
         message = "No results matched!"
         messageType = "danger"
      else:
         messageType = "success"

     
      mysql.connection.commit()
      cursor.close()
      
   except Exception as ex:
      print(f"MySQL Error [{list.__name__}] : ", ex)

      message = "No Database Connection!"
      messageType = "danger"
      data = ""
      columns = ""

   return data, columns, message, messageType



@app.route('/', methods=['POST', 'GET'])
def homepage():

   message = ""
   messageType = ""    
   data, columns, message, messageType = getPosts(message, messageType)

   try:
      username = session['username']
      login_status = True
      print("USERNAME: ", username)
      
   except Exception as ex:
      print(f"Session Error [{homepage.__name__}] : ", ex)
      login_status = False


   print("LOGIN STATUS: ", login_status)
   dictionary = {}
   data_list = []
   print("data: ", data)
   for id, title, content, summary, link, author, created_date, last_modified_date, tags in data:
      dictionary = dict(id = id, title = title, content = content, summary = summary, link = link, author = author, created_date = created_date, last_modified_date = last_modified_date, tags = tags)
      data_list.append(dictionary)
    
   return render_template("/homepage.html",  data_list=data_list, columns = columns, message = message, messageType=messageType, login_status = login_status)



@app.route("/posts/<string:post_link>", methods=['POST', 'GET'])
def showPost(post_link):
   message = ""
   messageType = ""
   data, columns, message, messageType = getPosts(message, messageType, post_link)
   login_status = False
   try:
      username = session['username']
      login_status = True
      
   except Exception as ex:
      print(f"Session Error [{showPost.__name__}] : ", ex)
      login_status = False

   dictionary = {}
   data_list = []
   print("data: ", data)
   for id, title, content, summary, link, author, created_date, last_modified_date, tags in data:
      dictionary = dict(id = id, title = title, content = content, summary = summary, link = link, author = author, created_date = created_date, last_modified_date = last_modified_date, tags = tags)
      data_list.append(dictionary)



   return render_template("panel/posts/post.html", data_list=data_list, columns = columns, message = message, messageType = messageType, login_status = login_status)


def insertPost(title, content, summary, created_date, last_modified_date, author, link, tags):
   
   try:
      cursor = mysql.connection.cursor()
      
      cursor.execute("SELECT link from posts;")
      tempLink= [item[0] for item in cursor.fetchall()]


      if not link in tempLink:

         query = f"INSERT INTO `posts`(`id`, `title`, `content`, `summary`,  `link`, `author`, `created_date`, `last_modified_date`, `tags` ) VALUES ('NULL', '{title}','{content}','{summary}' ,'{link}','{author}', '{created_date}', '{last_modified_date}', '{tags}')"
         cursor.execute(query)
      
         message = "Post added successfully!"
         messageType = "success"
         session.pop('post-title', None)
         session.pop('post-link', None)
         session.pop('post-content', None)
         session.pop('post-summary', None)
         session.pop('post-tags', None)
      else:
         session['post-title'] = title
         session['post-link'] = link
         session['post-content'] = content
         session['post-summary'] = summary
         session['post-tags'] = tags

         message = "Böyle bir link zaten var!"
         messageType = "danger"

      mysql.connection.commit()
      cursor.close()
   except Exception as ex:
      print(f"MySQL Error [{insertPost.__name__}] : ", ex)
      message = "Something's wrong, the post can't be added!"
      messageType = "danger"

   return message, messageType

@app.route('/panel/add-post', methods=['POST', 'GET'])
def addpost():
   print("addpost")
   try:
      if session['username'] != "":
         user = session['username']
         permission = session['permission']
         login_status = True

         try:
            if session["post-link"]:
               session['post-link'] = session['post-link']
         except Exception as ex:
            print(f"Session Error [{addpost.__name__}] : ", ex)
            session['post-link'] = ""

         if permission == "User":
            return redirect(url_for('loggedIn'))
                  

         message = ""
         messageType = ""
         

         try:
            if request.method == "POST":  
               content = request.form.get('ckeditor')
               created_date = datetime.now()
               last_modified_date = created_date
               author = user


               title = request.form.get('title') 
               link = request.form.get('link')
               summary = request.form.get('summary')
               tags = request.form.get('tags')

               message, messageType = insertPost(title, content, summary, created_date, last_modified_date, author, link, tags)
         except Exception as ex:
            print(f"Request Error [{addpost.__name__}] : ", ex)
         return render_template("/panel/posts/add-post.html", message = message, messageType=messageType, user=user, permission = permission, login_status = login_status)         
   except Exception as ex:
         print(f"Session Error [{addpost.__name__}] : ", ex)
         return redirect(url_for('loggedIn'))



@app.route('/panel/users', methods=['POST', 'GET'])
def users():
   try:
      if session['username'] != "":
         user = session['username']
         permission = session['permission']
         login_status = True

         if permission == "User":
            return redirect(url_for('loggedIn'))
                  

         message = ""
         messageType = ""
         
         data, columns, message, messageType = list(message, messageType)
         try:
            if request.method == "POST":  
               if request.form['process'] == 'Add':
                  message, messageType = insert()
                  data, columns, message, messageType = list(message, messageType)
               elif request.form['process'] == 'Update':
                  message, messageType = update()
                  data, columns, message, messageType = list(message, messageType)
               elif request.form['process'] == 'Search':
                  parameter = request.form.get('search') 
                  data, columns, message, messageType = list(message, messageType, parameter)
               elif int(request.form['process']) > 0: 
                  delete(int(request.form['process']))
                  data, columns, message, messageType = list(message, messageType)
               
         except Exception as ex:
            print(f"Request Error [{users.__name__}] : ", ex)
         return render_template("/panel/users/users.html", data=data, columns = columns, message = message, messageType=messageType, user=user, permission = permission, login_status = login_status)         
   except Exception as ex:
         print(f"Session Error [{users.__name__}] : ", ex)
         return redirect(url_for('loggedIn'))


#endregion adminpanel

#region actions
def list(message, messageType, parameter = ""):

   query = ""
   permission = session["permission"]

   try:
      cursor = mysql.connection.cursor()
      if parameter:
         if permission == "Admin":

            # Direct match
            # cursor.execute(f"SELECT id, username, password, permission from login \
            # WHERE username = '{parameter}' or \
            # password = '{parameter}' or \
            # permission = '{parameter}'")


            # Include           
            query = f"SELECT id, username, password, permission from login \
            WHERE username LIKE '%{parameter}%' or \
            password LIKE '%{parameter}%' or \
            permission LIKE '%{parameter}%'"

         elif permission == "Moderator":

            # Include
            query = f"SELECT id, username, REPLACE(password, password,'********'), permission from login \
            WHERE username LIKE '%{parameter}%' or \
            password LIKE '%{parameter}%' or \
            permission LIKE '%{parameter}%'"

      else:
         if permission == "Admin":
            query = "SELECT id, username, password, permission from login"
         elif permission == "moderator":
            query = "SELECT id, username, REPLACE(password, password,'********'), permission from login"
            
            
      
      cursor.execute(query)
      data = cursor.fetchall()
      
      cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='flask' AND `TABLE_NAME`='login';")
      columns= [item[0] for item in cursor.fetchall()]
      
      if not data:
         message = "No results matched!"
         messageType = "danger"
     
      mysql.connection.commit()
      cursor.close()
      
   except Exception as ex:
      print(f"MySQL Error [{list.__name__}] : ", ex)

      message = "No Database Connection!"
      messageType = "danger"
      data = ""
      columns = ""

   return data, columns, message, messageType

def delete(id):
   cursor = mysql.connection.cursor()

   query = f"SELECT username from login WHERE id='{id}';"
   cursor.execute(query)
   username = [item[0] for item in cursor.fetchall()]

   print(username)
   query = f"DELETE FROM `profilephotos` WHERE username='{username[0]}'"
   cursor.execute(query)

   query = f"DELETE FROM `login` WHERE id='{id}'"
   cursor.execute(query)


   mysql.connection.commit()
   cursor.close()

def insert():
   username = request.form.get('username') 
   password = request.form.get('password')
   permission = request.form.get("permission") #TODO
   
   cursor = mysql.connection.cursor()
   cursor.execute("SELECT username from login;")
   tempName= [item[0] for item in cursor.fetchall()]

   if not username in tempName:
      query = f"INSERT INTO `login`(`id`, `username`, `password`, `permission` ) VALUES ('NULL','{username}','{password}','{permission}')"
      cursor.execute(query)

      query = f"INSERT INTO `profilephotos`(`username`, `photo`) VALUES ('{username}','default.jpg')"
      cursor.execute(query)


      query = f"INSERT INTO `contactprofile`(`username`, `fullname`, `phone`, `address`, `email`, `job`) VALUES ('{username}','{username}', '', '', '', 'Looking for a job')"
      cursor.execute(query)

  
      query = f"INSERT INTO `skills`(`username`, `skill-1-name`, `skill-2-name`, `skill-3-name`, `skill-4-name`, `skill-5-name`, `skill-6-name`, `skill-7-name`, `skill-8-name`, `skill-9-name`, `skill-10-name`, `skill-1-value`, `skill-2-value`, `skill-3-value`, `skill-4-value`, `skill-5-value`, `skill-6-value`, `skill-7-value`, `skill-8-value`, `skill-9-value`, `skill-10-value` ) VALUES ('{username}','', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '')"
      cursor.execute(query)


      query = f"INSERT INTO `social`(`username`, `website`, `github`, `twitter`, `instagram`, `facebook`) VALUES ('{username}', '', '', '', '', '')"
      cursor.execute(query)




      message = "User added successfully!"
      messageType = "success"
   else:
      message = "This user already exists"
      messageType = "danger"
      
   mysql.connection.commit()
   cursor.close()

   return message, messageType

def update():

   id = request.form.get('idUpdate') 
   username = request.form.get('usernameUpdate') 
   password = request.form.get('passwordUpdate')
   permission = request.form.get("permissionUpdate") #TODO

   cursor = mysql.connection.cursor()
   cursor.execute("SELECT username from login;")
   tempNames= [item[0] for item in cursor.fetchall()]

   tempUsername=cursor.execute(f"SELECT username from login WHERE id = '{id}';")
   tempUsername= [item[0] for item in cursor.fetchall()]

   tempNames.remove(tempUsername[0]) 

   if not username in tempNames:
      query = f"UPDATE `login` SET `id`={id},`username`='{username}',`password`='{password}',`permission`='{permission}'  WHERE id = {id};"
      cursor.execute(query)
      message = "Informations are updated successfully!"
      messageType = "success"
   else:
      message = "This user already exists!"
      messageType = "danger"

   mysql.connection.commit()
   cursor.close()

   return message, messageType

#endregion actions

#region logout

@app.route('/panel/logout', methods = ['GET', 'POST'])
def logout():

   try:
      if session["username"]:
         session.pop('username', None)
         session.pop('password', None)
         session.pop('permission', None)
         message = "Successfully logged out!"
         messageType = "success"
   except Exception as ex:
      message = "Even you didn't logged in!"
      messageType = "danger"
      print(f"Session Error [{logout.__name__}]: ", ex)

   return render_template("/panel/login/login.html",message = message, messageType = messageType)

#endregion logout


#region profile settings

#Profil düzenleme sayfası #TODO
@app.route("/panel/profile/edit", methods=['POST', 'GET'])
def editProfile():
 
   try:
      if session['username'] != "":
         user = session['username']
         permission = session['permission']
         message = ""

         message = updateProfile(message)
         login_status = True

         try:
            
            cursor = mysql.connection.cursor()

            photoQuery = f"SELECT photo from profilephotos \
            WHERE username = '{user}'"
            cursor.execute(photoQuery)
            photo=[item[0] for item in cursor.fetchall()]


            contactProfileQuery = f"SELECT * from contactprofile \
            WHERE username = '{user}'"
            cursor.execute(contactProfileQuery)


            for item in cursor.fetchall():
               fullname = item[1]
               phone = item[2]
               address = item[3]
               email = item[4]
               job = item[5]

            skillsProfileQuery = f"SELECT * from skills \
            WHERE username = '{user}'"
            cursor.execute(skillsProfileQuery)

            for item in cursor.fetchall():
          
               skill_1_name = item[1]
               skill_2_name = item[2]
               skill_3_name = item[3]
               skill_4_name = item[4]
               skill_5_name = item[5]
               skill_6_name = item[6]
               skill_7_name = item[7]
               skill_8_name = item[8]
               skill_9_name = item[9]
               skill_10_name = item[10]

               skill_1_value = item[11]
               skill_2_value = item[12]
               skill_3_value = item[13]
               skill_4_value = item[14]
               skill_5_value = item[15]
               skill_6_value = item[16]
               skill_7_value = item[17]
               skill_8_value = item[18]
               skill_9_value = item[19]
               skill_10_value = item[20]

            socialProfileQuery = f"SELECT * from social \
            WHERE username = '{user}'"
            cursor.execute(socialProfileQuery)


            for item in cursor.fetchall():
               website = item[1]
               github = item[2]
               twitter = item[3]
               instagram = item[4]
               facebook = item[5]

            print(f"{user}'s photo: ",photo[0])
           
            mysql.connection.commit()
            cursor.close()

            uploadPhoto(user)

         except Exception as ex:
            print(f"MySQL Error [{editProfile.__name__}]: ", ex)


   except Exception as ex:
         print(f"Session Error [{editProfile.__name__}]: ", ex)
         return redirect(url_for('loggedIn'))

   return render_template("panel/profile/edit.html", photo=photo[0],message = message, messageType = "success", login_status = login_status, user=user, permission=permission, fullname = fullname, phone = phone, address = address, email = email, job = job,
   skill_1_name = skill_1_name, skill_1_value = skill_1_value,
   skill_2_name = skill_2_name, skill_2_value = skill_2_value,
   skill_3_name = skill_3_name, skill_3_value = skill_3_value,
   skill_4_name = skill_4_name, skill_4_value = skill_4_value,
   skill_5_name = skill_5_name, skill_5_value = skill_5_value,
   skill_6_name = skill_6_name, skill_6_value = skill_6_value,
   skill_7_name = skill_7_name, skill_7_value = skill_7_value,
   skill_8_name = skill_8_name, skill_8_value = skill_8_value,
   skill_9_name = skill_9_name, skill_9_value = skill_9_value,
   skill_10_name = skill_10_name, skill_10_value = skill_10_value,
   website = website, github=github, twitter=twitter, instagram = instagram, facebook = facebook)

   


def updateProfile(message):
   if request.method == "POST": 
      postWebsite = request.form.get('website')
      postGithub = request.form.get('github')
      postTwitter = request.form.get('twitter')
      postInstagram = request.form.get('instagram')
      postFacebook = request.form.get('facebook')
      
      cursor = mysql.connection.cursor()

      query = f"UPDATE `social` SET `website`='{postWebsite}',`github`='{postGithub}',`twitter`='{postTwitter}',`instagram`='{postInstagram}',`facebook`='{postFacebook}' WHERE `username`='{session['username']}'"
      cursor.execute(query)
         
      postFullname = request.form.get('fullname')
      postEmail = request.form.get('email')
      postPhone = request.form.get('phone')
      postJob = request.form.get('job')
      postAddress = request.form.get('address')

      query = f"UPDATE `contactprofile` SET `fullname`='{postFullname}',`email`='{postEmail}',`phone`='{postPhone}',`job`='{postJob}',`address`='{postAddress}' WHERE `username`='{session['username']}'"
      cursor.execute(query)

      postSkill_1_Name = request.form.get('skill_1_name')
      postSkill_1_Value = request.form.get('skill_1_value')

      postSkill_2_Name = request.form.get('skill_2_name')
      postSkill_2_Value = request.form.get('skill_2_value')

      postSkill_3_Name = request.form.get('skill_3_name')
      postSkill_3_Value = request.form.get('skill_3_value')

      postSkill_4_Name = request.form.get('skill_4_name')
      postSkill_4_Value = request.form.get('skill_4_value')

      postSkill_5_Name = request.form.get('skill_5_name')
      postSkill_5_Value = request.form.get('skill_5_value')

      postSkill_6_Name = request.form.get('skill_6_name')
      postSkill_6_Value = request.form.get('skill_6_value')

      postSkill_7_Name = request.form.get('skill_7_name')
      postSkill_7_Value = request.form.get('skill_7_value')

      postSkill_8_Name = request.form.get('skill_8_name')
      postSkill_8_Value = request.form.get('skill_8_value')

      postSkill_9_Name = request.form.get('skill_9_name')
      postSkill_9_Value = request.form.get('skill_9_value')

      postSkill_10_Name = request.form.get('skill_10_name')
      postSkill_10_Value = request.form.get('skill_10_value')

      query = f"UPDATE `skills` SET `skill-1-name`='{postSkill_1_Name}', \
      `skill-2-name`='{postSkill_2_Name}',`skill-3-name`='{postSkill_3_Name}', \
      `skill-4-name`='{postSkill_4_Name}',`skill-5-name`='{postSkill_5_Name}', \
      `skill-6-name`='{postSkill_6_Name}',`skill-7-name`='{postSkill_7_Name}', \
      `skill-8-name`='{postSkill_8_Name}',`skill-9-name`='{postSkill_9_Name}', \
      `skill-10-name`='{postSkill_10_Name}',`skill-1-value`='{postSkill_1_Value}', \
      `skill-2-value`='{postSkill_2_Value}',`skill-3-value`='{postSkill_3_Value}', \
      `skill-4-value`='{postSkill_4_Value}',`skill-5-value`='{postSkill_5_Value}', \
      `skill-6-value`='{postSkill_6_Value}',`skill-7-value`='{postSkill_7_Value}', \
      `skill-8-value`='{postSkill_8_Value}',`skill-9-value`='{postSkill_9_Value}', \
      `skill-10-value`='{postSkill_10_Value}' WHERE `username`='{session['username']}'"
      cursor.execute(query)


      mysql.connection.commit()
      cursor.close()
      message = "Your informations are updated!"
      
   return message



@app.route("/panel/profile", methods=['POST', 'GET'])
def profile():

   
   try:
      if session['username'] != "":
         user = session['username']
         permission = session['permission']
         message = ""
         login_status = True

         try:
            
            cursor = mysql.connection.cursor()

            photoQuery = f"SELECT photo from profilephotos \
            WHERE username = '{user}'"
            cursor.execute(photoQuery)
            photo=[item[0] for item in cursor.fetchall()]


            contactProfileQuery = f"SELECT * from contactprofile \
            WHERE username = '{user}'"
            cursor.execute(contactProfileQuery)


            for item in cursor.fetchall():
               fullname = item[1]
               phone = item[2]
               address = item[3]
               email = item[4]
               job = item[5]


            skillsProfileQuery = f"SELECT * from skills \
            WHERE username = '{user}'"
            cursor.execute(skillsProfileQuery)

            for item in cursor.fetchall():
 
               skill_1_name = item[1]
               skill_2_name = item[2]
               skill_3_name = item[3]
               skill_4_name = item[4]
               skill_5_name = item[5]
               skill_6_name = item[6]
               skill_7_name = item[7]
               skill_8_name = item[8]
               skill_9_name = item[9]
               skill_10_name = item[10]

               skill_1_value = item[11]
               skill_2_value = item[12]
               skill_3_value = item[13]
               skill_4_value = item[14]
               skill_5_value = item[15]
               skill_6_value = item[16]
               skill_7_value = item[17]
               skill_8_value = item[18]
               skill_9_value = item[19]
               skill_10_value = item[20]


            socialProfileQuery = f"SELECT * from social \
            WHERE username = '{user}'"
            cursor.execute(socialProfileQuery)


            for item in cursor.fetchall():
               website = item[1]
               github = item[2]
               twitter = item[3]
               instagram = item[4]
               facebook = item[5]
 
            print(f"{user}'ın fotoğrafı: ",photo[0])
           
            mysql.connection.commit()
            cursor.close()

            uploadPhoto(user)

         except Exception as ex:
            print(f"MySQL Error [{profile.__name__}]: ", ex)


   except Exception as ex:
         print(f"Session Error [{profile.__name__}]: ", ex)
         return redirect(url_for('loggedIn'))

   return render_template("panel/profile/profile.html", login_status = login_status, photo=photo[0],message = message, messageType = "success", user=user, permission=permission, fullname = fullname, phone = phone, address = address, email = email, job = job,
   skill_1_name = skill_1_name, skill_1_value = skill_1_value,
   skill_2_name = skill_2_name, skill_2_value = skill_2_value,
   skill_3_name = skill_3_name, skill_3_value = skill_3_value,
   skill_4_name = skill_4_name, skill_4_value = skill_4_value,
   skill_5_name = skill_5_name, skill_5_value = skill_5_value,
   skill_6_name = skill_6_name, skill_6_value = skill_6_value,
   skill_7_name = skill_7_name, skill_7_value = skill_7_value,
   skill_8_name = skill_8_name, skill_8_value = skill_8_value,
   skill_9_name = skill_9_name, skill_9_value = skill_9_value,
   skill_10_name = skill_10_name, skill_10_value = skill_10_value,
   website = website, github=github, twitter=twitter, instagram = instagram, facebook = facebook)






@app.route("/profile/<string:user>", methods=['POST', 'GET'])
def showProfile(user):
  
   login_status = False
   try:
      cursor = mysql.connection.cursor()
      cursor.execute(f"SELECT username from login WHERE username = '{user}';")
      users = [item[0] for item in cursor.fetchall()]

      cursor.execute(f"SELECT photo from profilephotos \
      WHERE username = '{user}'")

      photo=[item[0] for item in cursor.fetchall()]
           
      if users:
         message = "User matched!"
         
         messageType = "primary"

      contactProfileQuery = f"SELECT * from contactprofile \
      WHERE username = '{user}'"
      cursor.execute(contactProfileQuery)


      for item in cursor.fetchall():
         fullname = item[1]
         phone = item[2]
         address = item[3]
         email = item[4]
         job = item[5]


      skillsProfileQuery = f"SELECT * from skills \
      WHERE username = '{user}'"
      cursor.execute(skillsProfileQuery)

      for item in cursor.fetchall():

         skill_1_name = item[1]
         skill_2_name = item[2]
         skill_3_name = item[3]
         skill_4_name = item[4]
         skill_5_name = item[5]
         skill_6_name = item[6]
         skill_7_name = item[7]
         skill_8_name = item[8]
         skill_9_name = item[9]
         skill_10_name = item[10]

         skill_1_value = item[11]
         skill_2_value = item[12]
         skill_3_value = item[13]
         skill_4_value = item[14]
         skill_5_value = item[15]
         skill_6_value = item[16]
         skill_7_value = item[17]
         skill_8_value = item[18]
         skill_9_value = item[19]
         skill_10_value = item[20]


      socialProfileQuery = f"SELECT * from social \
      WHERE username = '{user}'"
      cursor.execute(socialProfileQuery)


      for item in cursor.fetchall():
         website = item[1]
         github = item[2]
         twitter = item[3]
         instagram = item[4]
         facebook = item[5]
 
         
      mysql.connection.commit()
      cursor.close()

      print(f"{user}'s photo: ",photo[0])



      return render_template("panel/profile/profile.html", login_status = login_status, photo=photo[0],message = message, messageType = messageType, user=user, fullname = fullname, phone = phone, address = address, email = email, job = job,
   skill_1_name = skill_1_name, skill_1_value = skill_1_value,
   skill_2_name = skill_2_name, skill_2_value = skill_2_value,
   skill_3_name = skill_3_name, skill_3_value = skill_3_value,
   skill_4_name = skill_4_name, skill_4_value = skill_4_value,
   skill_5_name = skill_5_name, skill_5_value = skill_5_value,
   skill_6_name = skill_6_name, skill_6_value = skill_6_value,
   skill_7_name = skill_7_name, skill_7_value = skill_7_value,
   skill_8_name = skill_8_name, skill_8_value = skill_8_value,
   skill_9_name = skill_9_name, skill_9_value = skill_9_value,
   skill_10_name = skill_10_name, skill_10_value = skill_10_value,
   website = website, github=github, twitter=twitter, instagram = instagram, facebook = facebook)
   except Exception as ex:
      print(f"MySQL Error [{showProfile.__name__}]: ", ex)
      message = "User not found!"
      messageType = "danger"
  
   return render_template("panel/profile/profile.html", message = message, messageType = messageType, user=user, login_status = login_status)



def allowedFile(filename, extension):

   return '.' in filename and \
           extension in ALLOWED_EXTENSIONS


def uploadPhoto(user):
   print("Request Method: ",request.method)
   if request.method == 'POST': 
    
      if 'file' not in request.files:
         print('File is not selected')
             

     
      file = request.files['file']    
      print("File: ", file)  
      print("Filename: ", file.filename)                
              
      if file.filename == '':
         print('File is not selected')


      extension = file.filename.rsplit('.', 1)[1].lower()
      print("Extension: ", extension)
      # Security
      if file and allowedFile(file.filename, extension):
         
         filename = user + "." + extension
         print("File Name: ", filename)
         file.save(os.path.join(app.config['UPLOAD_FOLDER'] + "/profilephotos", filename))

         cursor = mysql.connection.cursor()

         query = f"UPDATE `profilephotos` SET `username`='{user}',`photo`='{filename}' WHERE username = '{user}';"
         cursor.execute(query)
         
         mysql.connection.commit()
         cursor.close()

         print(f"{user}'s new photo: ", filename)
         #return redirect(url_for('dosyayukleme',dosya=dosyaadi))
         #return redirect('dosyayukleme/' + filename)
      else:
         print('Not allowed extension')
         #return redirect('dosyayukleme')



#endregion profile settings


#region app.run
if __name__ == "__main__":
   app.run(debug=True)
#endregion app.run







# sorgu = "CREATE DATABASE movies"
      # cursor.execute(sorgu)
      #query = "CREATE TABLE IF NOT EXISTS users(title VARCHAR(50) NOT NULL,genre VARCHAR(30) NOT NULL,director VARCHAR(60) NOT NULL,release_year INT NOT NULL,PRIMARY KEY(title));"
      #cursor.execute(query)


      # query = "INSERT INTO kullanicilar VALUES(%s,%s)"
      # cursor.execute(sorgu,(username,password))
      # mysql.connection.commit()
      # cursor.close()



