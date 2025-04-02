# dse-static pipiline

Script harvesting Peter Andorfer's [dse-static](https://github.com/acdh-oeaw?q=dse-static&type=all&language=&sort=) TEI-XML digital editions,
tokenizing and enriching them with lemma and part of speach
and writing a (No)Sketch Engine-compatible [vertical file](https://www.sketchengine.eu/glossary/vertical-file/) and a corresponding [corpus config file](https://www.sketchengine.eu/documentation/the-corpus-configuration-file/).

## Usage

* Clone this repo and go into directory with this file
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
  python3 create_verticals.py
  ```
  * To see all command-line options run
    ```bash
    python3 create_verticals.py --help
    ```
