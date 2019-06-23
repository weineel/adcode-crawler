FROM python:3

WORKDIR /usr/app

COPY . /usr/app

RUN pip install pipenv && pipenv install

CMD ['python', './src/first.py', '-h']
