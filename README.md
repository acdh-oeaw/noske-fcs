# noske-fcs

This repository provides a deployment of the [mquery-sru](https://github.com/czcorpus/mquery-sru) for ACDH-CH public corpora.

It uses github actions to run a following workflow:

* Clone the [mquery-sru](https://github.com/czcorpus/mquery-sru) repo.
* Adjust its Dockerfile so it includes corpora from existing docker images defined in the `preDockerfile`
  and copies data from them according to the `postDockerfile`.
* Include into the build config the `confgen.py` script and the `corpora.yml` file which are used to dynamically
  build the `corpora-resources` section of the 
  [mquery-sru's config file](https://github.com/czcorpus/mquery-sru/blob/main/config-reference.md)
  upon its container startup.
* Build the docker image and push it to the docker hub.

The deployment is available under https://noske-fcs.acdh-ch-dev.oeaw.ac.at/, e.g. 

* https://noske-fcs.acdh-ch-dev.oeaw.ac.at/?operation=explain&version=2.0&x-fcs-endpoint-description=true
* https://noske-fcs.acdh-ch-dev.oeaw.ac.at/?query=Vater

## Endpoint configuration

* Open the `config.json` and adjust the `serverInfo` section.
* Save, commit, push, run the build action.

## Adding additional corpora

* If the corpus is a part of a publicly available docker image, then define an alias to it
  in the `preDockerfile` and add a data copy command to the `postDockerfile` (see the sample code in these files)
* Edit the `corpora.yaml` providing all configuration properties for the new corpus
  (see comments inside the file)
* Commit, push, run the build action.

## Links

* [mquery-sru](https://github.com/czcorpus/mquery-sru)
* [CLARIN FCS 2.0 spec](https://clarin-eric.github.io/fcs-misc/fcs-core-2.0-specs/fcs-core-2.0.html)
* [CLARIN FCS validator](https://fcs-validator.data.saw-leipzig.de/)
* [Sketch Engine corpora config file reference](https://www.sketchengine.eu/documentation/corpus-configuration-file-all-features/)
* [Hannes's gitlab.oeaw.ac.at repositories](https://gitlab.oeaw.ac.at/acdh-ch/hpirker/)
* [noske-fcs namespace in Rancher](https://rancher.acdh-dev.oeaw.ac.at/dashboard/c/c-m-6hwgqq2g/explorer/namespace/noske-fcs#Workloads)
