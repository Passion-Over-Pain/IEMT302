import spacy
import logging
import re
import random
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)

# Point-of-view conversion
povs = {
    "I am": "you are", "I was": "you were", "I'm": "you're", "I'd": "you'd", "I've": "you've", "I'll": "you'll",
    "you are": "I am", "you were": "I was", "you're": "I'm", "you'd": "I'd", "you've": "I've", "you'll": "I'll",
    "I": "you", "my": "your", "your": "my", "yours": "mine", "you": "I", "me": "you",
}
povs_c = re.compile(r'\b({})\b'.format('|'.join(re.escape(pov) for pov in povs)))

# --- SENTENCE Handlers ---
def wh_question_handler(nlp, sentence, verbs_idxs, user_name=None):
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
    reply += random.choice([", but keep reflecting on it.", ". Perhaps write more about it later.", ". Let's think about it together."])
    return f"{user_name}, {reply}" if user_name else reply

def yn_question_handler(nlp, sentence, verbs_idxs, user_name=None):
    reply = random.choice(["Yes.", "No.", "Maybe.", "I'm not sure."])
    return f"{user_name}, {reply}" if user_name else reply

def wish_handler(nlp, sentence, verbs_idxs, user_name=None):
    reply = re.sub(povs_c, lambda match: povs.get(match.group()), sentence.text)
    reply = random.choice(["Understood: ", "Got it: "]) + reply
    return f"{user_name}, {reply}" if user_name else reply

def instruction_handler(nlp, sentence, verbs_idxs, user_name=None):
    reply = re.sub(povs_c, lambda match: povs.get(match.group()), sentence.text)
    reply = random.choice(["Understood: ", "Got it: "]) + reply
    reply += random.choice(["", " Let's work on that together."])
    return f"{user_name}, {reply}" if user_name else reply

def generic_handler(nlp, sentence, verbs_idxs, user_name=None):
    reply = re.sub(povs_c, lambda match: povs.get(match.group()), sentence.text)
    return f"{user_name}, {reply}" if user_name else reply

# --- Sentence and Verb Matchers ---
from spacy.matcher import Matcher, DependencyMatcher

class SentenceTyper(Matcher):
    def __init__(self, vocab):
        super().__init__(vocab)
        # WH-questions
        self.add("WH-QUESTION", patterns=[[{"IS_SENT_START": True, "TAG": {"IN": ["WDT", "WP", "WP$", "WRB"]}}]])
        # Yes/No questions
        self.add("YN-QUESTION", patterns=[
            [{"IS_SENT_START": True, "TAG": "MD"}, {"POS": {"IN": ["PRON", "PROPN", "DET"]}}],
            [{"IS_SENT_START": True, "POS": "VERB"}, {"POS": {"IN": ["PRON", "PROPN", "DET"]}}, {"POS": "VERB"}]
        ])
        # Imperative
        self.add("INSTRUCTION", patterns=[
            [{"IS_SENT_START": True, "TAG": "VB"}],
            [{"IS_SENT_START": True, "LOWER": {"IN": ["please", "kindly"]}}, {"TAG": "VB"}]
        ])
        # Wish
        self.add("WISH", patterns=[
            [{"IS_SENT_START": True, "TAG": "PRP"}, {"TAG": "MD"},
             {"POS": "VERB", "LEMMA": {"IN": ["love", "like", "appreciate"]}}],
            [{"IS_SENT_START": True, "TAG": "PRP"}, {"POS": "VERB", "LEMMA": {"IN": ["want", "need", "require"]}}]
        ])

    def __call__(self, *args, **kwargs):
        matches = super().__call__(*args, **kwargs)
        if matches:
            match_id, _, _ = matches[0]
            if match_id == self.vocab["WH-QUESTION"]:
                return wh_question_handler
            elif match_id == self.vocab["YN-QUESTION"]:
                return yn_question_handler
            elif match_id == self.vocab["WISH"]:
                return wish_handler
            elif match_id == self.vocab["INSTRUCTION"]:
                return instruction_handler
        else:
            return generic_handler


class VerbFinder(DependencyMatcher):
    def __init__(self, vocab):
        super().__init__(vocab)
        self.add("VERBPHRASE", [[{"RIGHT_ID": "node0", "RIGHT_ATTRS": {"DEP": "ROOT"}}]])

    def __call__(self, *args, **kwargs):
        verbmatches = super().__call__(*args, **kwargs)
        if verbmatches:
            match_id, token_idxs = verbmatches[0]
            return sorted(token_idxs)
        return []

# --- Main Chat Function ---
def chat():
    nlp = spacy.load('en_core_web_sm')
    sentencetyper = SentenceTyper(nlp.vocab)
    verbfinder = VerbFinder(nlp.vocab)

    user_name = input("Welcome, What's your name? ")

    print(f"Hello {user_name}! Let's reflect on your day. Type 'exit' to quit.")
    while True:
        text = input(f"{user_name}: ")
        if text.lower() in ["exit", "quit"]:
            print(f"Goodbye {user_name}! Have a great day!")
            break

        # Current day and time
        now = datetime.now()
        day = now.strftime("%A")
        time = now.strftime("%H:%M")

        doc = nlp(text)
        reply = f"[{day}, {time}] "
        for sentence in doc.sents:
            verbs_idxs = verbfinder(sentence.as_doc())
            reply += (sentencetyper(sentence.as_doc()))(nlp, sentence, verbs_idxs, user_name) + " "
        print("Bot:", reply.strip())

#We run the bot here
if __name__ == "__main__":
    chat()
