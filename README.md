# Pre-Requisites

    1. Python install properly
    2. Environment vairable created to access in Terminal, CMD etc.

# Steps to Execute Source Code

    1. Download the source code
    2. Unzip the source code
    3. Also download the provided "requirements.txt" then open the Terminal / CMD and write the command below:
        "pip install -r requirements.txt"
    4. Go to the folder where "main.py" is present and write the command below
        "python main.py"
    5. Terminal/CMD will show you the "localhost" ip, click on the ip and it will lead to the GUI
    6. Upload the image and select the output format of the output
    7. It will take few seconds and will display the image you inserted, along with the Output for downloading
    8. Click on the button named "Download Result" to get the output

Enjoy using the App!

# Using Docker

    Another way of using this app is using docker, using this method you will not have to resolve any dependency issues
    1. Extract the source code
    2. Place the Dockerfile, Makefile, requirements.txt in the source code folder
    3. Open the terminal and use "Docker build" && "Docker run" commands to run the container of the Application
