FROM python:2-slim

# INSTALL TOOLS
RUN apt-get update \
    # gcc required for cx_Oracle
    && apt-get -y install gcc \
    && apt-get -y install unzip \
    && apt-get -y install libaio-dev

ADD ./oracle-instantclient/ /opt/data
ADD ./install-instantclient.sh /opt/data
ADD ./requirements.txt /opt/data

WORKDIR /opt/data

ENV ORACLE_HOME=/opt/oracle/instantclient
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$ORACLE_HOME

ENV OCI_HOME=/opt/oracle/instantclient
ENV OCI_LIB_DIR=/opt/oracle/instantclient
ENV OCI_INCLUDE_DIR=/opt/oracle/instantclient/sdk/include

RUN chmod +x ./install-instantclient.sh

# INSTALL INSTANTCLIENT AND DEPENDENCIES
RUN ./install-instantclient.sh \
    && pip install -r requirements.txt

WORKDIR /usr/src/app

COPY ./app .

EXPOSE 5000

CMD [ "python", "./app.py" ]
