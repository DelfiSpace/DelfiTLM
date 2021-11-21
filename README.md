# DelfiTLM

# Setup

1. Create a python environment (one time instruction):
`python3 -m venv env`

2. Activate it using:
`source env/bin/activate`

3. Install the requirements (one time instruction):
`pip install -r requirements.txt`

4. If you run the server locally, set up the database for local development
`docker-compose up db`

5. Run the server from the root folder:
`python src/manage.py runserver` The server runs on http://127.0.0.1:8000/

6. Run the tests:
`python src/manage.py test`

7. Run pylint:
`find src -name "*.py" | xargs pylint`

8. Build and run Docker deployment script (runs on port 80 - default web port):
`docker-compose -f docker-compose-deploy.yml up --build`

9. Simulate a deployment locally with Django debug mode enabled (runs on port 8000):
`docker-compose up --build`

Note: remove `--build` to skip building the container, will use the cached one (last build)