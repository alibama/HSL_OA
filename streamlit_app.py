#this is the entire app - rendered by streamlit at https://share.streamlit.io/carrlucy/hsl_oa/main
#if you're interested editing this tool for your own uses look at the "bigask function" and find the 
#line that reads query = '(AFF:"University of Virginia") AND (FIRST_PDATE:[2017-01-01 TO 2020-12-31])'
#and then edit the AFF (institutional affliation) to suit your needs do some typing

import math
import streamlit as st
import numpy as np
import json
import altair as alt
from urllib.request import urlopen
#from xml.etree.ElementTree import parse
import urllib
import urllib.parse as urlparse
import requests
import pandas as pd
import fuzzywuzzy
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from pandas import json_normalize 
import mkwikidata


#import pandas_profiling
#@st.cache


import codecs
#from pandas_profiling import ProfileReport 

# Components Pkgs
import streamlit.components.v1 as components
#from streamlit_pandas_profiling import st_profile_report

# Custom Component Fxn
import sweetviz as sv 

st.header('Open Data Dashboard using EuropePMC Publication Data')
st.subheader('Exploratory Data Analysis with Streamlit')

st.markdown('In this app, we are using content pulled from [EuropePMC](https://europepmc.org/RestfulWebService) with a simple Python script, gratefully edited by Dr. Maaly Nassar of the EuropePMC publication team, and served via [Streamlit](https://streamlit.io)')

#with st.sidebar.form(key ='Form1'):
#	user_input = st.text_input("Departmental Filter", )
#	submitted1 = st.form_submit_button(label = 'Filter')


query = """
SELECT ?part ?partLabel ?parentOrg ?parentOrgLabel
WHERE 
{
  {?part wdt:P361+ wd:Q34433.}
  union
  {?part wdt:P361/wdt:P749 wd:Q34433.}
  ?part wdt:P361 ?parentOrg.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". } # Helps get the label in your language, if not, then en language
}
order by ?part
"""
query_result = mkwikidata.run_query(query, params={ })  

wikidata = [{"label" : x["partLabel"]["value"], "part" : x["part"]["value"]} for x in query_result["results"]["bindings"]]
wikidf= pd.DataFrame(wikidata).set_index("label")
wikidf.reset_index(inplace=True)
wikidf = wikidf.rename(columns = {'index':'dept'})


wiki_clear=wikidf.drop_duplicates(subset=None, keep='first', inplace=False, ignore_index=False)
wiki_clear = wiki_clear.reset_index(drop=True)
st.write(wiki_clear)

@st.cache(suppress_st_warning=True)
def bigask ():
    dct = {}
    for col in ['oa','author','year','title','doi','cited','aff']:
        dct[col] = []

    cr_mrk= '' #current cursor mark
    nxt_mrk = '*' #next cursor mark
    while cr_mrk != nxt_mrk:              
        url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?'
        query = '(AFF:"University of Virginia") AND (FIRST_PDATE:[2017-01-01 TO 2020-12-31])'
        params = {'query':query, 'resultType':'core', 'synonym':'TRUE','cursorMark':nxt_mrk,'pageSize':'1000','format':'json'}
        response = requests.get(url,params)
        rjson = response.json()
        cr_mrk = urlparse.unquote(rjson['request']['cursorMark'])
        nxt_mrk = urlparse.unquote(rjson['nextCursorMark'])
        for rslt in rjson['resultList']['result']:
            dct['author'].append(rslt['authorString']) if 'authorString' in rslt.keys() else dct['author'].append(0)
            dct['year'].append(rslt['pubYear']) if 'pubYear' in rslt.keys() else dct['year'].append(0)
            dct['title'].append(rslt['title']) if 'title' in rslt.keys() else dct['title'].append(0)
            dct['doi'].append(rslt['doi']) if 'doi' in rslt.keys() else dct['doi'].append(0)
#           dct['id'].append(rslt['id']) if 'id' in rslt.keys() else dct['id'].append(0)
            dct['oa'].append(rslt['isOpenAccess']) if 'isOpenAccess' in rslt.keys() else dct['oa'].append(0)
            dct['cited'].append(rslt['citedByCount']) if 'citedByCount' in rslt.keys() else dct['cited'].append(0) 
            dct['aff'].append(rslt['affiliation']) if 'affiliation' in rslt.keys() else dct['aff'].append(0) 
    df=pd.DataFrame.from_dict(dct, orient='columns')
    return df



# #menu = ["Y", "N"]
# #st.sidebar.subheader("Select Option")
# #choice = st.sidebar.selectbox("Full Text", menu)

dfdata=bigask()
# #dfdata2=bigask2()
# #https://stackoverflow.com/questions/43727583/re-sub-erroring-with-expected-string-or-bytes-like-object

dfdata['aff'] = dfdata['aff'].apply(str)
dfdata['doi'] = dfdata['doi'].astype(str)  #pandas was calling this a mixed type column and it borked sweetviz

dfdatahead = dfdata.head(100)
st.write(dfdatahead)

wiki_clear['label']=wiki_clear['label'].apply(str)
wiki_clear['label']=wiki_clear['label'].astype(str)

list1 = dfdatahead['aff'].tolist()
list2 = wiki_clear['label'].tolist()
threshold = 80

mat1 = []
for i in list1:
     mat1.append(process.extract(i, list2, limit=1))

#df_results = pd.DataFrame(zip(mat1, label), columns=['aff', 'label'])
#dfdatahead['matches'] = mat1

#st.write(mat1)

openFilter = sorted(df['aff'].drop_duplicates()) # select the open access values 
open_Filter = st.sidebar.selectbox('Open Access?', openFilter) # render the streamlit widget on the sidebar of the page using the list we created above for the menu
df2=df[df['openAccess'].str.contains(open_Filter)] # create a dataframe filtered below
st.write(df2.sort_values(by='date'))


@st.cache(suppress_st_warning=True)
def st_display_sweetviz(report_html,width=1000,height=500):
 	report_file = codecs.open(report_html,'r')
 	page = report_file.read()
 	components.html(page,width=width,height=height,scrolling=True)


  
def main():
 	if st.button("Generate Sweetviz Report"):
 		report = sv.analyze(dfdata)
 		report.show_html()
 		st_display_sweetviz("SWEETVIZ_REPORT.html")

# st.subheader('Streamlit makes interactive widgets with minimal code')
    
# '''This is a simple slider built in Streamlit that interacts with the imported data and provides the user with a textual and graphical output.'''
# #citations = st.slider('Number of citations', 0, 100, 1)
# citations = 0
# dfdata = dfdata[dfdata['cited'] >= citations] 
# dfdata['doi'] = dfdata['doi'].astype(str)  #pandas was calling this a mixed type column and it borked sweetviz
# dfdata['aff'] = dfdata['aff'].astype(str)  #pandas was calling this a mixed type column and it borked sweetviz
# #dfdata
# dfdata.to_csv('opendata.csv', index=False)
# st.write(dfdata)
        
# valLayer = alt.Chart(dfdata).mark_bar().encode(x='year',y='count(oa)',color='oa')
# st.altair_chart(valLayer, use_container_width=True)
# st.subheader('EDA reports provide a simple & low-code overview of data')
# '''Exploratory data analysis (EDA) provides a quick overview of a data set, helping to establish the type and quality of the data to be processed. In our example, [Sweetviz](https://pypi.org/project/sweetviz/) applies univariate graphical and textual reports to give data sets a first review. EDA tools can generate a report with only a few lines of code, and are thus especially useful for programmers to deliver to stakeholders early in the process.'''

# if __name__ == '__main__':
#  	main()
	
#https://stackoverflow.com/questions/55961615/how-to-integrate-wikidata-query-in-python
#https://query.wikidata.org/#SELECT%20%3Fpart%20%3FpartLabel%20%3FparentOrg%20%3FparentOrgLabel%0AWHERE%20%0A%7B%0A%20%20%7B%3Fpart%20wdt%3AP361%2B%20wd%3AQ213439.%7D%0A%20%20union%0A%20%20%7B%3Fpart%20wdt%3AP361%2Fwdt%3AP749%20wd%3AQ213439.%7D%0A%20%20%3Fpart%20wdt%3AP361%20%3FparentOrg.%0A%20%20SERVICE%20wikibase%3Alabel%20%7B%20bd%3AserviceParam%20wikibase%3Alanguage%20%22%5BAUTO_LANGUAGE%5D%2Cen%22.%20%7D%20%23%20Helps%20get%20the%20label%20in%20your%20language%2C%20if%20not%2C%20then%20en%20language%0A%7D%0Aorder%20by%20%3FparentOrgLabel




# wikiurl = 'https://query.wikidata.org/sparql'
# wikiquery = '''

# '''
# r = requests.get(wikiurl, params = {'format': 'json', 'query': wikiquery})
# wikidata = r.json()
# #wikidf = pd.read_json(wikidata)
# wikidf = json_normalize(wikidata['results.bindings'])
# st.write(wikidf)

#st.write("This is testing the fuzzywuzzy package to begin aggregating departments")
#st.write(process.extract(user_input, dfdata['aff'].to_list(), limit = 10))
