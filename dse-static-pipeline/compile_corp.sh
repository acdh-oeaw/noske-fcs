#!/bin/bash
mkdir compiled
docker run --rm \
    -v `pwd`/data:/var/lib/manatee/registry \
    -v `pwd`/compiled:/var/lib/manatee/data \
    --entrypoint bash \
    czcorpus/kontext-manatee:2.225.8-noble \
    -c 'for i in `ls /var/lib/manatee/registry/ | grep -v "[.]"`; do compilecorp /var/lib/manatee/registry/$i ; done'
