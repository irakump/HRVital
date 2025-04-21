import os
import json


### History ###
# four previous data points are saved to one file, history.json
# data point includes information about data and time, mean hr, mean ppi, rmssd and sdnn (+ sns and pns)
# saving a new data point increases previous data points indexes (index keeps track of data point order)
# after saving a fifth data point (to first index), the oldest data point is deleted (fifth index)


class History:
    def __init__(self):
        self.max_histories_to_store = 4  # max histories saved at one time
        self.history_file_name = 'history.json'  # all history data is stored in this file
    
    def read_from_history_file(self):
        try:
            # open file in read mode
            with open(self.history_file_name, 'r') as file:
                file_content = json.load(file)
                return file_content
        except Exception as e:  # file not found
            #print('Error:', e)
            return False
    
    def write_to_history_file(self, data):
        # open file in write mode, creates file if it does not exist
        with open(self.history_file_name, 'w') as file:
            json.dump(data, file)
    
    def delete_history_file(self):  # for debugging
        # loop through all files and check for name match with history file
        # delete history file if found
        [os.remove(file) for file in os.listdir() if file == self.history_file_name]
    
    def combine_new_data_with_old_data(self, new_data):
        data = dict()
        
        # extend history file with new data if file exists, otherwise replace content (which doesn't exist anyway)
        existing_data = self.read_from_history_file()
        
        if existing_data:
            # shift all existing data indexes up by one
            shifted_existing_data = dict()
            for key, value in existing_data.items():
                new_index = int(key) + 1
                shifted_existing_data.update({new_index: value})
            
            data = shifted_existing_data
        
        # add newest data as first index
        data.update({1: new_data})
        
        # remove entry if its index is larger than maximum allowed
        while len(data) > self.max_histories_to_store:
            for key, value in data.items():
                if key > self.max_histories_to_store:
                    data.pop(key)
        return data
    
    def save_to_history(self, new_data):
        
        # kutsu tätä funktiota datalla (alla oleva muoto on esimerkki)
        new_data = {
            'date_and_time': '1.1.2025 10:10',
            'mean_hr': 76,
            'mean_ppi': 750,
            'rmssd': 23,
            'sdnn': 22,
            'sns': 1.234,
            'pns': -1.234,
        }
        
        data = self.combine_new_data_with_old_data(new_data)
        self.write_to_history_file(data)


history = History()
#history.delete_history_file()

#history.save_to_history('this is placeholder')

#data = history.read_from_history_file()
#print(data)
