#!/bin/bash
#
# Extracts existing verticals and config files from the acdhch/noske-fcs-dse-static docker image
#

if [ ! -d data ] ; then
    mkdir data
fi
docker pull ghcr.io/acdh-oeaw/noske-fcs-dse-static:latest
cid=$(docker create ghcr.io/acdh-oeaw/noske-fcs-dse-static:latest /bin/true)
docker cp "$cid":/var/lib/manatee/registry/. data/
docker rm "$cid" > /dev/null
