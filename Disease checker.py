import pickle
import re
import time
import random
import warnings
import requests
from bs4 import BeautifulSoup
from googlesearch import search
import os

warnings.filterwarnings("ignore")


# Step 1: Fetch disease names from the National Health Portal of India
def fetch_diseases_from_nhp():
    base_url = 'https://www.nhp.gov.in/disease-a-z/'
    diseases = []
    for c in 'abcdefghijklmnopqrstuvwxyz':
        url = base_url + c
        try:
            time.sleep(random.uniform(1, 3))  # Random delay to avoid being blocked
            response = requests.get(url, verify=False)
            soup = BeautifulSoup(response.content, 'lxml')  # Switched to faster parser
            disease_div = soup.find('div', class_='all-disease')
            if disease_div:
                for li in disease_div.find_all('li'):
                    diseases.append(li.get_text(strip=True))
        except Exception as e:
            print(f"Error fetching diseases for letter '{c}': {e}")
    return diseases


# Step 2: Load additional disease names from pickle
def load_pickle_diseases(filepath):
    if not os.path.exists(filepath):  # Check if the file exists
        print(f"Error: {filepath} not found.")
        return []
    try:
        with open(filepath, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Error loading pickle file: {e}")
        return []


# Step 3: Search Wikipedia and extract symptoms from infobox
def fetch_symptoms(disease_list):
    dis_symp = {}
    for dis in disease_list:
        query = f"{dis} wikipedia"
        try:
            for result in search(query, tld="com", stop=10, pause=1):  # Adjusted tld and pause
                if "wikipedia" in result:
                    wiki_page = requests.get(result, verify=False)
                    soup = BeautifulSoup(wiki_page.content, 'lxml')
                    info_table = soup.find("table", {"class": "infobox"})
                    if info_table:
                        for row in info_table.find_all("tr"):
                            header = row.find("th", {"scope": "row"})
                            if header and "Symptom" in header.get_text():
                                symptoms_td = row.find("td")
                                if symptoms_td:
                                    symptoms = symptoms_td.get_text(separator=', ', strip=True)
                                    symptoms = re.sub(r'\[.*?\]', '', symptoms)  # Remove references
                                    dis_symp[dis] = symptoms
                                    break
                    if dis in dis_symp:
                        break  # Stop further searches if symptoms found
        except Exception as e:
            print(f"Error fetching symptoms for {dis}: {e}")
    return dis_symp


# Step 4: Remove duplicates based on symptom text
def remove_duplicates(symptom_dict):
    unique_symptoms = set()
    cleaned_dict = {}
    for disease, symptoms in symptom_dict.items():
        normalized_symptoms = ' '.join(symptoms.split())  # Normalize whitespace
        if normalized_symptoms not in unique_symptoms:
            cleaned_dict[disease] = symptoms
            unique_symptoms.add(normalized_symptoms)
        else:
            print(f"Duplicate symptoms found for: {disease}")
    return cleaned_dict


# Main process
if __name__ == "__main__":
    diseases_from_web = fetch_diseases_from_nhp()
    diseases_from_pickle = load_pickle_diseases('list_diseaseNames.pkl')

    combined_diseases = sorted(set(diseases_from_web).union(set(diseases_from_pickle)))

    print(f"Total unique diseases: {len(combined_diseases)}")

    disease_symptoms = fetch_symptoms(combined_diseases)
    final_symptoms = remove_duplicates(disease_symptoms)

    print(f"Diseases with unique symptoms: {len(final_symptoms)}")

    with open('final_dis_symp.pickle', 'wb') as f:
        pickle.dump(final_symptoms, f, protocol=pickle.HIGHEST_PROTOCOL)

