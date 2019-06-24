FROM kennethreitz/pipenv

ENTRYPOINT ["python3", "src/main.py"]

CMD -r -i 2
