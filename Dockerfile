FROM python:latest
ADD *.py /
ADD locales/ /locales/
ADD requirements.txt /
RUN pip install -r requirements.txt
CMD ["python", "./script.py", "--service"]
