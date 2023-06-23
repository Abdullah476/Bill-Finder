FROM python:3.9.16 

# Set the working directory of the project
WORKDIR /

# Copy the requirements
COPY requirements.txt ./requirements.txt

# Copy the Makefile for installation
COPY Makefile ./Makefile

# Copy all files
COPY ner_model/ /ner_model/
COPY static/ /static/
COPY templates/ /templates/

# Finally, copy the Flask server execution file
COPY main.py ./main.py

# Install the dependencies
RUN make install

# Setting the environment variable for flask app
ENV FLASK_APP=main.py

# Command for running flask app
CMD ["python", "-m", "flask", "run", "--host", "0.0.0.0"]