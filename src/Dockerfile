# pull official base image
FROM hykilpikonna/vt-cuda:1.0.0

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

#ENV LD_LIBRARY_PATH=/usr/local/cuda/lib64:/usr/local/cuda/compat:/usr/local/nvidia/lib64:/usr/local/nvidia/lib
ENV LD_LIBRARY_PATH=/usr/local/cuda/lib64:/usr/local/nvidia/lib64:/usr/local/nvidia/lib
ENV LIBRARY_PATH=${LIBRARY_PATH}:/usr/local/cuda/lib64

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
