FROM python:3.10-slim-bullseye

WORKDIR /usr/src/app

COPY ./requirements.txt .

ENV PYTHONPATH .
RUN apt-get update
RUN apt-get install -y libz-dev gcc g++
RUN apt-get install -y --no-install-recommends git

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --upgrade git+https://github.com/terrierteam/pyterrier_doc2query.git
RUN pip install --upgrade git+https://github.com/terrierteam/pyterrier_dr.git
COPY ./src/* .

CMD [ "python", "-u", "Crawler.py"]