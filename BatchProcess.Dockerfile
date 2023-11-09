# To enable ssh & remote debugging on app service change the base image to the one below
# FROM mcr.microsoft.com/azure-functions/python:4-python3.9-appservice
FROM mcr.microsoft.com/azure-functions/python:4-python3.9

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

COPY ./code/requirements.txt /
RUN apt-get update \
    && apt-get -y install pytesseract \
RUN apt-get update \
    && apt-get -y install tesseract-ocr \ # required for pytesseract
    
RUN pip install -r /requirements.txt

COPY ./code /home/site/wwwroot