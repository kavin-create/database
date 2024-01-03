import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import base64
import os
import json

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

    # Check if the username already exists
    if username in user_data['Username'].values:
        st.error("Username already exists. Choose a different username.")
        return user_data

    # Get the index of the available row
    index_point = user_data.index.max() + 1 if not user_data.empty else 0

    # Collect new user information (replace this with your actual data collection code)
    new_entry = pd.DataFrame([[username, password, pageid, access_token]],
                             columns=['Username', 'Password', 'PageID', 'AccessToken'], index=[index_point])

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
        local_file_path = "user_data.xlsx"
        user_data.to_excel(local_file_path, index=False)

        # Read the updated user data from the local file
        with open(local_file_path, "rb") as file:
            content = base64.b64encode(file.read()).decode('utf-8')

        # Get the branch's last commit information
        branch = "main"  # Change this to your branch name if different
        last_commit_info = get_last_commit_info(GITHUB_REPO_OWNER, GITHUB_REPO_NAME, branch)

        # Define the GitHub API URL for creating a new blob
        blob_url = f'https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/git/blobs'

        # Set up headers with authorization and content type
        headers = {
            'Authorization': f'Bearer {GITHUB_ACCESS_TOKEN}',
            'Content-Type': 'application/json',
        }

        # Prepare the data payload for the GitHub API
        data = {
            'content': content,
            'encoding': 'base64',
        }

        # Send a POST request to create a new blob on GitHub
        response = requests.post(blob_url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        blob_info = response.json()

        # Define the GitHub API URL for creating a new tree
        tree_url = f'https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/git/trees'

        # Prepare the data payload for the GitHub API
        tree_data = {
            'base_tree': last_commit_info['commit']['tree']['sha'],
            'tree': [
                {
                    'path': 'user_data.xlsx',
                    'mode': '100644',
                    'type': 'blob',
                    'sha': blob_info['sha'],
                }
            ],
        }

        # Send a POST request to create a new tree on GitHub
        response = requests.post(tree_url, headers=headers, data=json.dumps(tree_data))
        response.raise_for_status()
        tree_info = response.json()

        # Define the GitHub API URL for creating a new commit
        commit_url = f'https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/git/commits'

        # Prepare the data payload for the GitHub API
        commit_data = {
            'message': 'Update user_data.xlsx',
            'tree': tree_info['sha'],
            'parents': [last_commit_info['sha']],
        }

        # Send a POST request to create a new commit on GitHub
        response = requests.post(commit_url, headers=headers, data=json.dumps(commit_data))
        response.raise_for_status()
        new_commit_info = response.json()

        # Update the reference (branch) to point to the new commit
        update_branch_reference(GITHUB_REPO_OWNER, GITHUB_REPO_NAME, branch, new_commit_info['sha'])

        print("File uploaded successfully.")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Function to get the information of the last commit on a branch
def get_last_commit_info(owner, repo, branch):
    url = f'https://api.github.com/repos/{owner}/{repo}/commits/{branch}'
    headers = {
        'Authorization': f'Bearer {GITHUB_ACCESS_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

# Function to update the branch reference to a new commit
def update_branch_reference(owner, repo, branch, commit_sha):
    url = f'https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch}'
    headers = {
        'Authorization': f'Bearer {GITHUB_ACCESS_TOKEN}',
        'Content-Type': 'application/json',
    }
    data = {
        'sha': commit_sha,
        'force': True  # Required to force-update the branch reference
    }
    response = requests.patch(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()

# Function to get the SHA of the last commit on a branch
def get_last_commit_sha(owner, repo, branch):
    url = f'https://api.github.com/repos/{owner}/{repo}/commits/{branch}'
    headers = {
        'Authorization': f'Bearer {GITHUB_ACCESS_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['sha']

# Function to get the SHA of a file on GitHub
def get_file_sha(owner, repo, file_path):
    url = f'https://api.github.com/repos/{owner}/{repo}/contents/{file_path}'
    headers = {
        'Authorization': f'Bearer {GITHUB_ACCESS_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['sha']

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
