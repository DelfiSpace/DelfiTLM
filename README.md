# DelfiTLM

# Requirements

- A modern python version
- For local running/development: The postgres client library (For apt users: `apt install libpq-dev`)
- Docker and docker-compose if running the system or the database from a container
- For running without docker: Set up a Postgres instance on port 5432

# Setup (Run locally/on host machine)

This method

1. Create a python environment (one time instruction):
`python3 -m venv env`

2. Activate it using:
`source env/bin/activate`

3. Install the requirements (one time instruction):
`pip install -r requirements.txt`

4. Set up the database via docker or connect your own Postgres instance
`docker-compose up db`

5. Run the migrations from the root folder:
`python src/manage.py migrate`

6. Run the server from the root folder:
`python src/manage.py runserver` The server runs on http://127.0.0.1:8000/

7. To run the tests:
`python src/manage.py test`

8. To run pylint:
`find src -name "*.py" | xargs pylint`

# Setup (Run via docker)

This method should be sufficient for most development tasks as any (file) changes you make are monitored by StatReloader. To start the environment, run:
`docker-compose up --build`

Note: remove `--build` to skip building the container, will use the cached one (last build)

After this, you can access the application on http://127.0.0.1:8000/ and a pgAdmin instance on http://127.0.0.1:5050/ with `admin@admin.com:admin` for username:password. From pgAdmin add a new server by giving it a name and the following database credentials:

![image](https://user-images.githubusercontent.com/15870306/145728488-ada8aacf-ec53-42d1-8e4d-b7198c70cc77.png)

To reset the container and remove the volumes run the `./reset_docker.sh` script

# Deployment

1. Build and run Docker deployment script (runs on port 80 - default web port):
`docker-compose -f docker-compose.yml -f docker-compose-deploy.yml up --build`

2. Access the container to initialise Django (only required the first time):
`docker exec -it delfitlm_app_1 /bin/bash`

3. Run the database migration to create the tables (only required the first time):
`python manage.py migrate`

Note: remove `--build` to skip building the container, will use the cached one (last build)

