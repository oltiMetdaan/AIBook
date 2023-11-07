import os
import cv2
def construct_command(face_file, input_file, output_file):
    base_command = "python3 classes/run.py"
    source_option = f"--source {face_file}"
    target_option = f"--target {input_file}"
    output_option = f"--output {output_file}"  # Customize your output path
    other_options = "--keep-fps --keep-frames --temp-frame-quality 100"  # Add any other desired options here
    
    full_command = f"{base_command} {source_option} {target_option} {output_option} {other_options}"
    
    return full_command

def main(face, inputs, output):
    face_directory = os.path.join(os.getcwd(),face)
    input_directory = os.path.join(os.getcwd(),inputs)
    output_file = os.path.join(os.getcwd(),output)
    
    # Assuming only one file in the face folder, otherwise adjust the logic
    face_file = os.path.join(face_directory, [f for f in os.listdir(face_directory) if '.ipynb_checkpoints' not in f][0])

    input_files = [os.path.join(input_directory, f) for f in os.listdir(input_directory) if os.path.isfile(os.path.join(input_directory, f))]
    input_files = [f for f in input_files if '.ipynb_checkpoints' not in f]
    for input_file in input_files:
        command = construct_command(face_file, input_file, output_file)
        print(f"Executing: {command}")
        os.system(command)

if __name__ == "__main__":
    main()
