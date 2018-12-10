
FROM python:3.6-stretch

RUN adduser -disabled-password orthozor

WORKDIR /home/orthozor

# Installation de R par ajout du dépôt pertinent
RUN apt-get update -y && apt-get install -y dirmngr --install-recommends software-properties-common apt-transport-https
#RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-key 'E19F5F87128899B192B1A2C2AD5F960A256A04AF'
#RUN add-apt-repository 'deb https://cloud.r-project.org/bin/linux/debian stretch-cran35/'

RUN apt-get update -y && apt-get upgrade -y && apt-get install -y r-base postgresql
RUN apt-get -f install


COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt


#Installation des packages R
RUN Rscript -e "install.packages('mirtCAT', dependencies=TRUE, repos='http://cran.rstudio.com/')"

COPY app app
COPY migrations migrations
COPY config.py wsgi.py boot.sh ./
RUN chmod +x boot.sh

ENV FLASK_APP wsgi.py
ENV FLASK_CONFIG production


RUN chown -R orthozor:orthozor ./
USER orthozor


EXPOSE 5000
ENTRYPOINT ["./boot.sh"]