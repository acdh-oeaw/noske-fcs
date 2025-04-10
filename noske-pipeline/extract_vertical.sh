#!/bin/bash
#
# Extracts verticals from source definitions read from the standard input.
#
# The input should be in a CSV format (semicolon-separated) with each row describing a single source:
# - 1st col: the name of the corpora config file in the /var/lib/manatee/registry directory
# - 2nd col: docker image
# - 3rd col: path of vertical file(s) within the image
# - 4th col: lowercase ISO-639-3 language code of the corpora
#
# e.g. "shawi;ghcr.io/acdh-oeaw/shawi-data/shawi-noske:597a978;var/lib/manatee/data/verticals/*txt"
#
# Vertical(s) are concatenated together into a vertical file named after the corpora name.
#
DIR=`dirname "${BASH_SOURCE[0]}"`
if [ ! -d verticals ] ; then
    mkdir verticals
fi
while IFS=';' read CORP IMG VRTPATH LANGUAGE ; do
    if [ "CORP" == "" ] ; then
        continue
    fi
    VRTPATH2=`echo "$VRTPATH" | sed -e 's/\*/.*/'`

    echo "$LANGUAGE" > "verticals/$CORP.vrt"

    # downlaod the image and extract to a tar file
    docker pull $IMG
    docker save $IMG > tmp.tar
    # search layers for the vertical(s)
    for LAYER in `docker image inspect $IMG | grep '    "sha256' | sed -e 's/ *"sha256://' -e 's/".*//'` ; do
        tar -xf tmp.tar --transform 's/.*\///' blobs/sha256/$LAYER

        VERTICALS=`tar -tf $LAYER | grep "$VRTPATH2"`
        if [ "$?" == "0" ] ; then
            # vertical(s) found - extract, join and append to the vertical file
            mkdir tmp
            tar -xf $LAYER -C tmp --wildcards "$VRTPATH"
            cd tmp
            echo "$VERTICALS" | xargs -d '\n' cat >> "../verticals/$CORP.vrt"
            cd ..
            rm -fR tmp
        fi

        # extract the configuration file
        CFGPATH="var/lib/manatee/registry/$CORP"
        tar -tf $LAYER | grep "$CFGPATH" > /dev/null
        if [ "$?" == "0" ] ; then
            tar -xf $LAYER -C verticals --transform 's/var\/lib\/manatee\/registry\///' "$CFGPATH"
        fi

        rm $LAYER
    done
    rm tmp.tar
done
