from lxml import etree
import json
import requests
import streamlit as st
import streamlit_ext as ste


st.title('Oversettelser i Nasjonalbibliografien')
st.write('Liste over utgivelser hvor gitt navn er registrert som oversetter')
navn = st.text_input("*Oversetter (Etternavn, Fornavn):*")
xmldoc = '''<modsCollection xmlns="http://www.loc.gov/mods/v3">
'''

SEARCHAPI = 'https://api.nb.no/catalog/v1/items?q=namecreators:{s}&searchType=FIELD_RESTRICTED_SEARCH&filter=bibliography:Norbok&sort=date&size={ant}';
ns = {"mods": "http://www.loc.gov/mods/v3"}

searchurl = SEARCHAPI.format(s=navn, ant=50) if navn else None
n = 0

if searchurl is not None:
    with st.spinner():
        while searchurl is not None:
            searchresp = requests.get(searchurl)
            if not searchresp.ok:
                searchurl = None
            else:
                data_json = json.loads(searchresp.content)
                if "_embedded" in data_json and 'items' in data_json['_embedded']:
                    for rec in data_json['_embedded']['items']:
                        title = rec['metadata']['title']
                        
                        modsurl = rec["_links"]["mods"]["href"]
                        res = requests.get(modsurl)
                        if res.status_code == 200:
                            mods = etree.fromstring(res.content)
                            
                            navnfunn = mods.xpath("mods:name[mods:namePart[contains(text(), '" + navn + "')] and mods:role/mods:roleTerm='trl']",
                                                namespaces=ns)
                            if len(navnfunn) > 0:
                                forfatterlist = mods.xpath("mods:name[not(mods:role/mods:roleTerm='trl')]/mods:namePart/text()", namespaces=ns)
                                forfatter = forfatterlist[0] if len(forfatterlist) > 0 else ""
                                aarlist = mods.xpath("mods:originInfo/mods:dateIssued/text()", namespaces=ns)
                                aar = aarlist[0] if len(aarlist)>0 else ""
                                isbnlist = mods.xpath("mods:identifier[@type='isbn']/text()", namespaces=ns)
                                isbn = "ISBN " + isbnlist[0] if len(isbnlist)>0 else ""
                                st.write('- ',title, ' / ', forfatter, ' ; ', aar, ' ; ', isbn)
                                modstxt = etree.tostring(mods, pretty_print=True, encoding='utf-8')
                                xmldoc += modstxt.decode("utf-8")
                                n += 1
                                #utfil.write(modstxt.decode("utf-8"))
                    
                if '_links' in data_json and "next" in data_json['_links']:
                    searchurl = data_json['_links']['next']['href']
                else:
                    searchurl = None
                
    xmldoc += "</modsCollection>\n";

    st.markdown("""---""")
    if (n > 0):
        ste.download_button('Last ned MODS XML', xmldoc,
                    file_name=navn.replace(' ', '').replace(',', '_') + '.xml')
    else:
        st.write("Beklager, ingen utgivelser funnet.")
        