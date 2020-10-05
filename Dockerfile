FROM continuumio/miniconda3:latest
ADD *.py /
ADD locales/ /locales/
ADD _credentials/ /_credentials/
ADD requirements.txt /
RUN pip install -r requirements.txt
CMD ["python", "./script.py"]
