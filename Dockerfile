FROM python:3
#ADD app.py /

COPY ./requirements.txt /requirements.txt
WORKDIR /
RUN pip3 install -r requirements.txt
COPY . /
ENTRYPOINT [ "python3" ]


CMD [ "app/app.py" ]



