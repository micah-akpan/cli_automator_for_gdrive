#!venv/bin/python

from __future__ import print_function
import pickle
import os.path
from typing import Any
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']


def make_copy(gdrive_service, fileId: str):
    """
    Makes a copy of {filename} in the drive
    """
    copied_file = gdrive_service.files().copy(
        fileId=fileId, fields='id,name,mimeType,parents').execute()

    return copied_file


def create_new_folder(gdrive_service, folder_name: str):
    """
      Create a copy of {folder_name} folder in the drive
    """
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    new_folder = gdrive_service.files().create(
        body=file_metadata, fields='id').execute()

    return new_folder


def get_file_to_be_copied(filename: str, items: list) -> str:
    """
      Returns the id of the file: {filename} to be copied
    """
    selected_files = list(filter(
        lambda file: file['name'] == filename, items))
    fileId = selected_files[0].get('id', '')
    return fileId


def get_list_of_files(gdrive_service):
    """
    Returns a list of all files
    """
    files = gdrive_service.files().list(fields="nextPageToken, files(id, name)",
                                        supportsAllDrives=True).execute()
    return files.get('files', [])


def get_request_service():
    """
      Authenticates the user and returns the service that encapsulates the
      user authenticated session
    """
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds)
    return service


def create_doc_template(gdrive_service, file_to_be_copied_name: str, folder_name: str, move_to_folder=True):

    files = get_list_of_files(gdrive_service)

    fileId = get_file_to_be_copied(file_to_be_copied_name, files)
    copied_file = make_copy(gdrive_service, fileId)
    new_folder = create_new_folder(gdrive_service, folder_name)

    # file copied, move copied_file into the desired_folder
    previous_parents = ",".join(copied_file.get('parents', ''))

    # move the copied file to the new folder
    newly_moved_file = gdrive_service.files().update(fileId=copied_file.get('id'),
                                                     addParents=new_folder.get(
        'id'),
        removeParents=previous_parents,
        fields='id, parents').execute()

    return f'You have a new copy with id: {newly_moved_file.get("id")} created'


def main():
    filename = ''  # this and the folder name, if specified will come from the command line
    gdrive_service = get_request_service()
    copy_msg = create_doc_template(
        gdrive_service, '[Lambda] Labs Web Final Template', 'John Wick 3')

    print(copy_msg)


if __name__ == '__main__':
    main()
