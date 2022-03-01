from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from django.db.models import Q # new

from .models import Search

import csv
import urllib
import requests

from collections import Counter, defaultdict
from django.http import HttpResponse


class HomePageView(TemplateView):
    template_name = 'home.html'


class OdinsonView(TemplateView):
    template_name = 'odinson.html'

AGGREGATE_CHAR = ['*', '?']


def build_odinson_query(input_str, corpus_source="PubMed articles"):
    param_str = urllib.parse.urlencode({"odinsonQuery": input_str})

    if corpus_source == "PubMed articles":
        return f"http://localhost:8999/api/execute/pattern?{param_str}"
    else:
        return f"http://localhost:9000/api/execute/pattern?{param_str}"


def build_odinson_query_w_meta(input_str, chemu_filter):
    meta_query_list = []
    for filter_name, filter_value in chemu_filter.items():
        if filter_value and filter_value not in AGGREGATE_CHAR:
            meta_query = f"{filter_name} contains '{filter_value}'"
            meta_query_list.append(meta_query)
    meta_query_all = " and ".join(meta_query_list)

    param_str = urllib.parse.urlencode({"odinsonQuery": input_str, 'metadataQuery': meta_query_all})

    return f"http://localhost:9000/api/execute/pattern?{param_str}"


# Control the length of the presented captures
def length_control(str_list, length_list=120):
    return [item if len(item) <= length_list else item[:length_list-3]+"..." for item in str_list]


def build_elasticsearch_query(chemu_input):
    # return f"http://localhost:9200/chemu/_search?q=product:{prod_str}%20AND%20reagent:{reag_str}%20AND%20solvent:{solv_str}&size=500000"

    parameter_list = []
    for chemu_item, chemu_value in chemu_input.items():
        if chemu_value:
            parameter_list.append(f"{chemu_item}:{chemu_value}")

    parameter_str = "%20AND%20".join(parameter_list)

    return f"http://localhost:9200/chemu/_search?q={parameter_str}&size=10000"


def aggregate_captures_es_only(es_results, chemu_input, capture_num=50):

    captures_all = []
    captures_sen_dict = defaultdict(list)

    for each_hit in es_results:

        docid = each_hit['id']
        words = each_hit['word'].split("  ")

        # Make sure the return paraphrases have reasonable length
        if len(words) > 3000:
            continue

        chemu_flag = {chemu_item:False for chemu_item, chemu_value in chemu_input.items()}
        chemu_ent_str_ent = {}

        try:
            for chemu_item, chemu_value in chemu_input.items():

                if chemu_item == 'product': # There should be only one product for each procedure
                    if chemu_value:
                        if chemu_item in each_hit and len(each_hit[chemu_item].split("::")) == 3:

                            each_hit_str, each_hit_ent_start, each_hit_ent_end = each_hit[chemu_item].split("::")
                            chemu_ent_str_ent[chemu_item] = [int(each_hit_ent_start), int(each_hit_ent_end), each_hit_str]
                            chemu_flag[chemu_item] = True
                        else:
                            raise
                else:
                    if chemu_value:
                        if chemu_item in each_hit and each_hit[chemu_item] != "":
                            each_hit_item_list = each_hit[chemu_item].split(" %%%%% ")
                            each_hit_str_ent_list = []

                            for each_hit_item in each_hit_item_list:
                                each_hit_item_str, each_hit_item_ent_start, each_hit_item_ent_end = each_hit_item.split("::")
                                each_hit_item_ent_start, each_hit_item_ent_end = int(each_hit_item_ent_start), int(each_hit_item_ent_end)
                                each_hit_str_ent_list.append([each_hit_item_ent_start, each_hit_item_ent_end, each_hit_item_str])

                            chemu_ent_str_ent[chemu_item] = each_hit_str_ent_list
                            chemu_flag[chemu_item] = True
                        else:
                            raise
        except:
            continue

        docid = docid.split('_')[-1]

        captures_per_sen = []
        cap_str_dict = {}

        # Add ChemU entities
        cap_chemu_list = []
        for chemu_item, chemu_value in chemu_input.items():
            if chemu_flag[chemu_item]:
                if chemu_item == 'product':
                    each_hit_ent_start, each_hit_ent_end, each_hit_str = chemu_ent_str_ent[chemu_item]
                    cap_str_dict[each_hit_ent_start] = chemu_ent_str_ent[chemu_item]
                    cap_chemu_list.append(f"<b>{chemu_item}</b> : {each_hit_str}")
                else:
                    each_hit_ent_str_list = chemu_ent_str_ent[chemu_item]
                    for each_hit_str_ent in each_hit_ent_str_list:
                        cap_str_dict[each_hit_str_ent[0]] = each_hit_str_ent
                    each_hit_str_all = " \\ ".join([item[-1] for item in each_hit_ent_str_list])
                    cap_chemu_list.append(f"<b>{chemu_item}</b> : {each_hit_str_all}")

        word_index = 0
        words_new = []
        while word_index < len(words):
            if word_index not in cap_str_dict:
                words_new.append(words[word_index])
                word_index += 1
            else:
                span_start, span_end, span_str = cap_str_dict[word_index]
                words_new.append(f"<b>{span_str}</b>")
                word_index = span_end

        captures_per_sen.append("  |  ".join(cap_chemu_list))
        captures_sen_dict["  |  ".join(cap_chemu_list)].append((docid.strip('/').split('/')[-1], " ".join(words_new)))

        captures_all += captures_per_sen

    captures_list = sorted(Counter(captures_all).items(), key=lambda x: x[1], reverse=True)[:capture_num]
    captures_sen_list = [captures_sen_dict[each_capture] for each_capture, _ in captures_list]

    captures_list = [(item[0], item[1], captures_sen_dict[item[0]]) for item in captures_list]

    return captures_list, captures_sen_list


def aggregate_captures(odin_results, capture_num=50):
    captures_all = []
    captures_sen_dict = defaultdict(list)

    for matched_item in odin_results:

        # docid = matched_item['documentId']
        docid = matched_item['documentId'].split('_')[-1]
        words = matched_item['words']

        if 'matches' in matched_item:
            matches = matched_item['matches']

            # cap_str_dict = {}
            captures_per_sen = []
            for each_match in matches:

                if 'captures' in each_match:
                    cap_str_dict = {}
                    cap_list = []
                    for each_capture in each_match['captures']:
                        for cap_name, cap_content in each_capture.items():
                            cap_start, cap_end = cap_content['span']['start'], cap_content['span']['end']
                            cap_str = " ".join(words[cap_start:cap_end])
                            # cap_list.append(f"{cap_name}:{cap_str}")
                            cap_list.append(f"<b>{cap_name}</b> : {cap_str}")
                            cap_str_dict[cap_start] = [cap_start, cap_end, cap_str]

                    word_index = 0
                    words_new = []
                    while word_index < len(words):

                        if word_index not in cap_str_dict:
                            words_new.append(words[word_index])
                            word_index += 1
                        else:
                            span_start, span_end, span_str = cap_str_dict[word_index]
                            words_new.append(f"<b>{span_str}</b>")
                            word_index = span_end

                    captures_per_sen.append("  |  ".join(sorted(cap_list)))
                    captures_sen_dict["  |  ".join(sorted(cap_list))].append(
                        (docid.strip('/').split('/')[-1], " ".join(words_new)))
                    # captures_all.append(len(cap_list))

            captures_all += captures_per_sen

    captures_list = sorted(Counter(captures_all).items(), key=lambda x: x[1], reverse=True)[:capture_num]
    captures_sen_list = [captures_sen_dict[each_capture] for each_capture, _ in captures_list]
    captures_list = [(item[0], item[1], captures_sen_dict[item[0]]) for item in captures_list]

    return captures_list, captures_sen_list


def aggregate_captures_es_ids(odin_results, chemu_input, capture_num=50):
    docid_dict_odin = {matched_item['documentId']: '' for matched_item in odin_results}

    es_id_dict = {each_hit['_id']: each_hit['_source'] for each_id in docid_dict_odin.keys()
                  for each_hit in
                  requests.get(f"http://localhost:9200/chemu/_search?q=id:{each_id}").json()['hits']['hits']}

    captures_all = []
    captures_sen_dict = defaultdict(list)

    for matched_item in odin_results:

        docid = matched_item['documentId']
        words = matched_item['words']

        chemu_flag = {chemu_item: False for chemu_item, chemu_value in chemu_input.items()}
        chemu_ent_str_ent = {}

        if docid not in es_id_dict:
            continue
        else:

            try:
                for chemu_item, chemu_value in chemu_input.items():

                    if chemu_item == 'product':
                        if chemu_value:
                            if chemu_item in es_id_dict[docid] and \
                                    chemu_value in es_id_dict[docid][chemu_item] and len(
                                es_id_dict[docid][chemu_item].split("::")) == 3:

                                each_hit_str, each_hit_ent_start, each_hit_ent_end = es_id_dict[docid][
                                    chemu_item].split(
                                    "::")
                                chemu_ent_str_ent[chemu_item] = [int(each_hit_ent_start), int(each_hit_ent_end),
                                                                 each_hit_str]
                                chemu_flag[chemu_item] = True
                            else:
                                raise
                    else:

                        if chemu_value:
                            if chemu_item in es_id_dict[docid] and \
                                    chemu_value in es_id_dict[docid][chemu_item] and es_id_dict[docid][
                                chemu_item] != "":
                                each_hit_item_list = es_id_dict[docid][chemu_item].split(" %%%%% ")
                                each_hit_str_ent_list = []

                                for each_hit_item in each_hit_item_list:
                                    each_hit_item_str, each_hit_item_ent_start, each_hit_item_ent_end = each_hit_item.split(
                                        "::")
                                    each_hit_item_ent_start, each_hit_item_ent_end = int(
                                        each_hit_item_ent_start), int(each_hit_item_ent_end)
                                    each_hit_str_ent_list.append(
                                        [each_hit_item_ent_start, each_hit_item_ent_end, each_hit_item_str])

                                chemu_ent_str_ent[chemu_item] = each_hit_str_ent_list
                                chemu_flag[chemu_item] = True
                            else:
                                raise
            except:
                continue

        docid = docid.split('_')[-1]

        if 'matches' in matched_item:
            matches = matched_item['matches']

            # cap_str_dict = {}
            captures_per_sen = []
            for each_match in matches:

                if 'captures' in each_match:
                    cap_str_dict = {}

                    # Add ChemU entities
                    cap_chemu_list = []
                    for chemu_item, chemu_value in chemu_input.items():
                        if chemu_flag[chemu_item]:
                            if chemu_item == 'product':
                                each_hit_ent_start, each_hit_ent_end, each_hit_str = chemu_ent_str_ent[
                                    chemu_item]
                                cap_str_dict[each_hit_ent_start] = chemu_ent_str_ent[chemu_item]
                                cap_chemu_list.append(f"<b>{chemu_item}</b> : {each_hit_str}")
                            else:
                                each_hit_ent_str_list = chemu_ent_str_ent[chemu_item]
                                for each_hit_str_ent in each_hit_ent_str_list:
                                    cap_str_dict[each_hit_str_ent[0]] = each_hit_str_ent
                                each_hit_str_all = " \\ ".join([item[-1] for item in each_hit_ent_str_list])
                                cap_chemu_list.append(f"<b>{chemu_item}</b> : {each_hit_str_all}")

                    cap_list = []
                    for each_capture in each_match['captures']:
                        for cap_name, cap_content in each_capture.items():
                            cap_start, cap_end = cap_content['span']['start'], cap_content['span']['end']
                            cap_str = " ".join(words[cap_start:cap_end])
                            # cap_list.append(f"{cap_name}:{cap_str}")
                            cap_list.append(f"<b>{cap_name}</b> : {cap_str}")
                            cap_str_dict[cap_start] = [cap_start, cap_end, cap_str]

                    word_index = 0
                    words_new = []
                    while word_index < len(words):
                        if word_index not in cap_str_dict:
                            words_new.append(words[word_index])
                            word_index += 1
                        else:
                            span_start, span_end, span_str = cap_str_dict[word_index]
                            words_new.append(f"<b>{span_str}</b>")
                            word_index = span_end

                    captures_per_sen.append("  |  ".join(sorted(cap_list) + cap_chemu_list))
                    captures_sen_dict["  |  ".join(sorted(cap_list) + cap_chemu_list)].append(
                        (docid.strip('/').split('/')[-1], " ".join(words_new)))

            captures_all += captures_per_sen

    captures_list = sorted(Counter(captures_all).items(), key=lambda x: x[1], reverse=True)[:capture_num]
    captures_sen_list = [captures_sen_dict[each_capture] for each_capture, _ in captures_list]
    captures_list = [(item[0], item[1], captures_sen_dict[item[0]]) for item in captures_list]

    return captures_list, captures_sen_list


def search_results(request, download=False):

    query = request.GET.get('q')
    corpus_src = request.GET.get("corpus_src") if request.GET.get("corpus_src") else "Chemical patents"
    # cap_num = int(request.GET.get("cap_num", 10)) if request.GET.get("cap_num") else 10
    cap_num = 100000000 # Setting the number of captures to a very high number to avoid the limit of the API

    # ChEMU filters
    product_str = request.GET.get("product", None)
    reagent_str = request.GET.get('reagent', None)
    solvent_str = request.GET.get('solvent', None)
    other_compound_str = request.GET.get('other_compound', None)
    starting_material_str = request.GET.get('starting_material', None)
    temperature_str = request.GET.get('temperature', None)
    time_str = request.GET.get('time', None)
    yield_other_str = request.GET.get('yother', None)
    yield_percent_str = request.GET.get('ypercent', None)

    chemu_filter = {
        'product': product_str, 'reagent': reagent_str, 'solvent': solvent_str, 'other_compound': other_compound_str,
        'starting_material': starting_material_str, 'temperature': temperature_str, 'time': time_str,
        'yield_other': yield_other_str, 'yield_percent': yield_percent_str
    }

    # Make sure that the query is not empty
    chemu_filter_flag = False
    for key, value in chemu_filter.items():
        if value:
            chemu_filter_flag = True
            break

    # Check whether the Odinson query is valid
    if not query:

        # Check whether the source is PubMed or ChemU filters are empty
        if not (corpus_src == "PubMed articles") and chemu_filter_flag:
            elasticsearch_query = build_elasticsearch_query(chemu_filter)
            r_elastic = requests.get(elasticsearch_query)
            elastic_results = [each_hit['_source'] for each_hit in r_elastic.json()['hits']['hits']]
            captures_list, captures_sen_list = aggregate_captures_es_only(elastic_results, chemu_filter, cap_num)
        else:
            captures_list, captures_sen_list = [], []

    else:

        # Check whether the source is PubMed or ChemSyn
        if corpus_src == "PubMed articles":
            r_odinson = requests.get(build_odinson_query(query, corpus_src), auth=('user', 'pass'))
            captures_list, captures_sen_list = aggregate_captures(r_odinson.json()['scoreDocs'], cap_num)
        else:

            # Check whether there is a valid ChemU filter which should be applied to metadata search
            if sum([True if (chemu_value and chemu_value not in AGGREGATE_CHAR) else False for chemu_item, chemu_value in chemu_filter.items()]):
                r_query = build_odinson_query_w_meta(query, chemu_filter)
                r_odinson = requests.get(r_query, auth=('user', 'pass'))
                captures_list, captures_sen_list = aggregate_captures_es_ids(r_odinson.json()['scoreDocs'],
                                                                             chemu_filter,
                                                                             cap_num)

            elif sum([True if (chemu_value and chemu_value in AGGREGATE_CHAR) else False for chemu_item, chemu_value in chemu_filter.items()]):
                r_odinson = requests.get(build_odinson_query(query, corpus_src), auth=('user', 'pass'))
                captures_list, captures_sen_list = aggregate_captures_es_ids(r_odinson.json()['scoreDocs'],
                                                                             chemu_filter,
                                                                             cap_num)

            else:
                r_odinson = requests.get(build_odinson_query(query, corpus_src), auth=('user', 'pass'))
                captures_list, captures_sen_list = aggregate_captures(r_odinson.json()['scoreDocs'], cap_num)

    if not download:
        captures_list = [(length_control(each_cap[0].split("  |  ")), each_cap[1], each_cap[2]) for each_cap in captures_list]

        return render(request, 'search_results.html',
                      {'query': query,
                       'product_str': chemu_filter['product'],
                       'reagent_str': chemu_filter['reagent'],
                       'solvent_str': chemu_filter['solvent'],
                       'other_compound_str': chemu_filter['other_compound'],
                       'starting_material_str': chemu_filter['starting_material'],
                       'temperature_str': chemu_filter['temperature'],
                       'time_str': chemu_filter['time'],
                       'yield_other_str': chemu_filter['yield_other'],
                       'yield_percent_str': chemu_filter['yield_percent'],
                       'capture_list': captures_list,
                       'cap_num': cap_num,
                       'corpus_src': corpus_src,
                       })
    else:
        captures_list = [(each_cap[0].split("  |  "), each_cap[1], each_cap[2]) for each_cap in captures_list]
        return captures_list



def download_results(request):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="search_results.csv"'},
    )

    captures_list = search_results(request, download=True)

    response.write(u'\ufeff'.encode('utf8'))
    writer = csv.writer(response)

    cap_num = len(captures_list[0][0])
    cap_title = ["DocID"] + [f"Capture{i+1}" for i in range(cap_num)] + ["MatchedParagraph"]

    writer.writerow(cap_title)
    for capture_name_list, capture_count, capture_sen_list in captures_list:
        for doc_id, each_sen in capture_sen_list:
            writer.writerow([doc_id] + capture_name_list[:cap_num] + [each_sen])

    return response

