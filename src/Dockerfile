# pull official base image
FROM hykilpikonna/vt-cuda:1.0.0

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

## install libraries
#RUN apt update
#RUN apt install libsndfile1-dev ffmpeg -y
#
## install dependencies
#RUN pip install --upgrade pip
#COPY ./requirements.txt .
#RUN pip install -r requirements.txt

# copy project
COPY . .
