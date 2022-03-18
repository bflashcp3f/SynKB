# SynKB: Semantic Search for Chemical Synthesis Procedures

This repo provides the code and data to replicate our demo system SynKB.

## System Overview
SYNKB is an open-source web-based search engine that allows users, like chemists, to perform structured queries over 
a large corpus of synthesis procedures extracted from chemical patents.

Demo URL: [https://tinyurl.com/synkb](https://tinyurl.com/synkb)\
Introduction video: [https://screencast-o-matic.com/watch/c3n6DTVDSTY](https://screencast-o-matic.com/watch/c3n6DTVDSTY)

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

3. Download indexed data ([index.tar.gz](https://drive.google.com/file/d/1ZOqvuPqftbaIAI_omQb8R53Mrr21YEWk/view?usp=sharing)) and extract files
```
tar -xvzf index.tar.gz
```

4. Launch Odinson (Java 11 is required)
```
cd ../../../
sbt backend/run
```

### Set up Elasticsearch

1. Download Elasticsearch folder ([elastic_data.tar.gz](https://drive.google.com/file/d/1eie6pEMN31n3D7R3mOOrz420s-2YVfSW/view?usp=sharing)), and extract files.
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

