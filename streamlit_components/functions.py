import streamlit as st
import requests
import json
import time
import io
import cv2
import numpy as np
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import random

MAIN_URL = "https://api.thenextleg.io/v2/"
HEADERS = {
    "Authorization": "Bearer 947c9027-64b2-4607-868d-7ea215fbf61e",
    "Content-Type": "application/json",
}
download_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
}

# Load the cascade
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

cwd = os.getcwd() + "/"


def generate_detailed_prompt(location, time, mood, other_details):
    final = ""
    if location != "":
        final += f"Location: {location} "
    if time != "":
        final += f"Time: {time} "
    if mood != "":
        final += f"Mood: {mood} "
    if other_details != "":
        final += f"Other Details: {other_details} "
    return final


def add_border(input_image, border_size):
    # Input image dimensions
    width, height = input_image.size

    # New image dimensions
    new_width = width + 2 * border_size
    new_height = height + 2 * border_size

    # Create a new transparent image with the new dimensions
    bordered_image = Image.new("RGBA", (new_width, new_height), (0, 0, 0, 0))

    # Paste the original image into the center of the new image
    bordered_image.paste(input_image, (border_size, border_size))

    return bordered_image


def color_distance(color1, color2):
    """Calculate the Euclidean distance between two RGB colors."""
    r_diff = color1[0] - color2[0]
    g_diff = color1[1] - color2[1]
    b_diff = color1[2] - color2[2]

    return (r_diff**2 + g_diff**2 + b_diff**2) ** 0.5


def make_black_border_transparent(img, threshold=30):
    img = img.convert("RGBA")
    datas = img.getdata()

    width, height = img.size
    border_pixels = []

    BLACK = (0, 0, 0)

    # Identify black and near-black border pixels
    for y in range(height):
        for x in range(width):
            if color_distance(datas[y * width + x][:3], BLACK) <= threshold:
                border_pixels.append((x, y))

    # Modify identified pixels to transparent
    for pixel in border_pixels:
        img.putpixel(pixel, (0, 0, 0, 0))
        # Add neighboring pixels to ensure we get the edge aliasing
        neighbors = [
            (pixel[0] + dx, pixel[1] + dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1]
        ]
        for neighbor in neighbors:
            if 0 <= neighbor[0] < width and 0 <= neighbor[1] < height:
                img.putpixel(neighbor, (0, 0, 0, 0))

    return img


def detect_faces(image, show_faces=None):
    # Convert the image to grayscale
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)

    # Detect faces
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)

    # Draw rectangles around the faces and number them if they are to be shown
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(f"{cwd}streamlit_components/Roboto-Black.ttf", 25)
    for index, (x, y, w, h) in enumerate(faces):
        if show_faces is None or show_faces[index]:
            draw.rectangle([x, y, x + w, y + h], outline="blue", width=2)
            draw.text((x, y), str(index + 1), fill="red", font=font)

    return image, faces


def swap_faces(image, faces, detected_faces, labaled_faces):
    image.save(f"{cwd}temp_folder/main.png")
    faces = [Image.open(image) for image in faces]
    for idx, face in enumerate(faces):
        face.save(f"{cwd}temp_folder/face{idx+1}.png")
    cropped_faces = [
        image.crop((x, y - 20, x + w, y + h + 20)) for (x, y, w, h) in detected_faces
    ]
    cropped_files = []
    for idx, image in enumerate(cropped_faces):
        add_border(image, 100).save(f"{cwd}temp_folder/cropImage{idx+1}.png")
        cropped_files.append(f"{cwd}temp_folder/cropImage{idx+1}.png")
    swapped_faces = []
    for input_file, label in zip(cropped_files, labaled_faces):
        if label == "":
            swapped_faces.append(Image.open(input_file))
        else:
            base_command = "python classes/run.py"
            source_option = f"--source temp_folder/face{label}.png"
            target_option = f"--target {input_file}"
            output_option = (
                f"--output temp_folder/output{label}.png"  # Customize your output path
            )
            other_options = "--keep-fps --keep-frames --temp-frame-quality 100"  #
            os.system(
                f"{base_command} {source_option} {target_option} {output_option} {other_options}"
            )
            swapped_faces.append(Image.open(f"temp_folder/output{label}.png"))

    main_image = Image.open("temp_folder/main.png")
    for idx, (x, y, h, w) in enumerate(detected_faces):
        mask = make_black_border_transparent(swapped_faces[idx]).split()[3]
        main_image.paste(swapped_faces[idx], (x - 100, y - 120), mask)
    return main_image


def download_image(buttonID, num):
    response = requests.get(
        f"{MAIN_URL}button?buttonMessageId={buttonID}&button=U{num}", headers=HEADERS
    )
    progress = 0
    progress_bar = st.progress(0)
    while progress != 100:
        time.sleep(1)
        response_button = get_image_progress(response.json()["messageId"])
        progress = response_button["progress"]
        progress_bar.progress(int(progress))
    image_bytes = requests.get(response_button["response"]["imageUrl"]).content
    return Image.open(io.BytesIO(image_bytes))


def save_data(data):
    with open("streamlit_data.json", "w") as f:
        json.dump(data, f, indent=4)


def display_uploaded_images(uploaded_images, col):
    upload_image = col.columns(3)
    for index, img in enumerate(uploaded_images):
        upload_image[index].image(img, width=200)
        upload_image[index].write(f"Face {index + 1}")


def get_image_from_api(prompt):
    payload = json.dumps(
        {
            "msg": prompt,
            "ref": "",
            "webhookOverride": "",
            "ignorePrefilter": "false",
        }
    )
    response = requests.post(f"{MAIN_URL}imagine", headers=HEADERS, data=payload)
    print(response)
    return response.json()


def get_image_progress(messageId):
    response = requests.get(f"{MAIN_URL}message/{messageId}", headers=HEADERS)
    return response.json()


def display_images(images, type_display=None):
    cols = st.columns(len(images))
    if type_display == None:
        for idx, (col, url) in enumerate(zip(cols, images)):
            if url == st.session_state.get("selected_image"):
                col.markdown(
                    f"<img src='{url}' style='width: 300px; border: 5px solid red; border-radius:20px;'/>",
                    unsafe_allow_html=True,
                )
            else:
                col.markdown(
                    f"<img src='{url}' style='width: 300px;  border-radius:20px;'/>",
                    unsafe_allow_html=True,
                )
            clicked = col.button(f"Select Image {idx + 1}")
            if clicked:
                st.session_state.selected_image = url
                st.experimental_rerun()
    else:
        for idx, (col, url) in enumerate(zip(cols, images)):
            if url == st.session_state.get("anim_selected_image"):
                col.markdown(
                    f"<img src='{url}' style='width: 300px; border: 5px solid red; border-radius:20px;'/>",
                    unsafe_allow_html=True,
                )
            else:
                col.markdown(
                    f"<img src='{url}' style='width: 300px;  border-radius:20px;'/>",
                    unsafe_allow_html=True,
                )
            clicked = col.button(f"Select Animated Image {idx + 1}")
            if clicked:
                st.session_state.anim_selected_image = url
                st.experimental_rerun()


def post_image_discord(image):
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format="PNG")
    img_byte_arr = img_byte_arr.getvalue()

    webhook = "https://discord.com/api/webhooks/1145980484711612476/XkbQtaW4Kn7oigvruxPMC6fnTyJcJF5wrJHUoaCUhW2tBLRL5WlXI4FaiE_s-mo733B_"

    data = {"content": "Uploading a file..."}

    files = {"file": ("filename.jpg", img_byte_arr)}

    response = requests.post(webhook, files=files, data=data)
    if response.status_code == 200:
        json_response = response.json()
        file_url = json_response["attachments"][0]["url"]
        return file_url
    else:
        return f"Error {response.status_code}: {response.text}"


def generate_pdf(images):
    file_name = f"test{time.time()}.pdf"
    try:
        images[0].save(file_name, save_all=True, append_images=images[1:])
    except:
        images[0].save(file_name, save_all=True)
    with open(file_name, "rb") as f:
        pdf_bytes = f.read()
    return pdf_bytes


def fix_story(story: str, name: str, pronoun: str):
    story = story.replace("{name}", name)
    if pronoun.lower() == "he":
        story = story.replace(".{pronoun1}", ". He")
        story = story.replace(". {pronoun1}", ". He")
        story = story.replace("{pronoun1}", "he")
        story = story.replace(".{pronoun2}", ". Him")
        story = story.replace(". {pronoun2}", ". Him")
        story = story.replace("{pronoun2}", "him")
        story = story.replace(".{pronoun3}", ". His")
        story = story.replace(". {pronoun3}", ". His")
        story = story.replace("{pronoun3}", "his")
    elif pronoun.lower() == "she":
        story = story.replace(".{pronoun1}", ". She")
        story = story.replace(". {pronoun1}", ". She")
        story = story.replace("{pronoun1}", "she")
        story = story.replace(".{pronoun2}", ". Her")
        story = story.replace(". {pronoun2}", ". Her")
        story = story.replace("{pronoun2}", "her")
        story = story.replace(".{pronoun3}", ". Her")
        story = story.replace(". {pronoun3}", ". Her")
        story = story.replace("{pronoun3}", "her")
    elif pronoun.lower() == "they":
        story = story.replace(".{pronoun1}", ". They")
        story = story.replace(". {pronoun1}", ". They")
        story = story.replace("{pronoun1}", "they")
        story = story.replace(".{pronoun2}", ". Them")
        story = story.replace(". {pronoun2}", ". Them")
        story = story.replace("{pronoun2}", "them")
        story = story.replace(".{pronoun3}", ". Their")
        story = story.replace(". {pronoun3}", ". Their")
        story = story.replace("{pronoun3}", "their")
    return story


def create_white_gradient(img):
    width, height = img.width // 4, img.height

    image = Image.new("RGBA", (width, height), (255, 255, 255, 0))

    for x in range(width):
        alpha = int((x / width) * 255)
        for y in range(height):
            image.putpixel((x, y), (255, 255, 255, alpha))

    white_image = Image.new("RGBA", (5 * img.width // 4, height), (255, 255, 255, 255))
    final_image = Image.new("RGBA", (width + 5 * img.width // 4, height))
    final_image.paste(image, (0, 0))
    final_image.paste(white_image, (width, 0))

    return final_image


def combine_gradient_image(img, gradient):
    mask = gradient.split()[3]
    width, height = img.width, img.height
    fin_image = Image.new("RGBA", (3 * width // 2, height))
    fin_image.paste(img, (0, 0))
    fin_image.paste(gradient, (width - width // 4, 0), mask)
    return fin_image


def add_text_to_image(img, text, font_name, font_size):
    font_name = f"./fonts/{font_name}.otf"
    gradient = create_white_gradient(img)
    combined_image = combine_gradient_image(img, gradient)

    font = ImageFont.truetype(font_name, font_size)

    draw = ImageDraw.Draw(combined_image)

    a = img.width + 40  # start width
    b = combined_image.width - 40  # end width

    wrapper = textwrap.TextWrapper(
        width=40
    )  # change 40 to control the number of words per line
    word_list = text.split(" ")
    wrapped_text = "\n".join(
        [
            " ".join(wrapper.wrap(" ".join(word_list[i : i + 40])))
            for i in range(0, len(word_list), 40)
        ]
    )

    colored_text = []
    for word in wrapped_text.split():
        if random.randint(1, 4) == 1:
            colored_text.append(
                (
                    word,
                    (
                        random.randint(100, 255),
                        random.randint(100, 255),
                        random.randint(100, 255),
                    ),
                )
            )
        else:
            colored_text.append((word, (0, 0, 0)))  # default color, black

    line_spacing = 20

    total_height = 0
    lines = []
    line = []
    line_width = 0
    word_heights = []

    for word, color in colored_text:
        bbox = draw.textbbox((0, 0), word, font)
        word_width = bbox[2] - bbox[0]
        word_height = bbox[3] - bbox[1]

        if line_width + word_width > b - a:
            lines.append(line)
            total_height += word_height + line_spacing
            word_heights.append(word_height)
            line = []
            line_width = 0

        line.append((word, color))
        line_width += word_width + draw.textbbox((0, 0), " ", font)[2]

    if line:
        lines.append(line)
        total_height += word_height
        word_heights.append(word_height)

    image_height = combined_image.size[1]
    start_y = max((image_height - total_height) // 2, 0)

    x = a
    y = start_y

    for i, line in enumerate(lines):
        x = a
        for word, color in line:
            bbox = draw.textbbox((x, y), word, font)
            word_width = bbox[2] - bbox[0]

            draw.text((x, y), word, font=font, fill=color)

            x += word_width + draw.textbbox((0, 0), " ", font)[2]

        y += word_heights[i] + line_spacing

    return combined_image
