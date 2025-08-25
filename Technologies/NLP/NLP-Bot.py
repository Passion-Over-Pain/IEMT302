import spacy
import logging
import re
import random

# Was unable to create a Telegram account therefore created a local bot
# The local bot uses spaCy for NLP just as the Telegram bot would have
# Used POV conversions, Sentence Type Handlers, Verb and WISH handlers
# Only difference is the input wrapper:        Telegram interface vs Local Console interface
# Additional logging for debugging

# With this I can debug messages
logging.basicConfig(level=logging.DEBUG)

# Point-of-view conversion - like telegram bot
povs = {
    "I am": "you are", "I was": "you were", "I'm": "you're", "I'd": "you'd", "I've": "you've", "I'll": "you'll",
    "you are": "I am", "you were": "I was", "you're": "I'm", "you'd": "I'd", "you've": "I've", "you'll": "I'll",
    "I": "you", "my": "your", "your": "my", "yours": "mine", "you": "I", "me": "you",
}
povs_c = re.compile(r'\b({})\b'.format('|'.join(re.escape(pov) for pov in povs)))

def wh_question_handler(nlp, sentence, verbs_idxs):
    """Qualitative answer, rearranges subject & verb"""
    reply = []
    reply.append(sentence[0].text.lower())  # WH-word
    part = [chunk.text for chunk in sentence.noun_chunks if chunk.root.dep_ == 'nsubj']
    if part: reply.append(part[0])
    if verbs_idxs:
        reply.append(" ".join([sentence[i].text.lower() for i in verbs_idxs]))
    part = [chunk.text for chunk in sentence.noun_chunks if chunk.root.dep_ == 'dobj']
    if part: reply.append(part[0])
    reply = re.sub(povs_c, lambda match: povs.get(match.group()), " ".join(reply))
    reply = random.choice(["I don't know ", "I can't say "]) + reply
    reply += random.choice([
        ", but I'll try to find out.",
        ". Perhaps check back with me later.",
        ". I’ll try to figure it out for you."
    ])
    return reply

def yn_question_handler(nlp, sentence, verbs_idxs):
    """Yes/No answer"""
    reply = random.choice(["Yes.", "No.", "Maybe.", "I'm not sure."])
    return reply

def wish_handler(nlp, sentence, verbs_idxs):
    reply = re.sub(povs_c, lambda match: povs.get(match.group()), sentence.text)
    reply = random.choice(["Understood: ", "Got it: "]) + reply
    return reply

def instruction_handler(nlp, sentence, verbs_idxs):
    reply = re.sub(povs_c, lambda match: povs.get(match.group()), sentence.text)
    reply = random.choice(["Understood: ", "Got it: "]) + reply
    reply += random.choice(["", " I'll see what I can do."])
    return reply

def generic_handler(nlp, sentence, verbs_idxs):
    reply = re.sub(povs_c, lambda match: povs.get(match.group()), sentence.text)
    return reply


from spacy.matcher import Matcher
from spacy.matcher import DependencyMatcher

class SentenceTyper(Matcher):
    """Detects sentence types"""
    def __init__(self, vocab):
        super().__init__(vocab)
        # WH-questions
        self.add("WH-QUESTION", [[{"IS_SENT_START": True, "TAG": {"IN": ["WDT", "WP", "WP$", "WRB"]}}]])
        # Yes/No questions
        self.add("YN-QUESTION",
                 [[{"IS_SENT_START": True, "TAG": "MD"}, {"POS": {"IN": ["PRON", "PROPN", "DET"]}}],
                  [{"IS_SENT_START": True, "POS": "VERB"}, {"POS": {"IN": ["PRON", "PROPN", "DET"]}}, {"POS": "VERB"}]])
        # Imperative
        self.add("INSTRUCTION",
                 [[{"IS_SENT_START": True, "TAG": "VB"}],
                  [{"IS_SENT_START": True, "LOWER": {"IN": ["please", "kindly"]}}, {"TAG": "VB"}]])
        # Wish
        self.add("WISH",
                 [[{"IS_SENT_START": True, "TAG": "PRP"}, {"TAG": "MD"},
                   {"POS": "VERB", "LEMMA": {"IN": ["love", "like", "appreciate"]}}],
                  [{"IS_SENT_START": True, "TAG": "PRP"}, {"POS": "VERB", "LEMMA": {"IN": ["want", "need", "require"]}}]])

    def __call__(self, *args, **kwargs):
        matches = super().__call__(*args, **kwargs)
        if matches:
            match_id, _, _ = matches[0]
            if match_id == self.vocab["WH-QUESTION"]:
                return wh_question_handler
            elif match_id == self.vocab["YN-QUESTION"]:
                return generic_handler
            elif match_id == self.vocab["WISH"]:
                return wish_handler
            elif match_id == self.vocab["INSTRUCTION"]:
                return instruction_handler
        else:
            return generic_handler

class VerbFinder(DependencyMatcher):
    """Finds verbs in a sentence"""
    def __init__(self, vocab):
        super().__init__(vocab)
        self.add("VERBPHRASE",
                 [[{"RIGHT_ID": "node0", "RIGHT_ATTRS": {"DEP": "ROOT"}}]])

    def __call__(self, *args, **kwargs):
        verbmatches = super().__call__(*args, **kwargs)
        if verbmatches:
            match_id, token_idxs = verbmatches[0]
            return sorted(token_idxs)
        return []

# The input loop, in telegram I would have used the Telegram API to interact with the bot
def chat():
    nlp = spacy.load('en_core_web_sm')
    sentencetyper = SentenceTyper(nlp.vocab)
    verbfinder = VerbFinder(nlp.vocab)

    print("Chatbot is ready! Type 'exit' to quit.")
    while True:
        text = input("You: ")
        if text.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        doc = nlp(text)
        reply = ""
        for sentence in doc.sents:
            verbs_idxs = verbfinder(sentence.as_doc())
            reply += (sentencetyper(sentence.as_doc()))(nlp, sentence, verbs_idxs) + " "
        print("Bot:", reply.strip())

# Local bot Analysis vs Telegram
# Caveat 1: Lacks Telegrams security but since local it's fine :)
# Caveat 2: Didn't build through the botFather :(
# Caveat 3: Interface is bland but once again for testing works
if __name__ == "__main__":
    chat()

