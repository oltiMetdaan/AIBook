from .functions import *
import streamlit as st
from .face_detector import *
from os import listdir
from os.path import isfile, join
import sys

sys.path.append('C:/Users/user1/Documents/Work/AIBook')

from classes.cartoonize import cartoonize
def generate_view(data):
    
    prew1, prew2, prew3, prew4 = st.columns([1,1,1,2])
    option_story = prew1.selectbox("Choose the Story", data["stories"])
    option_page = prew1.selectbox("Choose the Page", data["stories"][option_story])
    st.session_state.option_story = option_story
    st.session_state.option_page = option_page
    
    location = prew2.text_input("Location:")
    time = prew2.text_input("Time:")
    mood = prew2.text_input("Mood:")
    other_details = prew2.text_input("Other Details:")
    
    uploaded_faces = prew3.file_uploader(
        "Upload Faces",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        help="Upload up to 3 images.",
    )
    if uploaded_faces:
        if len(uploaded_faces) > 3:
            prew3.warning("Please upload only up to 3 images.")
        display_uploaded_images(uploaded_faces[:3], prew4)
    if prew3.button("Generate Images"):
        response_data = get_image_from_api(
            f"""{data["stories"][option_story][option_page]["url"]
            } {generate_detailed_prompt(location, time, mood, other_details)
            } {data["stories"][option_story][option_page]["prompt"].split('--')[0]} --ar 2:1 --chaos 0 --no animated, sunglasses --v 5.2 --style raw"""
        )
        print(response_data)
        
        messageId = response_data["messageId"]
        progress = 0
        progress_bar = st.progress(0)
        while progress != 100:
            import time
            time.sleep(1)
            response_progress = get_image_progress(messageId)
            progress = response_progress["progress"]
            progress_bar.progress(progress)
        st.session_state.images = response_progress["response"]["imageUrls"]
        st.session_state.button_url = response_progress["response"]["buttonMessageId"]
        st.session_state.selected_image = None

        #
        st.warning("Internal Error. Please generate again.")

    if "images" in st.session_state:
        display_images(st.session_state.images)
        if st.session_state.get("selected_image") and st.button("Detect Faces"):
            st.session_state.face_image = download_image(st.session_state.get("button_url"), str(int(st.session_state.get("selected_image")[-5:-4]) + 1))
            st.experimental_rerun()

    if 'face_image' in st.session_state:
        col3, col4 = face_chooser(st.session_state.face_image,uploaded_faces)


    if 'swapped_faces' in st.session_state:
        col3.image(st.session_state.swapped_faces, caption="Swapped Faces", use_column_width=True)
        st.session_state.animation_style = col4.selectbox(
            "Animation Style",
            ["None", "Painting"]
        )
        if col4.button('Animate'): #Pil Image
            if  st.session_state.get("animation_style") == "Painting" :
                st.session_state.animated_image = cartoonize(st.session_state.swapped_faces)
            elif st.session_state.get("animation_style") == "None": 
                st.session_state.animated_image = st.session_state.swapped_faces

    if "animated_image" in st.session_state:
        col5 , col6 = st.columns([3,1])
        col5.image(st.session_state.get("animated_image"))
        st.session_state.font = col6.selectbox(
            "Font", [f.split('.')[0] for f in listdir("./fonts") if isfile(join('./fonts', f))]
        )
        st.session_state.font_size = col6.number_input(
            "Font Size", value = 40, step = 2
            )
        st.session_state.name = col6.text_input("Character Name")
        st.session_state.pronoun = col6.selectbox("Pronouns", ["","He","She","They"])
        
            
        if st.session_state.get("name") != "" and st.session_state.get("pronoun") != "":
            st.session_state.page_text = fix_story(
                data["stories"][option_story][option_page]['description'],
                st.session_state.get('name'), 
                st.session_state.get('pronoun'))
            
            st.session_state.image_with_text = add_text_to_image(
                st.session_state.get("animated_image"),
                st.session_state.get("page_text"),
                st.session_state.get("font"),
                st.session_state.get("font_size")
            ).convert("RGB")
            col7, col8 = st.columns([3,1])
            roi_img = st.session_state.get('image_with_text')
            col7.image(roi_img)
            img_byte_arr = io.BytesIO()
            roi_img.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            col8.download_button(
                label="Download Image",
                data=img_byte_arr,
                    file_name=f"{option_story} {option_page}.png",
                    mime="image/png"
                  )