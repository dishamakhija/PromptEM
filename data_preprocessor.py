import os
import numpy as np
import collections
import itertools
import csv
import random

class GeneratedDataPreprocessor:
    ## Pre-processes the generated data files to convert it into a format required by PromptEM
    ## which includes files corresponding to left.csv, right.csv, train.csv, test.csv, val.csv

    def __init__(self, input_data_path, output_data_path, start_prompt = "", conjunction_prompt_pos = "", conjunction_prompt_neg = "", end_prompt = ""):
        self.positive_entities_path = input_data_path + "/positive_entities.txt"
        self.negative_entities_path = input_data_path + "/negative_entities.txt"
        self.output_data_path = output_data_path
        self.start_prompt = start_prompt
        self.conjunction_prompt_pos = conjunction_prompt_pos
        self.conjunction_prompt_neg = conjunction_prompt_neg
        self.end_prompt = end_prompt + "\n"

    def create_dataset(self, train_ratio, test_ratio):
        ## Calls functions to map the entities into unique integers and then divides the entity
        ## pairs into train, test and val datasets and writes them on disk

        mapped_entities, mappings = self.create_entites()
        print(os.path.join(self.output_data_path,"left"+".csv"))
        files = ['left','right']
        for file_name in files:
            with open(os.path.join(self.output_data_path,file_name+""), 'w') as f:
                writer = csv.writer(f)
                for key in mappings.keys():
                    writer.writerow([mappings[key].strip()])
            f.close()

        train, test, val = self.create_train_test_val_split(mapped_entities, train_ratio, test_ratio )
        data_segs = {"train" : train, "test" : test, "valid": val}
        for data_seg in data_segs.keys():
            print(data_seg)
            with open(os.path.join(self.output_data_path,data_seg+".csv"), 'w') as f:
                writer = csv.writer(f)
                for line in data_segs[data_seg]:
                    print(line)
                    writer.writerow((line))
            f.close()

    def read_entites_and_split(self, file_name, conjunction_prompt):
        ## Reads the raw entity files to create python lists for easy usage
        with open(file_name, 'r') as f:
            entity_pairs_lines = f.readlines()

        left_entites = []
        right_entites = []

        for line in entity_pairs_lines:
            if self.start_prompt !="" and self.start_prompt in line:
                current_line = line.split(self.start_prompt)[1]
            if self.end_prompt !="" and self.end_prompt in line:
                current_line = current_line.split(self.end_prompt)[0]

            if conjunction_prompt !="" and conjunction_prompt in line:
                entites = current_line.split(conjunction_prompt)
                left_entites.append(entites[0])
                right_entites.append(entites[1])

        return left_entites, right_entites

    def create_entites(self):
        ## calls the read function and then maps the set of lists to a common set of unique numbers
        positive_left_entites, positive_right_entities =  self.read_entites_and_split(self.positive_entities_path,self.conjunction_prompt_pos)
        negative_left_entites, negative_right_entities =  self.read_entites_and_split(self.negative_entities_path, self.conjunction_prompt_neg)
        mapped_entities, mappings = self.map_entities([positive_left_entites, positive_right_entities,
                                                       negative_left_entites, negative_right_entities])

        return mapped_entities, mappings


    def map_entities(self, entity_lists):
        ## A custom mapper function

        #counter = itertools.count().next
        #names = collections.defaultdict(next(itertools.count()))
        counter = itertools.count().__next__
        names = collections.defaultdict(counter)

        mapped_entities = []
        for entity_list in entity_lists:
            new_list = [names[item] for item in entity_list]
            mapped_entities.append(new_list)
        mappings = dict((name, idx) for idx, name in names.items())

        return mapped_entities, mappings

    def create_train_test_val_split(self, mapped_entities, train_ratio = 0.7, test_ratio = 0.15):
        ## Creates train-test-val split from positive entity pairs and negative entity pairs
        print(mapped_entities)
        positive_pair_left, positive_pair_right = mapped_entities[0], mapped_entities[1]
        negative_pair_left, negative_pair_right = mapped_entities[2], mapped_entities[3]

        num_pos_pairs_train = int(np.floor(train_ratio * len(positive_pair_left)))
        num_pos_pairs_test = int(np.floor(test_ratio * len(positive_pair_left)))
        num_pos_pairs_val = len(positive_pair_left) - num_pos_pairs_train - num_pos_pairs_test

        num_neg_pairs_train = int(np.floor(train_ratio * len(negative_pair_left)))
        num_neg_pairs_test = int(np.floor(test_ratio * len(negative_pair_left)))
        num_neg_pairs_val = len(negative_pair_left) - num_neg_pairs_test - num_neg_pairs_train

        positive_pairs = list(zip(positive_pair_left, positive_pair_right))
        positive_pairs = [list(tup)+[1] for tup in positive_pairs]
        negative_pairs = list(zip(negative_pair_left, negative_pair_right))
        negative_pairs = [list(tup)+[0] for tup in negative_pairs]

        random.shuffle(positive_pairs)
        random.shuffle(negative_pairs)

        train = []
        test = []
        val = []
        print("!11")
        print(positive_pairs)
        print(negative_pairs)
        if num_pos_pairs_train > 0 :
            train.extend(positive_pairs[:num_pos_pairs_train])
        if num_neg_pairs_train > 0 :
            train.extend(negative_pairs[:num_neg_pairs_train])
        if num_pos_pairs_test > 0 :
            test.extend(positive_pairs[num_pos_pairs_train:num_pos_pairs_train+num_pos_pairs_test])
        if  num_neg_pairs_test > 0:
            test.extend(negative_pairs[num_neg_pairs_train:num_neg_pairs_train+num_neg_pairs_test])
        if num_pos_pairs_val > 0 :
            val.extend(positive_pairs[-num_pos_pairs_val:])
        if  num_neg_pairs_val > 0:
            val.extend(negative_pairs[-num_neg_pairs_val:])
        return train, test, val
