
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
