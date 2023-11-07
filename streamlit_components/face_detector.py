from .functions import *


def face_chooser(image, faces):
    st.write("")
    st.write("Detecting faces...")
    # Detect faces initially without drawing them
    _, detected_faces = detect_faces(image.copy(), show_faces=None)
    col2, col1 = st.columns([3, 1])
    col3, col4 = st.columns([3,1])
    if len(detected_faces) > 0:
        # Ensure show_faces is initialized with the correct length
        if "show_faces" not in st.session_state or len(st.session_state.show_faces) != len(detected_faces):
            st.session_state.show_faces = [True] * len(detected_faces)
        labaled_face = []
        # Display toggle buttons for each face
        for i in range(len(detected_faces)):
            with col1:
                face_text = st.text_input(f"Detected Face {i+1}")
                labaled_face.append(face_text)
        # Ensure show_faces has correct length
        show_faces = st.session_state.get("show_faces", [True] * len(detected_faces))
        # Detect and render faces based on show_faces list
        processed_image, _ = detect_faces(image.copy(), show_faces)
        if col1.button('Swap Faces'):
            st.session_state.swapped_faces = swap_faces(image, faces, detected_faces, labaled_face)

        col2.image(processed_image, caption="Detected Faces.", use_column_width=True)
        if len(detected_faces) == len(labaled_face):
            return col3,  col4
        
        
    else:
        st.write("No faces detected!")
