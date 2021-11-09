FROM python:3.6

ADD final.py requirements.txt ec2-keypair.pem /

RUN python3 -m pip install --upgrade pip
RUN pip install -r requirements.txt

ENV AWS_ACCESS_KEY_ID=
ENV AWS_SECRET_ACCESS_KEY=
ENV AWS_SESSION_TOKEN=
ENV AWS_REGION=us-east-1
ENV AWS_DEFAULT_REGION=us-east-1
RUN aws ecr get-login --region ${AWS_REGION}

ENV PYTHONUNBUFFERED=1
CMD [ "python", "./final.py" ]
