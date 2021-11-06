# DelfiTLM

# Setup

1. Create a python environment (one time instruction):
`python3 -m venv env`

2. Activate it using:
`source env/bin/activate`

3. Install the requirements (one time instruction):
`pip install -r requirements.txt`

4. Run the server from the root folder:
`python src/manage.py runserver` The server runs on http://127.0.0.1:8000/

5. Run the tests:
`python src/manage.py test`

6. Run pylint:
`find src -name "*.py" | xargs pylint`

7. Build and run Docker deployment script:
`docker-compose -f docker-compose-deploy.yml up --build`