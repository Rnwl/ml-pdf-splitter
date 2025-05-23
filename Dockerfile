# FROM python:3.9.16

FROM rnwlcontainerregistryexplore.azurecr.io/python:3.9.16

WORKDIR /usr/src/app

COPY requirements.txt requirements.txt

# Install python packages
RUN python3 -m pip install --no-cache-dir -r requirements.txt

#Copy current directory to workdir . in the image
COPY . .
RUN ["mkdir", "-p", "logs"]

EXPOSE 5006

CMD ["uvicorn", "src.api:pdf_splitter_app", "--host", "0.0.0.0", "--port", "5006"]
