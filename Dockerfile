FROM continuumio/miniconda3:latest
ADD *.py /
ADD locals/ /
RUN pip install ethercalc-python
RUN pip install Babel
CMD ["python", "./script.py"]
