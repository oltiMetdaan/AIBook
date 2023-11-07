from streamlit_components.generate_story import generate_view
from streamlit_components.config_story import create_config
from streamlit_option_menu import option_menu
import streamlit as st
import json


def load_data():
    with open("streamlit_data.json", "r") as f:
        return json.load(f)


def app():
    st.set_page_config(layout="wide")
    data = load_data()

    option = option_menu(
        menu_title = "AI Book Creator",
        options=[
            "Generate Personalized Book",
            "Book Configuration"
        ],
        icons=[
            "book",
            "gear"
        ],
        default_index = 0,
        orientation = "horizontal"
        )
    if option == "Generate Personalized Book":
        generate_view(data)
    
    elif option == "Book Configuration":
        create_config(data)

    hide_st_style = """
                <style>
                #MainMenu {visibility:hidden;}
                footer {visibility:hidden;}
                .block-container {padding-top:50px;}
                """
                
    st.markdown(hide_st_style, unsafe_allow_html=True)

if __name__ == "__main__":
    app()
