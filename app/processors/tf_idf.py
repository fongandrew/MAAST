import csv
import re
import math
from operator import itemgetter
import nltk
#from google.appengine.ext import db

"""
class Message(db.Model):
  user_email = db.StringProperty()
  msg_id = db.IntegerProperty()
  keyword = db.StringProperty()
  freq = db.FloatProperty()
"""
    
def tf_idf(message):
  allowed_words = 3
  
  #load stopwords
  stopword_filename = 'stop_words.csv' # all the stopwords are low cases
  reader = csv.reader(open(stopword_filename, "r"), delimiter = ',')
  
  stopwords = []
  for row in reader:
    stopwords = row    
    
  #parse incoming message
  text = nltk.word_tokenize(message) #tokenize sentence
  filtered_text = []
  
  #take out stopwords
  for item in text:
    if item.lower() not in stopwords:
      filtered_text.append(item)
  
  #find nouns
  tagged_words = nltk.pos_tag(filtered_text)
  nouns = []
  for tagged_word in tagged_words:
    if "N" in tagged_word[1]:
      nouns.append(tagged_word[0])
      
  #find frequent nouns
  noun_freq = {}
  for i in set(nouns):
    noun_freq[i] = nouns.count(i)
    
  print noun_freq
#  for word in nouns:
#    words[word] = tf(word,message)
    
#      m = Message()
#      m.user_email = "travis.yoo@gmail.com"
#      m.msg_id = 1
#      m.keyword = item[0]
#      m.freq = item[1]
#      m.put()
#      allowed_words -= 1

"""
def freq(word, document):
  return document.split(None).count(word)

def word_count(document):
  return len(document.split(None))

def numDocsContaining(word,documentList):
  count = 0
  for document in documentList:
    if freq(word,document) > 0:
      count += 1
  return count

def tf(word, document):
  return (freq(word,document) / float(word_count(document)))

def idf(word, documentList):
  return math.log(len(documentList) / float(numDocsContaining(word,documentList)))

def tfidf(word, document, documentList):
  return (tf(word,document) * idf(word,documentList))

"""          

"""
Test
"""
if __name__ == '__main__':
  tf_idf("""
  1 Racediversity-open moderator request(s) waiting
  1 Education-open moderator request(s) waiting
  1 Healthcare-open moderator request(s) waiting
  1 Foreignaffairs-open moderator request(s) waiting
  1 Hba-open moderator request(s) waiting
  1 Est-open moderator request(s) waiting
  1 Immigration-open moderator request(s) waiting
  Immigration-open moderator request check result
  Inbox for Andrew Fong (3)
  Re: SF for Obama Volunteers data entry summary!
  CaliforniaCAN Digest, April 9th
  USACAN Digest, April 9th
  [PingMe] Run...
  [PingMe] Morning Vitamins...
  [PingMe] Louder ringtone for dad...
  Your team has won!
  [ycfounders] Re: Recruiter Recommendation
  [dfa-78] Re: Did You Get the News?
  [dfa-78] Did You Get the News?
  [ycfounders] Re: Recruiter Recommendation
  [ycfounders] Re: Recruiter Recommendation
  [ycfounders] Re: Recruiter Recommendation
  [ycfounders] Recruiter Recommendation
  [PingMe] Evening Vitamins...
  Tara Schubert invited you to the event "Call for Change: Help Indiana Obama Supporters Mobilize for ...
  Warfish.net Your Turn Still In-Progress
  """)