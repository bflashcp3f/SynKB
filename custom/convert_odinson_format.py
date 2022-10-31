import math
import glob
import time
import json
import pickle
import os
import numpy as np
import operator
import time
import random
import re
import torch
import sys
import string
import argparse

from random import sample
from datetime import datetime
from nltk.tokenize import word_tokenize

from collections import defaultdict, Counter, OrderedDict


def load_from_jsonl(file_name):
    data_list = []
    with open(file_name) as f:
        for line in f:
            data_list.append(json.loads(line))

    return data_list


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
                    ent_idx_list.append((ent_idx_queue[0], ent_idx_queue[-1]))

                    assert len(set(ent_type_queue)) == 1
                    ent_type_list.append(ent_type_queue[0])

            ent_queue, ent_idx_queue, ent_type_queue = [], [], []

    return ent_list, ent_idx_list, ent_type_list


def convert_annotated_to_index(data_dir, output_dir):

    print(data_dir)

    ner_re_merged = load_from_jsonl(data_dir)

    for ner_re_idx, ner_re_ann in enumerate(ner_re_merged[:]):

        if ner_re_idx % 1000 == 0:
            print("# files: ", ner_re_idx, datetime.now())

        file_id = ner_re_ann['id'].split('.')[0]
        ner_ann = ner_re_ann['ner']
        re_ann = ner_re_ann['re']

        json_data = {}
        json_data['id'] = file_id.split('_')[-1]
        json_data['metadata'] = []
        sentences = []

        for sen_idx, (word_per_sen, label_per_sen) in enumerate(ner_ann):

            assert len(word_per_sen) == len(label_per_sen)

            ent_list, ent_idx_list, ent_type_list = index_ent_in_prediction(word_per_sen, label_per_sen)
            ent_start_list = [item[0] for item in ent_idx_list]

            re_ann_per_sen = re_ann.get(str(sen_idx), [])
            re_ann_per_sen_lowered = [(arg1_start, arg2_start, relation.lower())
                                      for arg1_start, arg2_start, relation in re_ann_per_sen]

            for arg1_start, arg2_start, relation in re_ann_per_sen:
                assert arg1_start in ent_start_list
                assert arg2_start in ent_start_list

            each_sen_dict = {}

            fields = []

            # token
            fields.append({'tokens': word_per_sen, '$type': 'ai.lum.odinson.TokensField', 'name': 'raw'})

            # word
            fields.append({'tokens': word_per_sen, '$type': 'ai.lum.odinson.TokensField', 'name': 'word'})

            # entity
            fields.append({'tokens': label_per_sen, '$type': 'ai.lum.odinson.TokensField', 'name': 'entity'})

            # rel
            fields.append(
                {'edges': re_ann_per_sen_lowered, '$type': 'ai.lum.odinson.GraphField', 'name': 'dependencies',
                 'roots': [0]})

            each_sen_dict['fields'] = fields
            each_sen_dict['numTokens'] = len(word_per_sen)
            sentences.append(each_sen_dict)

        json_data['sentences'] = sentences

        output_path = os.path.join(output_dir, f"{file_id}.json")

        with open(output_path, 'w') as f:
            json.dump(json_data, f)



def main(args):

    convert_annotated_to_index(args.input_file, args.output_dir)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--input_file", type=str, default=None)
    parser.add_argument("--output_dir", type=str, default=None)

    args = parser.parse_args()
    main(args)

    # python convert_odinson_format.py --input_file semantic_graph_sample.json --output_dir OUPUT_DIR