# SynKB: Semantic Search for Chemical Synthesis Procedures

This repo provides the code and data to replicate our system ["SynKB: Semantic Search for Synthetic Procedures"](https://arxiv.org/abs/2208.07400), which is accepted to EMNLP 2022 Demo track.
```
@article{bai-etal-2022-synkb,
  title={SynKB: Semantic Search for Synthetic Procedures},
  author={Bai, Fan and Ritter, Alan and Madrid, Peter and Freitag, Dayne and Niekrasz, John},
  journal={arXiv preprint arXiv:2208.07400},
  year={2022}
}
```

## System Overview
SYNKB is an open-source web-based search engine that allows users, like chemists, to perform structured queries over 
a large corpus of synthesis procedures extracted from chemical patents.

Demo URL: [https://tinyurl.com/synkb](https://tinyurl.com/synkb)\
Introduction video: [https://screencast-o-matic.com/watch/c3jVQsVZwOV](https://screencast-o-matic.com/watch/c3jVQsVZwOV)

## Installation
<!-- To enable all search features, we need to set up Odinson and Elasticsearch in the backend. -->

### Create conda environment
```
git clone https://github.com/bflashcp3f/SynKB.git
cd SynKB
conda env create -f environment.yml
conda activate synkb
```

### Set up Odinson search

1. Clone the Odinson repo

```
git clone https://github.com/bflashcp3f/odinson.git
cd odinson
git checkout synkb
```

2. Set up indexed data path
```
mkdir -p extra/data/pets/
cd extra/data/pets/
```

3. Download indexed data ([index.tar.gz](https://www.dropbox.com/s/3u6x1ixxb5oyrxq/index.tar.gz?dl=0)) and extract files
```
tar -xvzf index.tar.gz
```

4. Launch Odinson (Java 11 is required)
```
cd ../../../
sbt backend/run
```

### Set up Elasticsearch

1. Download Elasticsearch folder ([elastic_data.tar.gz](https://www.dropbox.com/s/1hxi7iobjk2rz9v/elastic_data.tar.gz?dl=0)), and extract files.
```
tar -xvzf elastic_data.tar.gz
```

2. Launch Elasticsearch
```
cd elasticsearch-6.8.19
./bin/elasticsearch
```

## Usage

### Launch the demo

```py
cd SynKB
python manage.py runserver YOUR_PORT_NUMBER
```

## Customization
If you want to customize SynKB for your own data, check out this [tutorial](./custom/README.md).
