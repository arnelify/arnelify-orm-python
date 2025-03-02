FROM gcc:14.2.0

WORKDIR /var/www/python

RUN apt-get update -y && apt-get upgrade -y
RUN apt-get install sudo nano ccache patchelf -y
RUN apt-get install libjsoncpp-dev -y

RUN apt-get install python3.11-dev python3.11-venv -y
RUN sudo ln -sf $(which python3) /usr/bin/python

EXPOSE 3001