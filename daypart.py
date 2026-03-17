import pandas as pd

class Daypart():
    
    def __init__(self, network:str, daypart_type:str, daypart:str, midas_cpm:float, videoamp_imps:int, nielsen_imps:int, videoamp_cpm:float, midas_cost_row:float, requires_prime:bool, 
                 relevant_prime_daypart_name:str, num_buys_relative_to_prime_daypart:int, ecpm:float, num_buys:int, broadcast:bool=False, cable_news:bool=False):
        self.network = network
        self.daypart_type = daypart_type
        self.daypart = daypart
        self.midas_cpm = midas_cpm
        self.requires_prime = requires_prime
        self.prime_value = 1 if requires_prime else 0
        self.nielsen_imps = nielsen_imps
        self.videoamp_imps = videoamp_imps
        self.videoamp_cpm = videoamp_cpm
        self.midas_cost_row = midas_cost_row
        self.relevant_prime_daypart_name = relevant_prime_daypart_name # Allows us to dynamically calculate prime daypart buys later on
        self.num_buys_relative_to_prime_daypart = num_buys_relative_to_prime_daypart if requires_prime else None 
        self.ecpm = ecpm
        self.num_buys = num_buys if num_buys else None
        self.broadcast = broadcast
        self.cable_news = cable_news


    def __str__(self):
        string = ''
        for key, val in self.__dict__.items():
            string+= f'{key} : {val}\n' 
        return string
    
    @staticmethod
    def to_dataframe(dayparts_list):
        data = {
            'network': [],
            'daypart_type': [],
            'daypart': [],
            'midas_cpm': [],
            'videoamp_imps': [],
            'nielsen_imps': [],
            'videoamp_cpm': [],
            'requires_prime': [],
            'prime_value': [],
            'relevant_prime_daypart_name': [],
            'num_buys_relative_to_prime_daypart': [],
            'ecpm': [],
            'midas_cost_row': [],
            'num_buys': [],
            'broadcast': [],
            'cable_news': []
        }

        for dp in dayparts_list:
            data['network'].append(dp.network)
            data['daypart_type'].append(dp.daypart_type)
            data['daypart'].append(dp.daypart)
            data['midas_cpm'].append(dp.midas_cpm)
            data['nielsen_imps'].append(dp.nielsen_imps)
            data['videoamp_imps'].append(dp.videoamp_imps)
            data['videoamp_cpm'].append(dp.videoamp_cpm)
            data['requires_prime'].append(dp.requires_prime)
            data['prime_value'].append(dp.prime_value)
            data['relevant_prime_daypart_name'].append(dp.relevant_prime_daypart_name)
            data['num_buys_relative_to_prime_daypart'].append(dp.num_buys_relative_to_prime_daypart)
            data['ecpm'].append(dp.ecpm)
            data['midas_cost_row'].append(dp.midas_cost_row)
            data['num_buys'].append(dp.num_buys)
            data['broadcast'].append(dp.broadcast)
            data['cable_news'].append(dp.cable_news)

        return pd.DataFrame(data)