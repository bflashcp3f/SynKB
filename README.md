# SynKB: Semantic Search for Chemical Synthesis Procedures

This repo provides the code and data to replicate our demo system SynKB.

## System Overview
SYNKB is an open-source web-based search engine that allows users, like chemists, to perform structured queries over 
a large corpus of synthesis procedures extracted from chemical patents.

Demo URL: [https://tinyurl.com/synkb](https://tinyurl.com/synkb)\
Introduction video: [https://screencast-o-matic.com/watch/c3n6DTVDSTY](https://screencast-o-matic.com/watch/c3n6DTVDSTY)

## Installation

### Create conda environment
```
git clone https://github.com/bflashcp3f/SynKB.git
cd SynKB
conda env create -f environment.yml
conda activate synkb
```

### Set up Odinson search
```
# Clone the Odinson repo
cd ..
git clone https://github.com/lum-ai/odinson.git
cd odinson
git checkout 9522ab65d3be2974b

# Setup index path
mkdir -p extra/data/pets/
cd extra/data/pets/

# Download index.tar.gz () and extract files
tar –xvzf index.tar.gz

# Launch Odinson
cd ../../../
sbt backend/run
```

### Set up Elasticsearch
Download Elasticsearch folder including data bucks via the [link]().
```
# Launch Elasticsearch
./bin/elasticsearch
```

## Usage

### Launch the demo

```py
cd SynKB
python manage.py runserver YOUR_PORT_NUMBER
```

