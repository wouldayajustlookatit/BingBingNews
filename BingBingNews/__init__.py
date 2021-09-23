import time
import requests
import json
import pandas as pd
import datetime

from tqdm import tqdm

# todo: need to add an automatical gitignore
class BingBingNews:
    '''query parameters located at https://docs.microsoft.com/en-us/bing/search-apis/bing-news-search/reference/query-parameters'''
    def __init__(self,subscription_key):
        self.subscription_key = {"Ocp-Apim-Subscription-Key" :subscription_key}
        self.endpoint = 'https://api.bing.microsoft.com/v7.0/news/'

    def _fix_dict_items(self,search:dict,removeVal = None):
        try:
            delkeys = [k for k, v in search.items() if isinstance(v,removeVal)]
        except:
            delkeys = [k for k, v in search.items() if v is removeVal]
        for k in delkeys:
            del search[k]
        return search

    def _get_new_search(self,search):
        try:
            self.res = requests.get(f'{self.endpoint}search/', headers=self.subscription_key, params=search)
            if self.res.status_code == 200 and len(self.res.content) > 0:
                res = self.res.json()['value']
                resResult = [self._fix_dict_items(resDict, removeVal=dict) for resDict in res]
                resResult = [self._fix_dict_items(resDict, removeVal=list) for resDict in resResult]
                return pd.DataFrame(resResult)
            else:
                print(f'Received an HTTP error code: {self.res.status_code} or not data came back')
        except Exception as error:
            print(f'cant get data from endpoint..exception: {error}')

    def news_search(self,query:str,since:datetime.datetime=None,sortBy:str='Date',region='en-US',count:int=100,offset:int=0,allResults:bool=False):
        # https://docs.microsoft.com/en-us/bing/search-apis/bing-news-search/overview
        # try to parse vars
        try:
            since = since.timestamp() * 1000
        except:
            pass

        if sortBy not in ['Date','Relevance',None]:
            raise Exception('incorrect sortBy type. [Date,Relevance] are the only choices')

        search = {'q': query, 'mkt': region,'since':since,'sortBy':sortBy,'count':count,'offset':offset}
        search = self._fix_dict_items(search)

        if not allResults:
            return self._get_new_search(search)
        else:
            news_search = self._get_new_search(search)
            totalhits = self.res.json()['totalEstimatedMatches']
            for countUP in tqdm(range(count, totalhits, count)):
                count += countUP
                print(f'pass {count} of {totalhits}')
                try:
                    search['offset'] = count
                    results = self._get_new_search(search)
                    if self.res.status_code == 429:
                        wait_time = dict(self.res.headers).get('Retry-After')
                        if isinstance(wait_time,int):
                            print(f'API called too often need to wait {wait_time} secs to retry')
                            print(f'sleeping {wait_time} secs to retry')
                            for sleep in tqdm(wait_time):
                                time.sleep(sleep)
                    else:
                        news_search = pd.concat([results,news_search],axis=1)
                        time.sleep(.5)
                except Exception as error:
                    print(error)
            return news_search


