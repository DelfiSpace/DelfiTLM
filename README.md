# DelfiTLM

# Setup

1. Create a python environment (one time instruction):
`python3 -m venv env`

2. Activate it using:
`source env/bin/activate`

3. Install the requirements (one time instruction):
`pip install -r requirements.txt`

4. Run the server from the root folder: 
`python manage.py runserver` The server runs on http://127.0.0.1:8000/

5. Run the tests:
`python manage.py test`

6. Run pylint:
`pylint --load-plugins pylint_django --django-settings-module=DelfiTLM.settings app`

