# Version 1.0 template-transformer-simple 

FROM agpipeline/gantry-base-image:latest
LABEL maintainer="Chris Schnaufer <schnaufer@email.arizona.edu>"

COPY requirements.txt packages.txt /home/extractor/

USER root

RUN [ -s /home/extractor/packages.txt ] && \
    (echo 'Installing packages' && \
        apt-get update && \
        cat /home/extractor/packages.txt | xargs apt-get install -y --no-install-recommends && \
        rm /home/extractor/packages.txt && \
        apt-get autoremove -y && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/*) || \
    (echo 'No packages to install' && \
        rm /home/extractor/packages.txt)

RUN wget https://raw.githubusercontent.com/GitHubRGI/geopackage-python/master/Tiling/gdal2tiles_parallel.py \
 && mv gdal2tiles_parallel.py /home/extractor/gdal2tiles_parallel.py

RUN python3 -m pip install --no-cache-dir -r /home/extractor/requirements.txt && \
    rm /home/extractor/requirements.txt

USER extractor

COPY *.py /home/extractor/
