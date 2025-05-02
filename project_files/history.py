import os
import json


### History ###
# four previous measurements are saved to one file, history.json
# measurement includes information about date and time, mean hr, mean ppi, rmssd and sdnn (+ sns and pns)
# saving a new measurement increases previous measurements indexes (index keeps track of creation order)
# after saving a fifth measurement (to first index), the oldest measurement is deleted (fifth index)


class History:
    def __init__(self):
        self.max_measurements = 4  # max histories saved at one time
        self.history_file_name = 'history.json'  # all history data is stored in this file
    
    def read_from_history_file(self):
        try:
            # open file in read mode
            with open(self.history_file_name, 'r') as file:
                file_content = json.load(file)
                return file_content
        except Exception as e:  # file not found
            #print('Error:', e)
            return []
    
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
        # add newest data as first index
        data.update({0: new_data})
        
        # extend history file with new data if file exists, otherwise replace content (which doesn't exist anyway)
        existing_data = self.read_from_history_file()
        
        if existing_data:
            # increase existing data indexes
            for key, value in existing_data.items():
                new_index = int(key) + 1
                # only save data if its index is within max
                if new_index <= self.max_measurements - 1:
                    data.update({new_index: value})
        return data
    
    def save_to_history(self, new_data):
        data = self.combine_new_data_with_old_data(new_data)
        self.write_to_history_file(data)

