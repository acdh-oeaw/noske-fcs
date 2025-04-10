
* Clone this repo and go into directory with this file.
* Add corpora definition to the `sources.csv' file.
  The fist column contains the corpora name, the second the docker image and the third the bash expression matching vertical files inside the image.
  Then commit and push.
* Extract original verticals by running the `extract_vertical.sh` script:
  ```bash
  echo sources.csv | extract_vertical.sh
  # or to process only a single one
  grep corporaName sources.csv | extract_vertical.sh
  ```
* Reprocess the vertical by running the `reprocess_vertical.py` script:
  * Install Python dependencies
    ```bash
    python3 -m venv env
    source env/bin/activate
    pip3 install -U -r requirements.txt
    ```
    * If you want to use the [spacy](https://spacy.io/) (and not the [udppipe](https://lindat.mff.cuni.cz/services/udpipe/)),
      you need to install it along with language models of your choice.
      Please take a look at the https://spacy.io/usage#quickstart for details
      but it will go down to something like (in already activated python virtual environment):
      ```bash
      pip3 install -U spacy
      python -m spacy download LangModuleOfYourChoice
      ```
  * Create the config file from a template:
    ```bash
    cp config_sample.yaml config.yaml
    ````
    and adjust the `config.yaml` contents
  * Run with
    ```bash
    python3 reprocess_vertical.py
    ```
    * To see all command-line options run
      ```bash
      python3 reprocess_vertical.py --help
      ```
* Then run
  ```bash
  ./extract_existing.sh
  ./compile_corp.sh
  ./build_image.sh
  docker push acdhch/noske-fcs-dse-static
  ```
* Update the [corpora.yaml](https://github.com/acdh-oeaw/noske-fcs/blob/main/corpora.yaml) with the data of the generated corpora
  (you can find them in the `data/*.yml` files), commit and push.
* Run the [build action](https://github.com/acdh-oeaw/noske-fcs/actions/workflows/build.yml) or make a new release.

