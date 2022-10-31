
Please follow the tutorial below to create your SynKB-like search engine.

## Slot-based Search

### 1. Prepare your data
Format your entity inference results as [slot_sample.json](./slot_sample.json).


### 2. Set up Elasticsearch
Download Elasticsearch package on your server (we use version 6.8.19). Then start Elasticsearch service by running the following command under elasticsearch directory.
```
cd elasticsearch-6.8.19
./bin/elasticsearch
```
The default address for Elasticsearch is `127.0.0.1:9200`. You could check if you have successfully started the service by visiting the above address.

### 3. Load your data into Elasticsearch
```
python load_elastic.py --index_name chemu --file_flag 1 --dir_file_name slot_sample.json
```
Note that, if you change `--index_name` in the command, you need to update the `index_name` in `load_elastic.py` accordingly. Also, if you have a large dataset, this step may take a while.

### 4. Start the search engine
```
cd SynKB
python manage.py runserver 0.0.0.0:YOUR_PORT
```

## Semantic Graph Search

### 1. Prepare your data
Format your semantic graph data as [semantic_graph_sample.json](./semantic_graph_sample.json).

### 2. Convert your data into pre-indexed Odinson format
```
python convert_odinson_format.py --input_file semantic_graph_sample.json --output_dir OUPUT_DIR
```

### 3. Set up Odinson (Java 11 is required)
```
git clone https://github.com/bflashcp3f/odinson.git
cd odinson
git checkout synkb
```

### 4. Set up pre-indexed data
```
mkdir -p extra/data/pets/docs
mv PRE-INDEXED_DATA/* extra/data/pets/docs
```

### 5. Index your data 
```
sbt "extra/runMain ai.lum.odinson.extra.IndexDocuments"
```

### 6. Launch Odinson
```
sbt backend/run
```