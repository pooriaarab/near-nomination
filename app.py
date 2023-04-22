from flask import Flask, render_template, request, send_file, url_for, redirect
from PIL import Image, ImageDraw, ImageFont
import tempfile
import os
from datetime import datetime, timedelta
from urllib.parse import urlencode, quote
import textwrap
import time
import string
import random
import requests 


app = Flask(__name__, static_url_path='/static')

# create a temporary directory to store the generated images
temp_dir = tempfile.mkdtemp()
app.config['TEMP_DIR'] = temp_dir

# Store the twitter username and nomination reason in global variables
twitter_username = None
nomination_reason = None


@app.route('/')
def home():
    return render_template('index.html')



@app.route('/', methods=['POST'])
def generate_image():
    global twitter_username, nomination_reason
    twitter_username = request.form['twitter_username']
    nomination_reason = request.form['nomination_reason']

    # Open the base image and create a new ImageDraw object
    base_image = Image.open('base_image.png')
    draw = ImageDraw.Draw(base_image)

    # Add the textboxes to the image
    font_size_username = 54
    font_size_nomination_reason = 34
    font_username = ImageFont.truetype('arial.ttf', font_size_username)
    font_nomination_reason = ImageFont.truetype('arial.ttf', font_size_nomination_reason)

    # Position the username text slightly higher
    x_username = base_image.width / 2
    y_username = 100
    draw.text((x_username, y_username), f'@{twitter_username}', font=font_username, fill=(0, 0, 0), anchor="mm", stroke_width=5, stroke_fill=(255, 255, 255))

    # Add the "for top 99 because" text in a new line below the username
    draw.text((x_username, y_username + font_size_username), "for top 99", font=font_nomination_reason, fill=(0, 0, 0), anchor="mm", stroke_width=5, stroke_fill=(255, 255, 255))

    # Set the maximum width for the text box
    max_width = 400

    # Wrap the text and add the nomination reason textbox to the image
    nomination_reason_lines = textwrap.wrap(nomination_reason, width=30)
    nomination_reason_text = '\n'.join(nomination_reason_lines)
    nomination_reason_text = nomination_reason_text[:150] + '...' if len(nomination_reason_text) > 150 else nomination_reason_text

    # Get the size of the wrapped text
    nomination_reason_size = draw.multiline_textsize(nomination_reason_text, font=font_nomination_reason, spacing=10)

    # Calculate the width of the wrapped text
    wrapped_text_width = max([draw.textsize(line, font=font_nomination_reason)[0] for line in nomination_reason_lines])

    # Position the nomination reason text in the center of the image
    x_nomination_reason = base_image.width / 2 - wrapped_text_width / 2
    y_nomination_reason = y_username + font_size_username + font_size_nomination_reason + 20

    # Add an offset to increase the line height
    y_nomination_reason += 20

    # Draw the nomination reason text on the image
    draw.multiline_text((x_nomination_reason, y_nomination_reason), nomination_reason_text, font=font_nomination_reason, fill=(0, 0, 0), align='center', spacing=10, stroke_width=5, stroke_fill=(255, 255, 255))


    temp_dir = app.config['TEMP_DIR']

    random_string = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890', k=10))

    # Save the generated image to a temporary file
    image_filename = f'{twitter_username}_{random_string}.png'
    image_path = os.path.join(app.config['TEMP_DIR'], image_filename)
    base_image.save(image_path, format='PNG')

    # Pause the execution of the code for 5 seconds
    #time.sleep(3)

    # Return the path to the generated image
    return render_template('image.html', image_path=url_for('generated', filename=image_filename), image_filename=image_filename)





@app.route('/generated/<filename>')
def generated(filename):
    temp_dir = app.config['TEMP_DIR']
    filepath = os.path.join(temp_dir, filename)
    if os.path.exists(filepath):
        # Set the Cache-Control header to cache the image for 1 hour
        expires = datetime.now() + timedelta(hours=1)
        response = send_file(filepath, mimetype='image/png')
        response.headers['Cache-Control'] = f'public, max-age={int(timedelta(hours=1).total_seconds())}'
        response.headers['Expires'] = expires.strftime('%a, %d %b %Y %H:%M:%S GMT')
        return response
    else:
        return f"File {filename} not found", 404


@app.route('/tweet')
def tweet():
    global twitter_username, nomination_reason
    encoded_username = quote(twitter_username)
    encoded_reason = quote(nomination_reason)
    tweet_text = f"I just nominated @{encoded_username} for top 99 in Web3 because {encoded_reason} \n\n cc @beeloudxyz"
    tweet_intent_url = f"https://twitter.com/intent/tweet?text={tweet_text}"
    return redirect(tweet_intent_url)

@app.route('/post-to-near', methods=['POST'])
def post_to_near():
    tweet_text = "example tweet text"  # Replace with the actual tweet text
    
    # Get the image path from the form data
    image_path = request.form.get('image_path')

    # Define the JavaScript code to execute
    js_code = f"""
        const tweetText = "{tweet_text}";
        const imagePath = "{image_path}";

        // Your composeData function here
        const composeData = () => {{
            const data = {{
                post: {{
                    main: JSON.stringify({{ text: tweetText }}),
                }},
                index: {{
                    post: JSON.stringify({{ key: "main", value: {{ type: "md" }} }}),
                }},
            }};

            if (imagePath) {{
                data.post.image = JSON.stringify({{ path: imagePath }});
            }}

            return data;
        }};

        // Execute the composeData function and post to Near
        const postData = composeData();
        window.nearAPI.connection.signAndSendTransaction(
            'mob.near',
            [
                window.nearAPI.transactions.functionCall(
                    'mob.near',
                    'createPost',
                    postData,
                    300000000000000,
                    '0'
                ),
            ],
            window.nearAPI.keyStores.InMemoryKeyStore.deserialize(
                window.localStorage.getItem('near-api-js:keystore')
            )
        );
    """

    # Render the page with the JavaScript code
    return render_template('image.html', js_code=js_code)

if __name__ == '__main__':
    app.run(debug=True)
