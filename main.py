# importing the necessary libraries
from flask import Flask, request, flash, redirect, url_for, render_template, send_from_directory
from spacy import load
import io
import json
import os
import cv2
import requests
import csv


# variable for storing the NER model
model = None

# create a new Flask application instance
app = Flask(__name__)

# set the secret key for the application
app.secret_key = "secret key"

# set the location where uploaded files will be saved
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['OUTPUT_FOLDER'] = 'static/outputs/'

# set the maximum file size for uploaded files to 16 MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# define the set of allowed file extensions
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

# file format of the output
file_format = ""
file_name = ""

def allowed_file(filename):
    """
    Function to check if the file extension of an uploaded file is allowed.
    """
    # check if the filename has a valid extension and the extension is in the set of allowed extensions
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# define the route for the homepage
@app.route('/')
def home():
    # render the index.html template
    return render_template('index.html')
 
# define the route for uploading an image file
@app.route('/', methods=['POST'])
def upload_image():
    
    # using the global variable
    global file_format
    global file_name

    # check if a file was uploaded
    if 'file' not in request.files:
        flash('No file part')
        # redirect back to the homepage
        return redirect(request.url)
    
    # get the uploaded file
    file = request.files['file']
    
    # check if an image was selected for uploading
    if file.filename == '':
        flash('No image selected for uploading')
        # redirect back to the homepage
        return redirect(request.url)
    
    # check if the uploaded file is a valid image type
    if file and allowed_file(file.filename):
        # save the uploaded file to the UPLOAD_FOLDER directory
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # get the selected file format from the form and save the filename as well
        file_format = request.form['format']
        file_name = filename

        # read the image from the folder
        image, grayscale = read_image("static/uploads/"+str(filename))

        # apply preprocessing on the image
        enhanced = pre_processing(grayscale)

        # passing the image to the OCR
        resultant_text = ocr_space_file(enhanced)

        # get the entities from the data
        entities = ner_interpretation(resultant_text)

        # save the output to the file
        output_file(entities)

        # generate the download link for the generated file
        download_link = url_for('download_output', filename=file_name + "." + file_format, _external=True)

        # display a success message and render the index.html template with the uploaded file name
        flash('Image successfully uploaded and displayed below')
        return render_template('index.html', filename=filename, download_link=download_link)
    else:
        # display an error message and redirect back to the homepage
        flash('Allowed image types are - png, jpg, jpeg')
        return redirect(request.url)
 

# define the route for displaying an uploaded image
@app.route('/display/<filename>')
def display_image(filename):
    # redirect to the uploaded image file in the UPLOAD_FOLDER directory
    return redirect(url_for('static', filename='uploads/' + filename), code=301)

# define the route for downloading the output file
@app.route('/download/<filename>')
def download_output(filename):
    # construct the path to the output file
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    # check if the output file exists
    if os.path.exists(output_path):
        # send the file for download
        return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)
    else:
        # display an error message if the output file does not exist
        flash('Requested file does not exist')
        return redirect(url_for('home'))

def pre_processing(image):
    """
        Function to apply some pre-processing techniques on the image
    """

    blur = cv2.GaussianBlur(image, (3,3), 0)
    resultant = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    return resultant


def read_image(image_path):
    """
        Function to read the image from the path
    """

    # read the image from the path provided
    try:
        image = cv2.imread(image_path)
    except:
        print("Unable to read the image from the path")

    # convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # return the colour and grayscale images
    return image, gray


def ocr_space_file(img, filename="dummy.jpg"):
    """
        Function to extract the text using the OCR Space API using image
    """

    # setting the parameters
    url_api = "https://api.ocr.space/parse/image"

    # compressing the image
    _, compressedimage = cv2.imencode(".jpg", img)
    file_bytes = io.BytesIO(compressedimage)

    # calling the api using post
    try:
        result = requests.post(url_api,
                               files={filename: file_bytes},
                               data={"apikey": "K86068826388957",
                                     "language": "eng",
                                     "OCREngine": "5",
                                     "isTable": "False",
                                     "scale": "True",
                                     "detectOrientation": "True"})
    except:
        print("Unable to call the OCR Space API")

    # reading the results
    result = result.content.decode()
    result = json.loads(result)

    # parsing the json results
    text_detected = result.get("ParsedResults")[0]["ParsedText"]

    tags = ['\t', '\n', '\r']
    for tag in tags:
        text_detected = text_detected.replace(tag, ' ')

    # return the text
    return text_detected


def output_file(data):
    """
    Function to save the resultant data in the specified file format.
    """

    global file_format
    global file_name

    output_location = 'static/outputs/'
    
    if file_format == "txt":
        filename1 = file_name + ".txt"
        # Open the text file in write mode
        with open(output_location + filename1, 'w', encoding='utf-8') as file:
            for key, value in data.items():
                file.write(f"{key}: {value}\n")
    
    elif file_format == "csv":
        filename1 = file_name + ".csv"
        # Extract the keys from the dictionary to use as column headers
        fieldnames = list(data.keys())

        # Open the CSV file in write mode
        with open(output_location + filename1, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=data.keys())

            # Write the column headers
            writer.writeheader()

            # Write the data row
            writer.writerow(data)
    
    elif file_format == "json":
        filename1 = file_name + ".json"
        with open(output_location + filename1, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)


def load_model(modelType="last"):
    """
    Function to load the NER model
    """

    global model
    if model is None:
        model = load(r'.\\ner_model\\model-' + modelType)
    return model


def ner_interpretation(text):
    """
    Function to get the required entities from the text
    """

    global model
    model = load_model()
    print(text)
    interpretation = model(text) # Simply pass the string text into the model to get the result
    entities = interpretation.ents # Extract the entities from it
    if entities is None: # If the NER model failed to pick any annotations from the string, return None
        raise Exception("No command was said.")
    print(dict(zip([entity.label_ for entity in entities], [entity.text for entity in entities])))
    print()
    return dict(zip([entity.label_ for entity in entities], [entity.text for entity in entities]))
    # Else, return the labels and their corresponding text in a dictionary format by:
    # - Using list comprehension to create two lists, one for labels, and one for text
    # - Zipping them together (as, common sense would have it, both lists would be equal in size, so there will be zero issues)
    # - Calling the built-in 'dict' function to convert the zipped file to a dictionary


# function to run the flask server
if __name__ == '__main__':
    load_model()
    app.run(port=9000, debug=True)
