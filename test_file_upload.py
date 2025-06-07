"""
Test script to debug the /api/chat/query-with-file endpoint issue.
This script sends a request similar to what the frontend would send.
"""
import requests
import os

# Set the API base URL
base_url = 'http://localhost:8000'
endpoint = '/api/chat/query-with-file'

# Set up a test file
test_file_path = os.path.join(os.getcwd(), 'data', 'test_document.txt')
if not os.path.exists(test_file_path):
    # Create test file if it doesn't exist
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write("This is a test document for file upload testing.")

# Test auth token - replace with a valid token if you have one
token = "YOUR_AUTH_TOKEN_HERE"  # You'll need to replace this with a valid token

# Set up the request data
with open(test_file_path, 'rb') as file:
    # Use proper form data format with 'file' and 'query' fields
    files = {'file': file}
    data = {'query': 'What is in this document?'}
    
    # Optional: Add conversation_id if continuing an existing conversation
    # data['conversation_id'] = 'some-conversation-id'
    
    # Send request
    headers = {'Authorization': f'Bearer {token}'}
    
    print(f"Sending request to {base_url + endpoint}")
    print(f"Data: {data}")
    print(f"Files: {files}")
    
    response = requests.post(
        base_url + endpoint,
        headers=headers,
        data=data,
        files=files
    )
    
    print(f"Response status code: {response.status_code}")
    
    # If response was successful, print the response
    if response.status_code == 200:
        print("Success!")
        print(response.json())
    else:
        # If there was an error, print the response body for debug info
        print(f"Error: {response.status_code}")
        print(f"Response body: {response.text}")
