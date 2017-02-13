
#Bake in Geomatica package 
FROM precisionhawk/gbdx-derive-dsm-test
MAINTAINER "Charles Rudder" <c.rudder@precisionhawk.com>

# Install PIL requirements and binaries
RUN easy_install http://dist.plone.org/thirdparty/PIL-1.1.7.tar.gz

# Install needed libraries via PIP
RUN \
  curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py" && \
  python get-pip.py && \
  export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH && \
  pip install simplejson && \
  pip install shapely && \
  pip install psutil && \
  pip install pycurl && \
  pip install Pillow && \
  pip install requests && \
  pip install bs4 && \
  pip install fiona && \
  pip install utm

# application directory
COPY app_root/ app
# Loads the GBDX task operation structure to the docker container
COPY mnt/ /mnt
#RUN mkdir /data

# Loads entry point, sets interactive
## Use this as entry point for interactive docker container
#COPY ./docker-entrypoint.sh /
#ENTRYPOINT ["/docker-entrypoint.sh"]
# Runs /bin/bash on container entry
CMD ["/bin/bash"]

# Set docker to be executable
#WORKDIR /app
#CMD ["python", "runner.py"]
#ENTRYPOINT ["python"]
#CMD ["/app/runner.py"]

