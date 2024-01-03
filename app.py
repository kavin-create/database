import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import base64
# GitHub repository information
GITHUB_REPO_OWNER = "deepakskepit"
GITHUB_REPO_NAME = "test_automate"
GITHUB_ACCESS_TOKEN = "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"  # Make sure to keep this secure

# Function to create or load the user data Excel file
def initialize_user_data():
    try:
        # Download user_data.xlsx from GitHub
        url = f'https://raw.githubusercontent.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/main/user_data.xlsx'
        response = requests.get(url)
        response.raise_for_status()
        user_data = pd.read_excel(BytesIO(response.content))
    except (requests.RequestException, pd.errors.EmptyDataError):
        columns = ['Username', 'Password', 'PageID', 'AccessToken']
        user_data = pd.DataFrame(columns=columns)
        upload_user_data(user_data)
    except Exception as e:
        print(f"An error occurred while initializing user_data: {e}")
        user_data = pd.DataFrame(columns=['Username', 'Password', 'PageID', 'AccessToken'])
    
    return user_data

def new_user_login(username, password, pageid, access_token):
    user_data = initialize_user_data()
    print("Type of user_data before append:", type(user_data))
    print("Contents of user_data before append:", user_data)
    
    new_entry = pd.DataFrame([[username, password, pageid, access_token]],
                             columns=['Username', 'Password', 'PageID', 'AccessToken'])
    
    user_data = user_data.append(new_entry, ignore_index=True)
    print("Type of user_data after append:", type(user_data))
    print("Contents of user_data after append:", user_data)
    
    upload_user_data(user_data)
    return user_data

# Function to upload user data to GitHub
def upload_user_data(user_data):
    user_data.to_excel("user_data.xlsx", index=False)
    with open("user_data.xlsx", "rb") as file:
        content = base64.b64encode(file.read()).decode('utf-8')
    
    url = f'https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/user_data.xlsx'
    headers = {
        'Authorization': f'Bearer {GITHUB_ACCESS_TOKEN}',
        'Content-Type': 'application/json',
    }
    data = {
        'message': 'Update user_data.xlsx',
        'content': content
    }
    response = requests.put(url, headers=headers, json=data)
    response.raise_for_status()

# Function to handle login for new user
#def new_user_login(username, password, pageid, access_token):
#    user_data = initialize_user_data()
#    new_entry = pd.DataFrame([[username, password, pageid, access_token]],
#                             columns=['Username', 'Password', 'PageID', 'AccessToken'])
#    user_data = user_data.append(new_entry, ignore_index=True)
#    upload_user_data(user_data)
#    return user_data

# Function to handle login for existing user
def existing_user_login(username):
    user_data = initialize_user_data()
    user_row = user_data[user_data['Username'] == username]
    if not user_row.empty:
        password = user_row.iloc[0]['Password']
        pageid = user_row.iloc[0]['PageID']
        access_token = user_row.iloc[0]['AccessToken']
        return password, pageid, access_token
    else:
        st.error("User not found. Please check the username.")

# Streamlit app
def main():
    st.title("GitHub Integrated Facebook Login App")

    # User selection: New user or Existing user
    user_type = st.radio("Select User Type", ('New User', 'Existing User'))

    # New user registration
    if user_type == 'New User':
        st.header("New User Registration")

        # Input fields
        username = st.text_input("Enter Username:")
        password = st.text_input("Enter Password:", type='password')
        pageid = st.text_input("Enter PageID:")
        access_token = st.text_input("Enter Access Token:")

        # Login button
        if st.button("Login"):
            user_data = new_user_login(username, password, pageid, access_token)
            st.success("Login successful! Data saved.")

    # Existing user login
    elif user_type == 'Existing User':
        st.header("Existing User Login")

        # Input field
        existing_username = st.text_input("Enter Username:")

        # Login button
        if st.button("Login"):
            password, pageid, access_token = existing_user_login(existing_username)
            if password is not None:
                st.success("Login successful!")
                st.write(f"Username: {existing_username}")
                st.write(f"Password: {password}")
                st.write(f"PageID: {pageid}")
                st.write(f"Access Token: {access_token}")

if __name__ == '__main__':
    main()
