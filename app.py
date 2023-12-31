from flask import Flask, request, render_template, jsonify

import boto3

import dynamoDB_handler as dynamodb
import urllib.parse

app = Flask(__name__)


s3 = boto3.resource(
    's3',
    aws_access_key_id     = keys.ACCESS_KEY_ID,
    aws_secret_access_key = keys.ACCESS_SECRET_KEY,
    region_name           = 'us-east-1',
)

@app.route('/')#decorator for home page
def root_route():
    # dynamodb.create_table()
    # return 'Table Created'
    return render_template("index.html")
    

    
@app.route('/login') # decorator for login page
def login():    
    return render_template('login.html')
    
@app.route('/register') # decorator for sign up page
def register():    
    return render_template('sign_up.html')

@app.route('/sign_up', methods=['POST'])    
def add_user():
    # Extract data from the form
    data = request.form.to_dict()
    
    # calling below function to add user data
    response = dynamodb.add_item_to_user_table(int(data['regno']), data['fullname'], data['email'],
     data['password'], data['degree'], data['contact'], data['introduction'], data['gpa'], data['skills'])
     
    if 'error' in response:
        error_msg = response['error']
        return render_template('sign_up.html', error_msg=error_msg)
  
  # check whether response passed below condition
    if (response['ResponseMetadata']['HTTPStatusCode'] == 200):
        msg = "Registration Complete. Please Login to your account !"
        return render_template('login.html', msg = msg)

    # if there is an error
    return {  
        'msg': 'Some error occcured',
        'response': response
    }

@app.route('/check', methods=['POST'])
def check_user():
    # Extract data from the form
    data = request.form.to_dict()
    
    #calling below function to check user exist
    response = dynamodb.check_users(data['email'], data['password'])
    items = response['Items']
    
    #if user exists with given email
    if items:
        
        item = items[0]
        
        if data['password'] == item['password']:
                
            return render_template("profile.html", item = item)
            
        errormsg = "Invalid Password!"
        return render_template("login.html", errormsg = errormsg)
    
    #if user doesn't exist with given email
    else:
        errormsg2 = "Invalid E-mail!"
        return render_template("login.html", errormsg2 = errormsg2)
        
@app.route('/student/<int:regno>', methods=["PUT"])
def update_user(regno):
    
    # get the json data passed from the client side
    data = request.get_json()
    
    # calling below function to update student details
    response = dynamodb.update_item_from_Student_table(data)
    
    # check whether update is successfull
    if (response['ResponseMetadata']['HTTPStatusCode'] == 200):
        return {
            'msg'                : 'Updated successfully',
            'ModifiedAttributes' : response['Attributes'],
            'response'           : response['ResponseMetadata']
        }
    # if update is not successfull
    return {
        'msg'      : 'Some error occured',
        'response' : response
    }  
    
    
@app.route('/profile/<int:rNo>', methods=["GET"])
def get_student(rNo):
    
    # calling below function to get student details according to the register number
        response = dynamodb.get_item_from_Student_table(rNo)
        users = response['Items']
        try:
            users = users[0]
        
            if  response['ResponseMetadata']['HTTPStatusCode'] == 200:
        
                if users:
                    # render porfile view with users details
                    return render_template("profile-view.html", users=users)
            
        except IndexError:
            
            #Out of index error
            error_reg = "There are not any student with this " + str(rNo);
            return;
    
        return {
            'msg': 'Some error occured',
            'response': response
        }
    
@app.route('/upload', methods=['POST'])
def upload():
    email = request.form.get('hidden-email')
    file = request.files['std-img']
    filename = file.filename
    bucket_name = 'studentimageflaskbucket'
    bucket = s3.Bucket(bucket_name)
    bucket.put_object(
        Key=filename,
        Body=file,
        ContentType='image/jpeg',
        ContentDisposition='inline'
    )
    # print(email)
    
    encoded_object_key = urllib.parse.quote(filename)
    object_url = f"https://{bucket_name}.s3.amazonaws.com/{encoded_object_key}"
    #return "successfully updated"
    
    response = dynamodb.update_image_url(email, object_url)
    
    if (response['ResponseMetadata']['HTTPStatusCode'] == 200):
         return {
            'msg'                : 'Updated successfully',
            'ModifiedAttributes' : response['Attributes'],
            'response'           : response['ResponseMetadata']
        } 
    # if update is not successfull
    return 'error is occured'
    return render_template("profile-view.html")

#define port and host
if __name__ == '__main__':
    app.run()
