import streamlit as st
import os
import traceback
from utilities.helper import LLMHelper
import streamlit.components.v1 as components
from urllib import parse
import requests
import json

def delete_embeddings_of_file(file_to_delete):
    # Query RediSearch to get all the embeddings - lazy loading
    if 'data_files_embeddings' not in st.session_state:
        st.session_state['data_files_embeddings'] = llm_helper.get_all_documents(k=1000)

    if st.session_state['data_files_embeddings'].shape[0] == 0:
        return

    for converted_file_extension in ['.txt']:
        file_to_delete = 'converted/' + file_to_delete + converted_file_extension

        embeddings_to_delete = st.session_state['data_files_embeddings'][st.session_state['data_files_embeddings']['filename'] == file_to_delete]['key'].tolist()
        embeddings_to_delete = list(map(lambda x: f"{x}", embeddings_to_delete))
        if len(embeddings_to_delete) > 0:
            llm_helper.vector_store.delete_keys(embeddings_to_delete)
            # remove all embeddings lines for the filename from session state
            st.session_state['data_files_embeddings'] = st.session_state['data_files_embeddings'].drop(st.session_state['data_files_embeddings'][st.session_state['data_files_embeddings']['filename'] == file_to_delete].index)

def delete_file_and_embeddings(filename=''):
    # Query RediSearch to get all the embeddings - lazy loading
    if 'data_files_embeddings' not in st.session_state:
        st.session_state['data_files_embeddings'] = llm_helper.get_all_documents(k=1000)

    if filename == '':
        filename = st.session_state['file_and_embeddings_to_drop'] # get the current selected filename
    
    file_dict = next((d for d in st.session_state['data_files'] if d['filename'] == filename), None)

    if len(file_dict) > 0:
        # delete source file
        source_file = file_dict['filename']
        try:
            llm_helper.blob_client.delete_file(source_file)
        except Exception as e:
            st.error(f"Error deleting file: {source_file} - {e}")

        # delete converted file
        if file_dict['converted']:
            converted_file = 'converted/' + os.path.splitext(source_file)[0].replace(' ', '_') + '.txt'
            try:
                llm_helper.blob_client.delete_file(converted_file)
            except Exception as e:
                st.error(f"Error deleting file : {converted_file} - {e}")

        # delete embeddings
        if file_dict['embeddings_added']:
            # converted_file = 'converted/json/' + os.path.splitext(source_file)[0].replace(' ', '_') + '.json'
            # try:
            #     llm_helper.blob_client.delete_file(converted_file)
            # except Exception as e:
            #     st.error(f"Error deleting file : {converted_file} - {e}")
            delete_embeddings_of_file(parse.quote(filename))
    
    # update the list of filenames to remove the deleted filename
    st.session_state['data_files'] = [d for d in st.session_state['data_files'] if d['filename'] != '{filename}']


def delete_all_files_and_embeddings():
    files_list = st.session_state['data_files']
    for filename_dict in files_list:
        delete_file_and_embeddings(filename_dict['filename'])

def handle_embeddings():

    filename = st.session_state['file_and_embeddings_to_drop']

    if filename != '' and len(st.session_state['data_files']) > 0:
        file_dict = next((d for d in st.session_state['data_files'] if d['filename'] == filename), None)

        download_filename = os.path.splitext(file_dict["filename"])[0].replace(' ', '_') + ".json"

        fileLink = f"https://{account_name}.blob.core.windows.net/{container_name}/converted/json/{download_filename}"

        print('fileLink --->', fileLink)

        response = requests.get(fileLink)

        if response.status_code == 200:
            st.text("")
            st.download_button(label='Download Json File',  file_name=f"{download_filename}", data=response.content)
        else:
            print(response.status_code)

def handleDelete():

    filename = st.session_state['file_and_embeddings_to_drop']

    filename = os.path.splitext(filename)[0] + '.json'

    os.remove(filename)

def handleText():
    filename = st.session_state['file_and_embeddings_to_drop']

    if filename != '' and len(st.session_state['data_files']) > 0:

        file_dict = next((d for d in st.session_state['data_files'] if d['filename'] == filename), None)

        converted_filename = os.path.splitext(file_dict['filename'])[0].replace(' ', '_') + '.txt'

        fileLink = f"https://{account_name}.blob.core.windows.net/{container_name}/converted/{converted_filename}"

        response = requests.get(fileLink)

        if response.status_code == 200:
            st.text("")
            st.download_button(label='Download Text File',  file_name=f"{converted_filename}", data=response.content)
        else:
            print(response.status_code)

def process_all_files():
    
    for file in st.session_state['data_files']:
        if not file['converted']:
            converted_filename = llm_helper.convert_file_and_add_embeddings(file['fullpath'], file['filename'], False)

            llm_helper.blob_client.upsert_blob_metadata(file['filename'], {'converted': 'true', 'embeddings_added': 'true', 'converted_filename': parse.quote(converted_filename)})
            st.success(f"File {file['filename']} embeddings added to the knowledge base.")

try:
    # Set page layout to wide screen and menu item
    menu_items = {
	'Get help': None,
	'Report a bug': None,
	'About': '''
	 ## Embeddings App

	Document Reader Sample Demo.
	'''
    }
    st.set_page_config(layout="wide", menu_items=menu_items)

    hide_streamlit_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                </style>
                """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

    llm_helper = LLMHelper()


    st.session_state['data_files'] = llm_helper.blob_client.get_all_files()
    st.session_state['data_files_embeddings'] = llm_helper.get_all_documents(k=1000)

    account_name : str = os.getenv('BLOB_ACCOUNT_NAME')
    container_name : str = os.getenv('BLOB_CONTAINER_NAME')

    if len(st.session_state['data_files']) == 0:
        st.warning("No files found. Go to the 'Add Document' tab to insert your docs.")

    else:
        st.dataframe(st.session_state['data_files'])

        st.text("")
        st.text("")
        st.text("")

        filenames_list = [d['filename'] for d in st.session_state['data_files']]
        st.selectbox("Select File", filenames_list, key="file_and_embeddings_to_drop")

        st.text("")
        st.button("Process all files", on_click=process_all_files)
        
        st.text("")
        st.button("Generate Text File", on_click=handleText)
        
        # st.text("")
        # st.button("Generate Embeddings", on_click=handle_embeddings)
        
        st.text("")
        st.button("Delete file and its embeddings", on_click=delete_file_and_embeddings)

        st.text("")
        if len(st.session_state['data_files']) > 1:
            st.button("Delete all files (with their embeddings)", type="secondary", on_click=delete_all_files_and_embeddings, args=None, kwargs=None)

except Exception as e:
    st.error(traceback.format_exc())
