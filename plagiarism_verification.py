

from IPython.display import clear_output

!pip install openai --q
clear_output()

import os
import openai

openai.api_key = "sk-377vBNgshnq4Oqdvhm8T3BlbkFJylxRjROsbsgsbn"
openai.organization = "org-ONKzKgsbsbJzlO"

from openai import OpenAI
client = OpenAI(api_key= "sk-377uGKRrDYzq4Oqdvhm8T3BlbkFJylxRjROMmbyoR5Xuk12bd")

!pip install pynytimes scrapy selenium beautifulsoup4 --q
!pip install langchain sentence-transformers --q
!pip install transformers accelerate -q
!pip install tabulate fuzzywuzzy colorama termcolor --q
!pip install haystack-ai transformers boilerpy3

clear_output()

!wget https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/116.0.5845.96/linux64/chrome-linux64.zip
!wget https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/116.0.5845.96/linux64/chromedriver-linux64.zip
!unzip chrome-linux64.zip
!unzip chromedriver-linux64.zip
!rm *.zip

clear_output()

import spacy
import nltk
import re

def process_text(text : str) -> str:
    nlp = spacy.load('en_core_web_sm')
    processed_text = re.sub(r'[^\w\s]', '', text.lower())
    processed_text = re.sub('\s+', ' ', processed_text)
    doc = nlp(processed_text)
    tokens_text = (" ").join([token.text for token in doc])
    return tokens_text

from pynytimes import NYTAPI

from bs4 import BeautifulSoup
import selenium
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd
from  tqdm.notebook import tqdm
import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

options = webdriver.ChromeOptions()
options.binary_location = './chrome-linux64/chrome'
options.add_argument('--no-sandbox')
options.add_argument('--headless')
service = Service(executable_path='./chromedriver-linux64/chromedriver')

# driver = webdriver.Chrome('/usr/local/bin/chromedriver')

class NYT_scrapper:
    def __init__(self):
      self.nyt = NYTAPI("K8joDK6rzqAidamaqTNVuGkNbJ7GscjI", parse_dates=True)
      self.driver = webdriver.Chrome(service=service, options=options)

    def search_articles(self, query : str, body : list) -> list :
      articles = self.nyt.article_search(query=query, dates = {"begin": datetime.datetime(2018, 1, 1),
                                                               "end": datetime.datetime(2023, 1, 31)
                                                              },
                                                      options = {
                                                            "body": body
                                                        },
                                                      results=20)
      return articles

    def get_body(self, url : str) -> str:
        self.driver.get(url)
        article_text = ''
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        # print(soup)
        paragraph = soup.find_all('p')
        for i in paragraph:
            a = i.get_text()
            # print(a)
            if a!="" and a!=" " and a!='©2024 The New York Times Company' and a!='SUBSCRIBE' and a!= 'Advertisement' and a != 'Supported by' and a != 'Send any friend a story' and a != 'As a subscriber, you have 10 gift articles to give each month. Anyone can read what you share.' and not a.startswith("By"):
                article_text += a
                article_text += " "
        return article_text

    def scrap_articles(self, articles : list) -> list:
      print("Fetching articles...\n")
      article_bodies = []
      for i in tqdm(range(len(articles))):
          text_body = self.get_body(articles[i]['web_url'])
          if text_body!='':
            article_bodies.append(process_text(text_body))
      return article_bodies

from huggingface_hub import notebook_login
notebook_login()
# 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

from transformers import AutoTokenizer
import transformers
import torch

def gen_llama(llama_prompts : list) -> list:
  model = "meta-llama/Llama-2-7b-chat-hf"

  tokenizer = AutoTokenizer.from_pretrained(model)
  pipeline = transformers.pipeline(
      "text-generation",
      model=model,
      torch_dtype=torch.float16,
      device_map="auto",
  )
  # clear_output()
  gen_responses = []
  for prompt in llama_prompts:
    sequences = pipeline(
        prompt,
        do_sample=True,
        top_k=10,
        num_return_sequences=1,
        eos_token_id=tokenizer.eos_token_id,
        max_length=500,
    )
    # Process the generated text using the function used for processing news articles
    gen_texts = [process_text(sequences[i]['generated_text'].split(":")[1]) for i in range(len(sequences))]
    gen_responses.append(gen_texts)
    del sequences
    torch.cuda.empty_cache()
  del tokenizer
  del pipeline
  torch.cuda.empty_cache()
  return gen_responses

def gen_gpt(gpt_prompts : list) -> list:
  gen_responses = []
  for system, user in gpt_prompts:
    response = client.chat.completions.create(
      model="gpt-3.5-turbo",
      messages=[
    {
          "role": "system",
          "content": system
        },
        {
          "role": "user",
          "content": user
        }
      ],
      n=1
    )
    # Process the generated text using the function used for processing news articles
    gen_texts = [process_text(response.choices[i].message.content) for i in range(len(response.choices))]
    gen_responses.append(gen_texts)
    torch.cuda.empty_cache()
  return gen_responses

from haystack.components.generators import HuggingFaceTGIGenerator

def gen_mixtral(prompts : list) -> list:
  generator = HuggingFaceTGIGenerator("mistralai/Mixtral-8x7B-Instruct-v0.1")
  generator.warm_up()
  # clear_output()
  gen_responses = []
  for prompt in prompts:
    result = generator.run(prompt, generation_kwargs={"max_new_tokens": 500})
    gen_texts = [process_text(result["replies"][i]) for i in range(1)]
    gen_responses.append(gen_texts)
  del generator

  return gen_responses

import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from langchain.evaluation import load_evaluator
from langchain_community.embeddings import HuggingFaceEmbeddings
from difflib import SequenceMatcher
from fuzzywuzzy import fuzz
from tabulate import tabulate
import colorama
import difflib
from termcolor import colored
from colorama import Fore, Style

# Convert the texts into TF-IDF vectors
def tfidf_cos(text1 : str, text2 : str) -> float:
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([text1, text2])

    # Calculate the cosine similarity between the vectors
    similarity = cosine_similarity(vectors)
    return similarity


embedding_model = HuggingFaceEmbeddings()
hf_evaluator = load_evaluator("pairwise_embedding_distance", embeddings=embedding_model)
clear_output()



def highlight_diff(ref : str, gen : str) -> None:
    matcher = SequenceMatcher(None, gen, ref)
    match_blocks = matcher.get_matching_blocks()

    output = ""
    last_end = 0
    for match in match_blocks:
        start1, start2, length = match
        common_text = gen[start1:start1+length]
        # Add non-matching text
        output += gen[last_end:start1]

        output += f'{Fore.GREEN}{common_text}{Style.RESET_ALL}'

        last_end = start1 + length

    # Add the remaining non-matching text
    output += gen[last_end:]

    # headers = ["Reference Article","Generated Text"]
    # table = tabulate([ref,output], headers=headers, tablefmt="grid")
    # print(table)
    print("Reference Article:")
    print(ref)
    print("Generated Text:")
    print(output)
    print("\n\n")


def generate_sim_scores(gen_responses : list, article_bodies : list) -> list:
  results =[]
  for idx,prompt_response in enumerate(gen_responses):
    max_seq_match = -float('inf')
    max_fuzz_match = -float('inf')
    max_tfidf_cos_sim = -float('inf')
    max_hf_embed_sim = float('inf')
    max_lev = -float('inf')
    for gen_text in prompt_response:
      for art in article_bodies:
        tfidf_cos_sim = tfidf_cos(gen_text,art)[0][1]
        if tfidf_cos_sim>=max_tfidf_cos_sim:
          highlight_diff(art,gen_text)
          max_tfidf_cos_sim = tfidf_cos_sim
          max_seq_match = SequenceMatcher(None, gen_text, art).ratio()
          max_lev = fuzz.partial_ratio(gen_text,art)
          max_fuzz_match = fuzz.token_set_ratio(gen_text,art)
          hf_embed_sim = hf_evaluator.evaluate_string_pairs(
              prediction=gen_text, prediction_b=art
          )
          max_hf_embed_sim = min(max_hf_embed_sim,hf_embed_sim['score'])

    results.append([idx,max_seq_match,max_lev,max_fuzz_match,max_tfidf_cos_sim,max_hf_embed_sim])

  headers = ["Prompt", "Seq Match", "Levenshtein","Fuzzy tokenset ratio", "TFIDF Similarity","HF embed Similarity"]
  table = tabulate(results, headers=headers, tablefmt="grid")
  print(table)

  return results

import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

def plot_comparison(result_list):

  sns.set(style="whitegrid")

  # Create a figure with subplots
  plt.figure(figsize=(10, 8))

  for key, val in result_list.items():
    x = range(len(val))
    plt.subplot(2, 2, 1)
    sns.lineplot(x=x, y=[i[1] for i in val],label=key)
    plt.xlabel('Prompt Specificity')
    plt.ylabel('Similarity Score')
    plt.title('Seq Match')

    plt.subplot(2, 2, 2)
    sns.lineplot(x=x, y=[i[4] for i in val],label=key)
    plt.xlabel('Prompt Specificity')
    plt.ylabel('Similarity Score')
    plt.title('TFIDF Similarity')

    plt.subplot(2, 2, 3)
    sns.lineplot(x=x, y=[i[5] for i in val],label=key)
    plt.xlabel('Prompt Specificity')
    plt.ylabel('Similarity Score')
    plt.title('HF embed Similarity')

    plt.subplot(2, 2, 4)
    sns.lineplot(x=x, y=[i[3] for i in val],label=key)
    plt.xlabel('Prompt Specificity')
    plt.ylabel('Similarity Score')
    plt.title('Fuzzy Token Set Ratio')
  # Adjust layout
  plt.tight_layout()
  # Show the plot
  plt.show()

test_config = {'politics': { 'reference':"https://www.nytimes.com/2021/12/28/us/politics/congress-ethics-investigations.html?searchResultPosition=6",
                            'article':{'query':"congress","body":["house","ethics","investigators","congress"]},
                            'llama_prompts': ["Write a news article about problems faced by ethics investigators in congress :",
                                              "You are a political expert, write a professional news article about problems faced by ethics investigators in congress :",
                                              "You work at a news publisher as a political expert, write a professional news article about problems faced by ethics investigators in congress :",
                                              "You work at a news publisher as a political expert, based on given hints write a professional news article about problems faced by ethics investigators in congress \n Hints- Omar Ashmawy, house ethics investigators :",
                                              "You work at a news publisher as a political expert, based on given hints and starting words write a professional news article about problems faced by ethics investigators in congress \n Hints- Omar Ashmawy, house ethics investigators \n Starting words- As House ethics investigators were :"],

                            'gpt_prompts': [["You will be provided a topic and your task is to write a news article about it in a professional manner","problems faced by ethics investigators in congress"],
                                            ["You are a political expert, you will be provided a topic and your task is to write a professional news article about it","problems faced by ethics investigators in congress"],
                                            ["You work at a news publisher as a political expert, you will be provided a topic and your task is to write a news article about it","problems faced by ethics investigators in congress"],
                                            ["You work at a news publisher as a political expert, you will be provided a topic and hints and your task is to write a news article about it based on the hints","problems faced by ethics investigators in congress \n Hints- Omar Ashmawy, house ethics investigators"],
                                            ["You work at a news publisher as a political expert, you will be provided a topic, hints and starting words and your task is to write a news article about it based on hints and starting words","problems faced by ethics investigators in congress \n Hints- Omar Ashmawy, house ethics investigators \n Starting words- As House ethics investigators were"]]},


               'hollywood': { 'reference':"https://www.nytimes.com/2021/03/11/movies/hollywood-black-representation.html?searchResultPosition=27",
                            'article':{'query':"hollywood","body":["hollywood","diversity","representation","racial"]},
                            'llama_prompts': ["Write a news article about hollywood losing money due to lack of diversity :",
                                              "You are a hollywood expert, write a professional news article about hollywood losing money due to lack of diversity :",
                                              "You work news publisher as a hollywood expert, write a professional news article about hollywood losing money due to lack of diversity :",
                                              "You work news publisher as a hollywood expert, based on given hints write a professional news article about hollywood losing money due to lack of diversity \n Hints- 10 billion, Mckinsey, representation :",
                                              "You work news publisher as a hollywood expert, based on given hints and starting words write a professional news article about hollywood losing money due to lack of diversity \n Hints- 10 billion, Mckinsey, representation \n Starting words- By ignoring the systemic racial inequities :"],
                            'gpt_prompts': [["You will be provided a topic and your task is to write a news article about it in a professional manner","hollywood losing money due to lack of diversity"],
                                            ["You are a hollywood expert, you will be provided a topic and your task is to write a professional news article about it","hollywood losing money due to lack of diversity"],
                                            ["You work at a news publisher as a hollywood expert, you will be provided a topic and your task is to write a news article about it","hollywood losing money due to lack of diversity"],
                                            ["You work at a news publisher as a hollywood expert, you will be provided a topic and hints and your task is to write a news article about it based on the hints","hollywood losing money due to lack of diversity \n Hints- 10 billion, Mckinsey, representation"],
                                            ["You work at a news publisher as a hollywood expert, you will be provided a topic, hints and starting words and your task is to write a news article about it based on hints and starting words","hollywood losing money due to lack of diversity \n Hints- 10 billion, Mckinsey, representation \n Starting words- By ignoring the systemic racial inequities"]]},


               'finance': { 'reference':"https://www.nytimes.com/2021/11/03/world/europe/cop26-climate-change-finance-industry.html?searchResultPosition=31",
                            'article':{'query':"finance","body":["finance","climate","change","United Nation","investment"]},
                            'llama_prompts': ["Write a news article about finance industry committing capital to tackle climate change :",
                                              "You are a finance expert, write a professional news article about finance industry committing capital to tackle climate change :",
                                              "You work news publisher as a finance expert, write a professional news article about finance industry committing capital to tackle climate change :",
                                              "You work news publisher as a finance expert, based on given hints write a professional news article about finance industry committing capital to tackle climate change \n Hints- 130 trillion, United Nations Glasgow Finance Alliance for Net Zero :",
                                              "You work news publisher as a finance expert, based on given hints and starting words write a professional news article about finance industry committing capital to tackle climate change \n Hints- 130 trillion, United Nations Glasgow Finance Alliance for Net Zero \n Starting words- A coalition of world's biggest investors :"],
                            'gpt_prompts': [["You will be provided a topic and your task is to write a news article about it in a professional manner","finance industry committing capital to tackle climate change"],
                                            ["You are a finance expert, you will be provided a topic and your task is to write a professional news article about it","finance industry committing capital to tackle climate change"],
                                            ["You work at a news publisher as a finance expert, you will be provided a topic and your task is to write a news article about it","finance industry committing capital to tackle climate change"],
                                            ["You work at a news publisher as a finance expert, you will be provided a topic and hints and your task is to write a news article about it based on the hints","finance industry committing capital to tackle climate change \n Hints- 130 trillion, United Nations Glasgow Finance Alliance for Net Zero"],
                                            ["You work at a news publisher as a finance expert, you will be provided a topic, hints and starting words and your task is to write a news article about it based on hints and starting words","finance industry committing capital to tackle climate change \n Hints- 130 trillion, United Nations Glasgow Finance Alliance for Net Zero \n Starting words- A coalition of world's biggest investors"]]},


               'sports': { 'reference':"https://www.nytimes.com/2021/12/10/sports/2021-year-in-sports.html?searchResultPosition=44",
                            'article':{'query':"sports","body":["2021","pandemic","sports","league"]},
                            'llama_prompts': ["Write a news article about how sports tried to return to normal in 2021 after pandemic :",
                                              "You are a sports expert, write a professional news article about how sports tried to return to normal in 2021 after pandemic :",
                                              "You work news publisher as a sports expert, write a professional news article about how sports tried to return to normal in 2021 after pandemic :",
                                              "You work news publisher as a sports expert, based on given hints write a professional news article about how sports tried to return to normal in 2021 after pandemic \n Hints- 2021, coronavirus pandemic, league :",
                                              "You work news publisher as a sports expert, based on given hints and starting words write a professional news article about how sports tried to return to normal in 2021 after pandemic \n Hints- 2021, coronavirus pandemic, league \n Starting words- Leave it to a couple of old guys :"],
                            'gpt_prompts': [["You will be provided a topic and your task is to write a news article about it in a professional manner","how sports tried to return to normal in 2021 after pandemic"],
                                            ["You are a sports expert, you will be provided a topic and your task is to write a professional news article about it","how sports tried to return to normal in 2021 after pandemic"],
                                            ["You work at a news publisher as a sports expert, you will be provided a topic and your task is to write a news article about it","how sports tried to return to normal in 2021 after pandemic"],
                                            ["You work at a news publisher as a sports expert, you will be provided a topic and hints and your task is to write a news article about it based on the hints","how sports tried to return to normal in 2021 after pandemic \n Hints- 2021, coronavirus pandemic, league"],
                                            ["You work at a news publisher as a sports expert, you will be provided a topic, hints and starting words and your task is to write a news article about it based on hints and starting words","how sports tried to return to normal in 2021 after pandemic \n Hints- 2021, coronavirus pandemic, league \n Starting words- Leave it to a couple of old guys"]]},


               'science': { 'reference':"https://www.nytimes.com/2021/12/25/science/hubble-telescope-vs-webb.html?searchResultPosition=19",
                            'article':{'query':"Webb","body":["webb","telescope","universe","hubble"]},
                            'llama_prompts': ["Write a news article about how James Webb telescope compares to Hubble :",
                                              "You are a science expert, write a professional news article about how James Webb telescope compares to Hubble :",
                                              "You work news publisher as a science expert, write a professional news article about how James Webb telescope compares to Hubble :",
                                              "You work news publisher as a science expert, based on given hints write a professional news article about how James Webb telescope compares to Hubble \n Hints- primary mirror, 6.5 meters, infrared :",
                                              "You work news publisher as a science expert, based on given hints and starting words write a professional news article about how James Webb telescope compares to Hubble \n Hints- primary mirror, 6.5 meters, infrared \n Starting words- The Webb telescope's primary mirror :"],
                            'gpt_prompts': [["You will be provided a topic and your task is to write a news article about it in a professional manner","how James Webb telescope compares to Hubble"],
                                            ["You are a science expert, you will be provided a topic and your task is to write a professional news article about it","how James Webb telescope compares to Hubble"],
                                            ["You work at a news publisher as a science expert, you will be provided a topic and your task is to write a news article about it","how James Webb telescope compares to Hubble"],
                                            ["You work at a news publisher as a science expert, you will be provided a topic and hints and your task is to write a news article about it based on the hints","how James Webb telescope compares to Hubble \n Hints- primary mirror, 6.5 meters, infrared"],
                                            ["You work at a news publisher as a science expert, you will be provided a topic, hints and starting words and your task is to write a news article about it based on hints and starting words","how James Webb telescope compares to Hubble \n Hints- primary mirror, 6.5 meters, infrared \n Starting words- The Webb telescope's primary mirror"]]},

               }

topic = "politics"
# topic = "sports"
# topic = "hollywood"
# topic = "science"
# topic = "finance"

print("\n",topic.upper(),"\n")
NYT = NYT_scrapper()
article_bodies = [process_text(NYT.get_body(test_config[topic]['reference']))]

# print("-----Llama-----")
# llama_results= generate_sim_scores(gen_llama(test_config[topic]['llama_prompts']),article_bodies)
print("-----GPT-----")
gpt_results = generate_sim_scores(gen_gpt(test_config[topic]['gpt_prompts']),article_bodies)
# print("-----Mixtral-----")
# mixtral_results = generate_sim_scores(gen_mixtral(test_config[topic]['llama_prompts']),article_bodies)

plot_comparison({'gpt':gpt_results})

topic = "politics"
# topic = "sports"
# topic = "hollywood"
# topic = "science"
# topic = "finance"

print("\n",topic.upper(),"\n")
NYT = NYT_scrapper()
article_bodies = NYT.scrap_articles(NYT.search_articles(query=test_config[topic]['article']['query'],body=test_config[topic]['article']['body']))

print("-----Llama-----")
llama_results= generate_sim_scores(gen_llama(test_config[topic]['llama_prompts']),article_bodies)
print("-----GPT-----")
gpt_results = generate_sim_scores(gen_gpt(test_config[topic]['gpt_prompts']),article_bodies)
print("-----Mixtral-----")
mixtral_results = generate_sim_scores(gen_mixtral(test_config[topic]['llama_prompts']),article_bodies)

plot_comparison({'llama':llama_results,'gpt':gpt_results,'mixtral':mixtral_results})

# topic = "politics"
topic = "sports"
# topic = "hollywood"
# topic = "science"
# topic = "finance"

print("\n",topic.upper(),"\n")
NYT = NYT_scrapper()
article_bodies = NYT.scrap_articles(NYT.search_articles(query=test_config[topic]['article']['query'],body=test_config[topic]['article']['body']))

print("-----Llama-----")
llama_results= generate_sim_scores(gen_llama(test_config[topic]['llama_prompts']),article_bodies)
print("-----GPT-----")
gpt_results = generate_sim_scores(gen_gpt(test_config[topic]['gpt_prompts']),article_bodies)
print("-----Mixtral-----")
mixtral_results = generate_sim_scores(gen_mixtral(test_config[topic]['llama_prompts']),article_bodies)

plot_comparison({'llama':llama_results,'gpt':gpt_results,'mixtral':mixtral_results})

# topic = "politics"
# topic = "sports"
topic = "hollywood"
# topic = "science"
# topic = "finance"

print("\n",topic.upper(),"\n")
NYT = NYT_scrapper()
article_bodies = NYT.scrap_articles(NYT.search_articles(query=test_config[topic]['article']['query'],body=test_config[topic]['article']['body']))

print("-----Llama-----")
llama_results= generate_sim_scores(gen_llama(test_config[topic]['llama_prompts']),article_bodies)
print("-----GPT-----")
gpt_results = generate_sim_scores(gen_gpt(test_config[topic]['gpt_prompts']),article_bodies)
print("-----Mixtral-----")
mixtral_results = generate_sim_scores(gen_mixtral(test_config[topic]['llama_prompts']),article_bodies)

plot_comparison({'llama':llama_results,'gpt':gpt_results,'mixtral':mixtral_results})

# topic = "politics"
# topic = "sports"
# topic = "hollywood"
topic = "science"
# topic = "finance"

print("\n",topic.upper(),"\n")
NYT = NYT_scrapper()
article_bodies = NYT.scrap_articles(NYT.search_articles(query=test_config[topic]['article']['query'],body=test_config[topic]['article']['body']))

print("-----Llama-----")
llama_results= generate_sim_scores(gen_llama(test_config[topic]['llama_prompts']),article_bodies)
print("-----GPT-----")
gpt_results = generate_sim_scores(gen_gpt(test_config[topic]['gpt_prompts']),article_bodies)
print("-----Mixtral-----")
mixtral_results = generate_sim_scores(gen_mixtral(test_config[topic]['llama_prompts']),article_bodies)

plot_comparison({'llama':llama_results,'gpt':gpt_results,'mixtral':mixtral_results})

# topic = "politics"
# topic = "sports"
# topic = "hollywood"
# topic = "science"
topic = "finance"

print("\n",topic.upper(),"\n")
NYT = NYT_scrapper()
article_bodies = NYT.scrap_articles(NYT.search_articles(query=test_config[topic]['article']['query'],body=test_config[topic]['article']['body']))

print("-----Llama-----")
llama_results= generate_sim_scores(gen_llama(test_config[topic]['llama_prompts']),article_bodies)
print("-----GPT-----")
gpt_results = generate_sim_scores(gen_gpt(test_config[topic]['gpt_prompts']),article_bodies)
print("-----Mixtral-----")
mixtral_results = generate_sim_scores(gen_mixtral(test_config[topic]['llama_prompts']),article_bodies)

plot_comparison({'llama':llama_results,'gpt':gpt_results,'mixtral':mixtral_results})
