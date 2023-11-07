import streamlit as st
from .functions import *


def create_config(data):
    try:
        buttons = {}
        story_list = list(data["stories"].keys())
        headers = st.columns([3,2,1,3,2])
        selected_story = headers[0].selectbox("Choose a story to edit:", story_list)
        headers[1].subheader('')
        if headers[1].button(f"Delete Story"):
            del data["stories"][selected_story]
            save_data(data)
            st.experimental_rerun()
        # Select a page to edit
        new_story = headers[3].text_input('New Story title')
        headers[4].subheader('')
        if headers[4].button('Create Story'):
            data['stories'][new_story] = {}
            save_data(data)
            headers[3].success(f"Saved edits for {selected_story}")
            time.sleep(1)
            st.experimental_rerun()

        page_list = list(data["stories"][selected_story].keys())
        edited_data = {}
        for selected_page in page_list:
            edited_data[selected_page] = {}
            # Display the current values of the selected page
            st.subheader(f"Editing {selected_page}")
            edited_data[selected_page]["url"] = st.text_input(
                f"Reference Image URL {selected_page}:",
                value=data["stories"][selected_story][selected_page]["url"],
            )
            edited_data[selected_page]["prompt"] = st.text_input(
                f"Prompt {selected_page}:",
                value=data["stories"][selected_story][selected_page]["prompt"],
            )
            edited_data[selected_page]["description"] = st.text_area(
                f"Page Text {selected_page}:",
                value=data["stories"][selected_story][selected_page]["description"],
            )
            buttons[selected_page] = st.columns(8)
            

            if buttons[selected_page][0].button(f"Delete Page {selected_page}"):
                # Delete the selected page
                del data["stories"][selected_story][selected_page]

                # Rename the subsequent pages
                current_page_number = int(
                    selected_page.split(" ")[1]
                )  # Extract the number from "Page X"
                for i in range(current_page_number + 1, len(page_list) + 1):
                    old_name = f"Page {i}"
                    new_name = f"Page {i - 1}"
                    data["stories"][selected_story][new_name] = data["stories"][
                        selected_story
                    ][old_name]
                    del data["stories"][selected_story][old_name]

                save_data(data)
                st.success(
                    f"Deleted {selected_page} and renamed subsequent pages."
                )
                st.experimental_rerun()
    except KeyError:
        st.warning(
            "There was an error loading the data. Please ensure your data structure is correct."
        )
    # Add a new page
    st.header('New Page')
    new_url = st.text_input("New Reference Image URL:")
    new_prompt = st.text_input("New Prompt:")
    new_description = st.text_area("New Page Text:")
    add, edit, _, _, _, _, _, _, _, _ = st.columns(10)
    if add.button("Add New Page"):
        # Calculate the next page number
        current_pages = list(data["stories"][selected_story].keys())
        next_page_num = len(current_pages) + 1
        page_name = f"Page {next_page_num}"
        # Add to the data structure
        data["stories"][selected_story][page_name] = {
            "url": new_url,
            "prompt": new_prompt,
            "description": new_description,
        }
        # Save the data back to the file
        save_data(data)
        st.success(f"Added {page_name} to {selected_story}")
        st.experimental_rerun()
    if edit.button(f"Save Edits"):
        for selected_page in list(edited_data.keys()):
            # Save the edited values
            
            data["stories"][selected_story][selected_page]["url"] = edited_data[selected_page]['url']
            data["stories"][selected_story][selected_page]["prompt"] = edited_data[selected_page]['prompt']
            data["stories"][selected_story][selected_page]["description"] = edited_data[selected_page]['description']
        save_data(data)
        st.success(f"Saved edits for {selected_story}")
        time.sleep(1)
        st.experimental_rerun()
        # Button to delete the selected page and rename subsequent pages