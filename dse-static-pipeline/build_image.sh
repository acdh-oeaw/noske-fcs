#!/bin/bash
docker build -t acdhch/noske-fcs-dse-static --label 'Image containing (No)Sketch Engine indices of dse-static digital editions to be used by the https://github.com/acdh-oeaw/noske-fcs' `dirname "${BASH_SOURCE[0]}"`
cat data/*yml
