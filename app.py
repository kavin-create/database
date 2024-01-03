import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import base64
import os

# Load GitHub access token from environment variable
GITHUB_ACCESS_TOKEN = os.environ.get("KEY")

# GitHub repository information
GITHUB_REPO_OWNER = "kavin-create"
GITHUB_REPO_NAME = "database"

# Function to create or load the user data Excel file
def initialize_user_data():
    try:
        # Download user_data.xlsx from GitHub
        url = f'https://raw.githubusercontent.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/main/user_data.xlsx'
        response = requests.get(url)
        response.raise_for_status()
        user_data = pd.read_excel(BytesIO(response.content))

        # If 'PageID' column contains both numeric and non-numeric values, keep it as an object (string)
        user_data['PageID'] = user_data['PageID'].astype(str)

        if not isinstance(user_data, pd.DataFrame):
            raise ValueError("Invalid data loaded. Expected a DataFrame.")
    except (requests.RequestException, pd.errors.EmptyDataError, ValueError) as e:
        print(f"An error occurred while initializing user_data: {e}")
        columns = ['Username', 'Password', 'PageID', 'AccessToken']
        user_data = pd.DataFrame(columns=columns)
        upload_user_data(user_data)

    return user_data

def new_user_login(username, password, pageid, access_token):
    user_data = initialize_user_data()

    # Collect new user information (replace this with your actual data collection code)
    new_entry = pd.DataFrame([[username, password, pageid, access_token]],
                             columns=['Username', 'Password', 'PageID', 'AccessToken'])

    # Concatenate the new entry to the original DataFrame
    user_data = pd.concat([user_data, new_entry])

    # Ensure 'PageID' column is of type object (string)
    user_data['PageID'] = user_data['PageID'].astype(str)

    # Save the updated user data to the Excel file and upload to GitHub
    upload_user_data(user_data)

    st.write("Type of user_data after append:", type(user_data))
    st.write("Contents of user_data after append:", user_data)
    st.success("Login successful! Data saved.")

    return user_data

# Function to upload user data to GitHub
def upload_user_data(user_data):
    try:
        # Save the updated user data to the local file
        user_data.to_excel("user_data.xlsx", index=False)

        # Read the updated user data from the local file
        with open("user_data.xlsx", "rb") as file:
            content = base64.b64encode(file.read()).decode('utf-8')

        # Define the GitHub API URL for updating the file
        url = f'https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/user_data.xlsx'

        # Set up headers with authorization and content type
        headers = {
            'Authorization': f'Bearer {GITHUB_ACCESS_TOKEN}',
            'Content-Type': 'application/json',
        }

        # Prepare the data payload for the GitHub API
        data = {
            'message': 'Update user_data.xlsx',
            'content': content
        }

        # Send a PUT request to update the file on GitHub
        response = requests.put(url, headers=headers, json=data)
        response.raise_for_status()
        print("File uploaded successfully.")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

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
