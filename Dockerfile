FROM continuumio/miniconda3:latest
ADD *.py /
ADD locals/ /
RUN pip install ethercalc-python
CMD ["python", "./script.py"]
