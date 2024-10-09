FROM continuumio/miniconda3


RUN mkdir /tmp/communitydetection_serviceapp
COPY dist/*.whl /tmp/communitydetection_serviceapp/

RUN pip install /tmp/communitydetection_serviceapp/communitydetection_serviceapp*whl

RUN rm -rf /tmp/communitydetection_serviceapp

ENTRYPOINT ["/opt/conda/bin/communitydetection_serviceappcmd.py"]
CMD ["--help"]
