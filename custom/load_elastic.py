from elasticsearch import Elasticsearch
from elasticsearch import helpers

import json
import argparse
import numpy as np
import gzip
import glob

from collections import defaultdict

### declare the client
es_client = Elasticsearch(hosts="http://127.0.0.1:9200/", timeout=30, max_retries=10, retry_on_timeout=True)
RANDOM_SEED = 901

TEXT_TYPE = "text"
KEYWORD_TYPE = "keyword"


def readJSONLine(path):

    output = []
    with open(path, 'r') as f:
        for line in f:
            output.append(json.loads(line))

    return output


def writeGZIPJSONLine(data, location):
    with gzip.open(location, "wb") as f:
        for each_line in data:
            f.write((json.dumps(each_line)+'\n').encode())


def deleteIndex(index_name):
    es_client.indices.delete(index_name)
    return None


def buildIndex(index_name):

    mappings = {"mappings": {
        "chemu": {
            "properties": {
                "id": {"type": KEYWORD_TYPE, "index": True},
                ## TEXT SEARCH
                "product": {"type": TEXT_TYPE, "index": True},
                "reagent": {"type": TEXT_TYPE, "index": True},
                "solvent": {"type": TEXT_TYPE, "index": True},
                "other_compound": {"type": TEXT_TYPE, "index": True},
                "starting_material": {"type": TEXT_TYPE, "index": True},
                "temperature": {"type": TEXT_TYPE, "index": True},
                "time": {"type": TEXT_TYPE, "index": True},
                "yield_other": {"type": TEXT_TYPE, "index": True},
                "yield_percent": {"type": TEXT_TYPE, "index": True},
                "word": {"type": TEXT_TYPE, "index": True},
            }
        }
    }
    }

    ## generate index
    es_client.indices.create(index=index_name, body=mappings)

    return None


def insertToES(index_name, input_data):

    action = [{
        "_index": index_name,
        "_type": "chemu",
        "_id": each_line['id'],
        "_source": {
            "id": each_line['id'],
            ## TEXT SEARCH
            "product": each_line['REACTION_PRODUCT'],
            "reagent": each_line['REAGENT_CATALYST'],
            "solvent": each_line['SOLVENT'],
            "other_compound": each_line['OTHER_COMPOUND'],
            "starting_material": each_line['STARTING_MATERIAL'],
            "temperature": each_line['TEMPERATURE'],
            "time": each_line['TIME'],
            "yield_other": each_line['YIELD_OTHER'],
            "yield_percent": each_line['YIELD_PERCENT'],
            "word": each_line['word'],
        }
    } for each_line in input_data]

    helpers.bulk(es_client, action)

    return None


def index_ent_in_prediction(word_list, tag_list):
    ent_queue, ent_idx_queue, ent_type_queue = [], [], []
    ent_list, ent_idx_list, ent_type_list = [], [], []

    for word_idx in range(len(word_list)):

        if 'B-' in tag_list[word_idx]:
            if ent_queue:

                if len(set(ent_type_queue)) != 1:
                    print(ent_queue)
                    print(ent_idx_queue)
                    print(ent_type_queue)
                    print(Counter(ent_type_queue).most_common())
                    print()

                else:
                    ent_list.append(' '.join(ent_queue).strip())
                    #                     ent_idx_list.append((ent_idx_queue[0], ent_idx_queue[-1]+1))
                    ent_idx_list.append((ent_idx_queue[0], ent_idx_queue[-1]))

                    assert len(set(ent_type_queue)) == 1
                    ent_type_list.append(ent_type_queue[0])

            ent_queue, ent_idx_queue, ent_type_queue = [], [], []
            ent_queue.append(word_list[word_idx])
            ent_idx_queue.append(word_idx)
            ent_type_queue.append(tag_list[word_idx][2:])

        if 'I-' in tag_list[word_idx]:
            if word_idx == 0 or (word_idx > 0 and tag_list[word_idx][2:] == tag_list[word_idx - 1][2:]):
                ent_queue.append(word_list[word_idx])
                ent_idx_queue.append(word_idx)
                ent_type_queue.append(tag_list[word_idx][2:])
            else:
                if ent_queue:

                    if len(set(ent_type_queue)) != 1:
                        print(ent_queue)
                        print(ent_idx_queue)
                        print(ent_type_queue)
                        print(Counter(ent_type_queue).most_common())
                        print()
                    else:
                        ent_list.append(' '.join(ent_queue).strip())
                        #                         ent_idx_list.append((ent_idx_queue[0], ent_idx_queue[-1]+1))
                        ent_idx_list.append((ent_idx_queue[0], ent_idx_queue[-1]))

                        assert len(set(ent_type_queue)) == 1
                        ent_type_list.append(ent_type_queue[0])

                ent_queue, ent_idx_queue, ent_type_queue = [], [], []
                ent_queue.append(word_list[word_idx])
                ent_idx_queue.append(word_idx)
                ent_type_queue.append(tag_list[word_idx][2:])

        if 'O' == tag_list[word_idx] or word_idx == len(word_list) - 1:
            if ent_queue:

                if len(set(ent_type_queue)) != 1:
                    print(ent_queue)
                    print(ent_idx_queue)
                    print(ent_type_queue)
                    print(Counter(ent_type_queue).most_common())
                    print()

                else:
                    ent_list.append(' '.join(ent_queue).strip())
                    #                     ent_idx_list.append((ent_idx_queue[0], ent_idx_queue[-1]+1))
                    ent_idx_list.append((ent_idx_queue[0], ent_idx_queue[-1]))

                    assert len(set(ent_type_queue)) == 1
                    ent_type_list.append(ent_type_queue[0])

            ent_queue, ent_idx_queue, ent_type_queue = [], [], []

    return ent_list, ent_idx_list, ent_type_list


def dataPreprocessing(input_data):

    CheMU_ENT_NAME = ['EXAMPLE_LABEL', 'OTHER_COMPOUND', 'REACTION_PRODUCT', 'REAGENT_CATALYST', 'SOLVENT',
                      'STARTING_MATERIAL', 'TEMPERATURE', 'TIME', 'YIELD_OTHER', 'YIELD_PERCENT']

    input_data_processed = []

    ner_data_merged = {k: v for d in input_data for k, v in d.items()}

    for file_id, word_label_list in list(ner_data_merged.items()):

        # print(file_id)
        ent_type_dict = defaultdict(list)
        word_all = []

        for sen_idx, (word_per_sen, label_per_sen) in enumerate(word_label_list):
            assert len(word_per_sen) == len(label_per_sen)

            ent_list, ent_idx_list, ent_type_list = index_ent_in_prediction(word_per_sen, label_per_sen)
            # print(list(zip(ent_list, ent_idx_list, ent_type_list)))
            # print(word_per_sen)

            offset = len(word_all)
            word_all += word_per_sen

            if sen_idx == 0:
                word_all += ['<br>']

            for ent, ent_idx, ent_type in zip(ent_list, ent_idx_list, ent_type_list):
                # print(ent, ent_idx, ent_type)
                ent_idx_start, ent_idx_end = ent_idx

                assert word_all[ent_idx_start+offset] == word_per_sen[ent_idx_start]
                assert word_all[ent_idx_end+offset] == word_per_sen[ent_idx_end]

                ent_type_dict[ent_type].append(f"{ent}::{ent_idx_start+offset}::{ent_idx_end+offset+1}")

        # print(ent_type_dict)
        ent_type_dict_final = {}
        ent_type_dict_final["id"] = file_id
        ent_type_dict_final["word"] = "  ".join(word_all)

        if "REACTION_PRODUCT" in ent_type_dict:
            # Make sure to find the best product
            react_prod_list = [[react_prod, len(react_prod.split("::")[0])] for react_prod in ent_type_dict["REACTION_PRODUCT"]]
            react_prod_list_sorted = sorted(react_prod_list, key=lambda x:x[1], reverse=True)

            for react_prod, _ in react_prod_list_sorted:
                if "compound" in react_prod.lower() or "product" in react_prod.lower():
                    continue
                else:
                    ent_type_dict_final["REACTION_PRODUCT"] = react_prod.strip(".")
                    break
        # else:
        if "REACTION_PRODUCT" not in ent_type_dict_final:
            ent_type_dict_final["REACTION_PRODUCT"] = ""


        for chemu_filter in CheMU_ENT_NAME:

            if chemu_filter == "REACTION_PRODUCT":
                continue

            if chemu_filter in ent_type_dict:
                ent_type_dict_final[chemu_filter] = " %%%%% ".join(list(set(ent_type_dict[chemu_filter])))
            else:
                ent_type_dict_final[chemu_filter] = ""

        # print(ent_type_dict_final)
        input_data_processed.append(ent_type_dict_final)
        # break

    return input_data_processed



def loadData(index_name, file_flag, dir_file_name):

    print(index_name, file_flag, dir_file_name)
    input_data = []
    print(file_flag)

    ## read in data
    if file_flag:
        print(dir_file_name)
        input_data = readJSONLine(dir_file_name)
    else:
        for file_path in glob.glob(f'{dir_file_name}/*'):
            print(file_path)
            input_data += readJSONLine(file_path)

    print('length of input data', len(input_data))

    ## random shuffle
    np.random.seed(RANDOM_SEED)
    np.random.shuffle(input_data)

    input_data_processed = dataPreprocessing(input_data)
    # print(input_data_processed[:10])

    ## first delete previous index
    try:
        deleteIndex(index_name)
    except:
        pass

    ## build new index
    buildIndex(index_name)

    ## load data
    insertToES(index_name, input_data_processed)

    return None


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("--index_name", type=str, required=True)
    parser.add_argument("--dir_file_name", type=str, required=True)
    parser.add_argument("--file_flag", type=int, required=True)

    args = parser.parse_args()

    print(args.index_name, args.file_flag, args.dir_file_name)

    loadData(args.index_name, args.file_flag, args.dir_file_name)

    ### commands
    # python load_elastic.py --index_name chemu --file_flag 1 --dir_file_name slot_sample.json
    # python load_elastic.py --index_name chemu --file_flag 0 --dir_file_name ner/
