import requests 
  
# defining the api-endpoint  
API_ENDPOINT = "https://www.twinword.com/api/v6/text/classify/"

body="""After a great deal of input from a large group of people what I hope is the 
almost final draft of the 2000 Tech Services is attached below.
Please take a look at them.
I will be at the Operations Directors Meeting next week to go over them.
For the Tech Service Teams you may find some of these which are appropriate 
to use in your Teams and Individual objectives.
If you have any questions please let me know.
Thanks
Rick Cates                                                         
"""  
subject=""
# your source code here 
source_code = ''' 
print("Hello, world!") 
a = 1 
b = 2 
print(a + b) 
'''
  
# data to be sent to api 
#data = {'api_dev_key':API_KEY, 
#        'api_option':'paste', 
 #       'api_paste_code':source_code, 
  #      'api_paste_format':'python'} 
 
data={'text':body,
 		'title':subject }

# sending post request and saving response as response object 
r = requests.post(url = API_ENDPOINT, data = data) 
  
# extracting response text  
data = r.json()


print(data['keywords'])