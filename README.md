# Blog website written in Python & JavaScript

Credit to [@angelabauer](https://github.com/angelabauer) for the website template and excellent [Python bootcamp](https://www.udemy.com/course/100-days-of-code/).

## Getting Started

Install application dependencies within a virtual environment
```
make install
```

Prepare the environment file
```
make env
```

If you want to add support for email notification via smtp lib then enter your email and password as well as flask application key to the `.env` file.

To start the web application in a local development environment execute
```
make run
```