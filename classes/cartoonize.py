import cv2
import numpy as np
import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()
from classes import network, guided_filter
from PIL import Image



def resize_crop(image):
    h, w, c = np.shape(image)
    if min(h, w) > 720:
        if h > w:
            h, w = int(720*h/w), 720
        else:
            h, w = 720, int(720*w/h)
    image = cv2.resize(image, (w, h),
                       interpolation=cv2.INTER_AREA)
    h, w = (h//8)*8, (w//8)*8
    image = image[:h, :w, :]
    return image
    

def cartoonize(input_image, model_path = 'classes/saved_models'):
    input_photo = tf.placeholder(tf.float32, [1, None, None, 3])
    network_out = network.unet_generator(input_photo)
    final_out = guided_filter.guided_filter(input_photo, network_out, r=1, eps=5e-3)

    all_vars = tf.trainable_variables()
    gene_vars = [var for var in all_vars if 'generator' in var.name]
    saver = tf.train.Saver(var_list=gene_vars)
    
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    sess = tf.Session(config=config)

    sess.run(tf.global_variables_initializer())
    saver.restore(sess, tf.train.latest_checkpoint(model_path))
    try:
        image = cv2.cvtColor(np.array(input_image.convert("RGB")), cv2.COLOR_RGB2BGR)
        image = resize_crop(image)
        
        batch_image = image.astype(np.float32)/127.5 - 1
        batch_image = np.expand_dims(batch_image, axis=0)
        output = sess.run(final_out, feed_dict={input_photo: batch_image})
        output = (np.squeeze(output)+1)*127.5
        output = np.clip(output, 0, 255).astype(np.uint8)
        output = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)


        # Open the images
        img1 = input_image
        img2 = Image.fromarray(output)

        # Get the smaller dimensions of the two images
        new_width = min(img1.width, img2.width)
        new_height = min(img1.height, img2.height)

        # Resize the images
        img1_resized = img1.resize((new_width, new_height))
        img2_resized = img2.resize((new_width, new_height))

        # Perform blending (assuming equal weightage to both images, adjust the alpha accordingly)
        alpha = 0.5  # Change alpha to adjust the weightage of the images in the blend
        combined = Image.blend(img1_resized, img2_resized, alpha)

        return combined
    except:
        print('cartoonize {} failed'.format("Image"))

    

    
