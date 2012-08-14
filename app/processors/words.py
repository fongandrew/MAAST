"""
Processor to count occurrences of particular words in the subject line

TODO?
# TF-IDF vs. others

"""
from fetching.meta import MessageProcessor
from fetching.contacts import ContactProcessor
from helpers.nested_dict import pincr, aggregate_dicts
import settings
import os
import re

# Get stop words
stop_name_file = os.path.join(
    os.path.dirname(__file__),
    'stop_words.csv')
f = open(stop_name_file)
STOP_WORDS = f.read().split(',')

# RegEx to parse subject lines
LISTSERV_RE = re.compile(r'\[[^\]]+?\]\s*(.+)')

def tokenize(phrase):
    """
    Iterates through a phrase and yields words
    
    >>> phrase = ("We're ten thousand miles apart. I've been "
    ...           "California-wishing on these stars so hard, "
    ...           "my California dream, my California king.")
    >>> for w in tokenize(phrase): print w
    we're
    ten
    thousand
    miles
    apart
    i've
    been
    california-wishing
    on
    these
    stars
    so
    hard
    my
    california
    dream
    my
    california
    king
    
    """
    phrase = phrase.lower()
    current_word = []
    for l in phrase:
        if not l in "abcdefghijklmnopqrstuvwxyz1234567890`\'-":
            if current_word:
                yield ''.join(current_word)
                current_word = []
        else:
            current_word.append(l)
    if current_word:
        yield ''.join(current_word)


class CountWordsProcessor(MessageProcessor):
    """
    Counts words in subject line, records both total and by year
    """
    def __init__(self, *args, **kwds):
        self.counts = {}
        self.contact_counts = {}
        super(CountWordsProcessor, self).__init__(*args, **kwds)
    
    def process(self, msg, extras={}):
        subject = msg.subject
        if not subject:
            return
        
        # Remove [Group-Name] prefixes
        match = LISTSERV_RE.match(subject)
        if match:
            subject = match.group(1)
        
        # Get contacts
        contacts = []
        if extras.get('from_user'):
            contacts = [person.email
                        for person in (extras['other_to'] + 
                                       extras['other_cc'])]
        elif extras['from_person']:
            contacts = [extras['from_person'].email]
        
         # What year?
        year = msg.date.year
        
        # Iterate through words
        for word in tokenize(msg.subject):
            if word in STOP_WORDS:
                continue
            if len(word) <= 3:
                continue
            self.counts[word] = self.counts.get(word,0) + 1
            for email in contacts:
                pincr(self.contact_counts,
                      (email, 'words', word, 'total'))
                pincr(self.contact_counts,
                      (email, 'words', word, 'year', str(year)))
    
    def commit(self, extras={}):
        extras.setdefault('contact_data', {})
        aggregate_dicts(extras['contact_data'],
                        self.contact_counts)


class GetWordCountsProcessor(ContactProcessor):
    def post_process(self, contact, data):
        """
        Get top X words per contact, total and per year
        Get top X words based on popularity and how unique
        they are to that year -- i.e. count-per-year^2 / total-count
        """
        total_word_counts = []
        yearly_word_counts = {}
        yearly_word_counts_adjusted = {}
        
        word_dicts = data.pop('words', {})
        for word, word_dict in word_dicts.iteritems():
            total_count = word_dict['total']
            total_word_counts.append((total_count, word))
            for year, count in word_dict['year'].iteritems():
                yearly_word_counts.setdefault(year, [])\
                                  .append((count, word))
                adjusted_count = (count ** 2) / float(total_count)
                yearly_word_counts_adjusted.setdefault(year, [])\
                                           .append((adjusted_count, word))
        
        
        # Set actual data for VizData purposes
        data['top_topics'] = []
        total_word_counts.sort()
        for count, word in reversed(
                total_word_counts[-settings.TOP_TOPICS:]):
            data['top_topics'].append(
                (word, count)
            )
        
        data['top_topics_by_year'] = []
        for year, counts in yearly_word_counts.iteritems():
            topics = []
            counts.sort()
            for count, word in reversed(counts[-settings.TOP_TOPICS:]):
                topics.append((word, count))
            data['top_topics_by_year'].append((year, topics))
        data['top_topics_by_year'].sort()
        
        data['top_topics_by_year_adjusted'] = []
        for year, counts in yearly_word_counts_adjusted.iteritems():
            topics = []
            counts.sort()
            for count, word in reversed(counts[-settings.TOP_TOPICS:]):
                topics.append((word, count))
            data['top_topics_by_year_adjusted'].append((year, topics))
        data['top_topics_by_year_adjusted'].sort()

