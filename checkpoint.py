import requests
import json
from bs4 import BeautifulSoup
import time

CACHE_FILENAME = "cache.json"
PUBCHEM_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
PROPERTIES = "/property/MolecularFormula,MolecularWeight,IsomericSMILES,XLogP,TPSA,HBondDonorCount,HBondAcceptorCount,RotatableBondCount/JSON"
PRESCRIBE_URL = "https://rxnav.nlm.nih.gov/REST/Prescribe/rxcui"
RXCLASS_URL = "https://rxnav.nlm.nih.gov/REST/rxclass/class/byRxcui.json?rxcui="
END_RXCLASS_URL = "&relaSource=MEDRT&relas=may_treat+has_MoA"
SIDE_EFFECT_URL = "https://www.drugs.com"

def open_cache() :
    ''' opens cache file if it exists and loads the JSON
    into the FIB_CACHE dictionary.

    if the cache file doesn't exist, creates new cache dictionary.

    Parameters
    ----------
    None

    Returns
    -------
    cache : dict or json
    '''

    try :
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except :
        cache_dict ={}
    
    return cache_dict


def save_cache(cache_dict) :
    ''' saves the current state of cache to disk.

    Parameters
    ----------
    cache_dict : dict
        dictionary to save

    Returns
    -------
    None
    '''

    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME, "w")
    fw.write(dumped_json_cache)
    fw.close()
    

def make_request(url) :
    ''' Makes a request to the Web API using the url.

    Parameters
    ----------
    url : string
        query url

    Returns
    -------
    result : dict
        json object as a result of API query
    '''

    response = requests.get(url)
    result = json.loads(response.text)

    return result


def make_request_with_cache(url) :
    ''' Checks cache for saved result for a certain drug molecule.
    If result found, returns that. Otherwise sends a new request, 
    saves it and returns it.

    Parameters
    ----------
    url : str
        API query for both pubchem and RxNorm API.
    
    Returns
    -------
    result : dict
        search result either from request or cache.
    '''

    if url in CACHE_DICT.keys():
        print("using cache...", url)
        return CACHE_DICT[url]

    else:
        print("making request...", url)
        if "www.drugs.com" not in url :
            CACHE_DICT[url] = make_request(url)
        else :
            response= requests.get(url)
            CACHE_DICT[url] = response.text
            save_cache(CACHE_DICT)
        return CACHE_DICT[url]


def get_physical_properties(ingredient):
    ''' retrieves the physical properties of the ingredient from PUBCHEM.

    Parameters
    ----------
    ingredient : string
        name of the ingredient

    Returns
    -------
    properties : dictionary
        important properties for drug compounds
    '''

    url = PUBCHEM_URL + ingredient + PROPERTIES
    result = make_request_with_cache(url)
    properties = result["PropertyTable"]["Properties"][0]
    
    return properties


def get_molecular_picture(ingredient) :
    ''' retrieves the 3d picture of the ingredient from PUBCHEM.

    Parameters
    ----------
    ingredient : string
        name of the ingredient

    Returns
    -------
    pic_url : string
        url of image source
    '''

    pic_url = PUBCHEM_URL + ingredient + "/PNG"

    return pic_url


def get_rxcui(ingredient):
    ''' retrieves the rxcui id of an ingredient from Prescribe API.
    
    Parameters
    ----------
    ingredient : string
        name of an active ingredient
    
    Returns
    -------
    rxcui : string
        rxcui id of the active ingredient
    '''

    url = PRESCRIBE_URL + f".json?name={ingredient}"
    try :
        result = make_request_with_cache(url)
        rxcui = result["idGroup"]["rxnormId"][0]
        return rxcui
    except : 
        print(f"{ingredient} does not exist on the National Library of Medicine database")
        return None


def get_products(rxcui):
    ''' gets up to 5 prescribable generic products.

    Parameters
    ----------
    rxcui : string
        rxcui id of an active ingredient
    
    Returns
    -------
    product_dict : dictionary
        brand name : ingredients and their strength
    '''

    url = PRESCRIBE_URL + f"/{rxcui}/allrelated.json"
    result = make_request_with_cache(url)
    result_list = result["allRelatedGroup"]["conceptGroup"]
    product_dict = {}

    for dicts in result_list:
        if dicts["tty"] in ["SBD", "SBDC", "SBDF"]:
            try :
                products = dicts["conceptProperties"]
            except : 
                return {}
            if len(product_dict.keys()) < 5:
            # format of products[i]["name"]: 100 ML Acetaminophen 10 MG/ML Injection [Ofirmev]
                for product in products:
                    brand_name = product["name"].split('[')[-1][:-1]
                    if brand_name not in list(product_dict.keys()):
                        product_form = product["name"].split('[')[0]
                        product_dict.update({brand_name: product_form})
    return product_dict
                

def get_howandwhat(rxcui):
    ''' gets for what symptom the ingredient is effective for by what mechanism.

    Parameters
    ----------
    rxcui : string
        rxcui id of an active ingredient

    Returns
    -------
    howandwhat : list of tuples
        {"symptoms" : [(symptom, symptom_class)], "mechanisms": [mech]}
    '''

    url = RXCLASS_URL + rxcui + END_RXCLASS_URL
    result = make_request_with_cache(url)
    try :
        effects = result["rxclassDrugInfoList"]["rxclassDrugInfo"]
        symptoms = []
        mechanisms = []

        for effect in effects:
            if effect["rela"] == "may_treat":
                symptom = effect["rxclassMinConceptItem"]["className"]
                reason = effect["rxclassMinConceptItem"]["classType"]
                if (symptom, reason) not in symptoms:
                    symptoms.append((symptom, reason))
            elif effect["rela"] == "has_moa":
                mech = effect["rxclassMinConceptItem"]["className"]
                if mech not in mechanisms:
                    mechanisms.append(mech)
        howandwhat = {"symptoms": symptoms, "mechanisms": mechanisms}
        return howandwhat
    except :
        return {}


def get_warning_pages() : 
    ''' Crawls within drugs.com's side effect section and collects
    the url's to popular inquiries for each starting alphabet.

    Parameters
    ----------
    None

    Returns
    -------
    drug_pages : list
        list of urls (portion after SIDE_DEFFECT_URL)
    '''

    response = requests.get(SIDE_EFFECT_URL+'/sfx')
    soup = BeautifulSoup(response.text, 'html.parser')

    parent_links = []
    drug_pages = []

    grandparents = soup.find_all('div', class_='column-split col-list-az')
    for grandparent in grandparents : 
        parent_paths = grandparent.find_all('a')
        for path in parent_paths :
            parent_path = path['href']
            list_parent = SIDE_EFFECT_URL + parent_path
            parent_links.append(list_parent)

    for link in parent_links:
        if '0' in link :
            response2 = requests.get(link)
            soup2 = BeautifulSoup(response2.text, 'html.parser')
            parent = soup2.find('div', class_='boxList')
            if parent == None : break
            child = parent.find('ul', class_='ddc-list-column-3')
            parent_list_items = child.find_all('li')
            for list_item in parent_list_items:
                drug_page = list_item.find('a')['href']
                drug_pages.append(drug_page)
    print(drug_pages)
    return drug_pages


def get_warnings(drug_pages) :
    ''' Scrapes through the list of pages to collect critical consumer warnings.

    Parameters
    ----------
    drug_pages : list
        list of urls

    Returns
    -------
    drug_warnings : dict
        dictionary that maps drugs to corresponding warning (list of string)
    '''

    drug_warnings = {}

    for drug in drug_pages[0:5] :
        url = SIDE_EFFECT_URL + drug
        sfx_drug_name = drug.split('-')[0]
        drug_name = sfx_drug_name.split('/')[-1]
        response = make_request_with_cache(url)
        soup = BeautifulSoup(response, 'html.parser')
        try :
            parent = soup.find('div', class_='blackboxWarning')
            warning_content = parent.find_all('p')
            drug_warnings.update({drug_name: warning_content})
        except :
            print("There is no warning for this drug")
            drug_warnings.update({drug_name: None})

    return drug_warnings


def get_new_warning(drug_name) : 
    ''' Returns consuming warning of drug not in cache.

    Parameters
    ----------
    drug_name : string

    Returns
    -------
    warnings : dict
    '''

    url = SIDE_EFFECT_URL + "/sfx/" + f"{drug_name}-side-effects.html"
    response = make_request_with_cache(url)
    soup = BeautifulSoup(response, 'html.parser')
    warnings = []
    try:
        parent = soup.find('div', class_='blackboxWarning')
        warning_content = parent.find_all('p')
        for warning in warning_content :
            warnings.append(warning.get_text())
        return warnings
    except:
        return None
        

CACHE_DICT = open_cache()

if __name__ == '__main__':
    comp = "sodium tetradecyl sulfate"
    properties = get_physical_properties(comp)
    rxcui = get_rxcui(comp)
    if rxcui != None :
        product_list = get_products(rxcui)
        howandwhat = get_howandwhat(rxcui)
        print(product_list)
        print(howandwhat)

    pages = get_warning_pages()
    warnings = get_warnings(pages)

