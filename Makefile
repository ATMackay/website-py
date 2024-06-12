# Alex Mackay 2024

# Create local environment for testing
env:
	cp .env.tpl .env

# Install dependencies in a virtual environment (Unix/MacOS)
# NOTE this command will activate the Python virtual environment.
# To deactivate exectute 'deactivate'
install-dependencies:
	python3 -m venv .venv
	python3 -m pip install --upgrade pip
	$(shell source .venv/bin/activate && pip install -r requirements.txt) 

# Create SQL light database for testing
db-light:
	cp instance/posts.db.tpl instance/posts.db

docker-run-db:
	@docker compose -f docker-compose.yml up -d database

# Run the application on localhost (http://127.0.0.1:5001)
run:
	$(shell source .venv/bin/activate && python3 main.py)
	
.PHONY: env db-light docker-run-db install-dependencies run