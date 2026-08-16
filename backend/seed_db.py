"""Reset the database and seed the calibrated question bank.

Questions carry a `difficulty` on the same 1-10 scale as a learner's level, so
the adaptive placement test can pick an item matched to the current ability
estimate. Two items per (skill, difficulty) gives the selector room to avoid
repeats across retakes and practice tests.

Run with the backend virtualenv active:

    python seed_db.py
"""
import bcrypt

import models
from database import SessionLocal, engine

# (difficulty, question, option_a, option_b, option_c, option_d, correct, explanation)
Item = tuple[int, str, str, str, str, str, str, str]


VOCABULARY: list[Item] = [
    (1, "Which word means the opposite of 'big'?", "large", "small", "tall", "wide", "B",
     "'Small' is the direct opposite of 'big'. 'Large' is a synonym."),
    (1, "What do you call the meal you eat in the morning?", "dinner", "supper", "breakfast", "lunch", "C",
     "Breakfast is the morning meal - it literally 'breaks' the overnight 'fast'."),
    (2, "Which word means 'to begin'?", "start", "stop", "finish", "end", "A",
     "'Start' means to begin. The other three all mean to conclude."),
    (2, "A person who teaches in a school is a ___.", "doctor", "driver", "teacher", "farmer", "C",
     "Teacher comes from 'teach' - the -er ending means the person who does it."),
    (3, "Which word is closest in meaning to 'rapid'?", "slow", "quick", "heavy", "quiet", "B",
     "'Rapid' and 'quick' both describe high speed."),
    (3, "What does the prefix 'un-' mean in 'unhappy'?", "very", "again", "not", "before", "C",
     "'Un-' means 'not', so unhappy means not happy."),
    (4, "Which word means 'happening every year'?", "monthly", "annual", "weekly", "daily", "B",
     "'Annual' comes from the Latin 'annus', meaning year."),
    (4, "Choose the best synonym for 'reluctant'.", "eager", "unwilling", "confident", "curious", "B",
     "Someone reluctant hesitates to act - the opposite of eager."),
    (5, "Which of the following is a synonym for 'meticulous'?", "Careless", "Detailed", "Fast", "Angry", "B",
     "Meticulous means showing great attention to detail."),
    (5, "What does 'inevitable' mean?", "avoidable", "certain to happen", "unlikely", "reversible", "B",
     "Inevitable means it cannot be prevented - 'in-' (not) plus 'evitable' (avoidable)."),
    (6, "Identify the antonym for 'benevolent'.", "Kind", "Generous", "Malevolent", "Happy", "C",
     "'Bene-' means good and 'male-' means bad, so malevolent is the direct opposite."),
    (6, "What does the word 'ephemeral' mean?", "Lasting forever", "Short-lived", "Very bright", "Heavy", "B",
     "Ephemeral describes something that lasts a very short time."),
    (7, "Which word is closest in meaning to 'ubiquitous'?", "Rare", "Found everywhere", "Hidden", "Loud", "B",
     "Ubiquitous comes from the Latin 'ubique', meaning everywhere."),
    (7, "A 'pragmatic' decision is one that is ___.", "idealistic", "practical", "emotional", "hasty", "B",
     "Pragmatic means dealing with things sensibly and realistically."),
    (8, "Which word means 'to formally give up a position of power'?", "abdicate", "advocate", "adjudicate", "allocate", "A",
     "Abdicate means to renounce a throne or high office."),
    (8, "'Her explanation was perspicuous' means it was ___.", "confusing", "clearly expressed", "lengthy", "insincere", "B",
     "Perspicuous means clearly expressed. Do not confuse it with 'perspicacious', which describes a sharp observer."),
    (9, "Which word describes an argument that is deliberately misleading but appears sound?", "cogent", "specious", "lucid", "candid", "B",
     "Specious means superficially plausible but actually wrong."),
    (9, "'The committee's response was equivocal' means it was ___.", "decisive", "deliberately ambiguous", "hostile", "unanimous", "B",
     "Equivocal means open to more than one interpretation, usually on purpose."),
    (10, "Which pair correctly distinguishes 'refute' from 'rebut'?", "They are interchangeable", "Refute means to disprove; rebut means to argue against", "Rebut means to disprove; refute means to argue against", "Both mean to ignore", "B",
     "To refute is to prove false; to rebut is merely to offer a counter-argument."),
    (10, "A 'disinterested' judge is one who is ___.", "bored by the case", "impartial", "hostile to both parties", "poorly informed", "B",
     "Disinterested means having no stake in the outcome. 'Uninterested' means bored."),
]

GRAMMAR: list[Item] = [
    (1, "Choose the correct sentence.", "I is happy.", "I am happy.", "I are happy.", "I be happy.", "B",
     "The verb 'be' takes 'am' with the subject 'I'."),
    (1, "Complete: 'She ___ to school every day.'", "go", "goes", "going", "gone", "B",
     "A singular subject like 'she' takes the -s form of the verb in the present tense."),
    (2, "Which word correctly completes: 'There ___ three books on the table.'", "is", "am", "are", "be", "C",
     "'Three books' is plural, so it takes the plural verb 'are'."),
    (2, "What is the past tense of 'go'?", "goed", "gone", "went", "going", "C",
     "'Go' is irregular: go / went / gone."),
    (3, "Select the correct word: 'She runs ___ than her brother.'", "fast", "fastly", "faster", "more fast", "C",
     "Short adjectives form the comparative with -er, not with 'more'."),
    (3, "Which sentence is grammatically correct?", "Their going to the store.", "They're going to the store.", "There going to the store.", "They going to the store.", "B",
     "'They're' is the contraction of 'they are', which is what this sentence needs."),
    (4, "Choose the correct verb: 'Neither of the boys ___ going to the park.'", "is", "are", "am", "be", "A",
     "'Neither' is singular, so it takes 'is' even though 'boys' is plural."),
    (4, "Identify the error: 'He don't know the answer.'", "He", "don't", "know", "answer", "B",
     "The third-person singular requires 'doesn't', not 'don't'."),
    (5, "Which sentence uses the article correctly?", "I saw a elephant.", "I saw an elephant.", "I saw elephant.", "I saw an the elephant.", "B",
     "'An' is used before a vowel sound, and 'elephant' begins with one."),
    (5, "Choose the correctly punctuated complex sentence.", "Although it was late we kept working.", "Although it was late, we kept working.", "Although, it was late we kept working.", "Although it was late; we kept working.", "B",
     "A dependent clause placed first is followed by a comma."),
    (6, "Which sentence uses the passive voice?", "The committee rejected the proposal.", "The proposal was rejected by the committee.", "The committee is rejecting proposals.", "Reject the proposal.", "B",
     "In the passive, the subject receives the action rather than performing it."),
    (6, "Identify the dangling modifier.", "Walking to the station, I was caught by the rain.", "Walking to the station, the rain started.", "As I walked to the station, it rained.", "It rained while I walked to the station.", "B",
     "The rain was not walking - the modifier has no logical subject to attach to."),
    (7, "Choose the correct conditional: 'If I ___ more time, I would help.'", "have", "had", "will have", "would have", "B",
     "A second conditional (unlikely or hypothetical) uses the past form in the 'if' clause."),
    (7, "Which sentence has correct parallel structure?", "She likes swimming, to cycle, and running.", "She likes swimming, cycling, and running.", "She likes to swim, cycling, and she runs.", "She likes swim, cycle, and running.", "B",
     "Items joined by 'and' must share the same grammatical form."),
    (8, "Choose the correct subjunctive: 'The board recommends that he ___ immediately.'", "resigns", "resign", "will resign", "resigned", "B",
     "After verbs of recommendation the subjunctive uses the bare infinitive."),
    (8, "Which is the correct third conditional?", "If I would have known, I would have called.", "If I had known, I would have called.", "If I knew, I would have called.", "If I have known, I would call.", "B",
     "'Would' never belongs in the 'if' half of a conditional."),
    (9, "Identify the sentence with a correctly placed 'only'.", "She only drives to work on Fridays.", "She drives only to work on Fridays.", "She drives to work only on Fridays.", "Only she drives to work on Fridays.", "C",
     "All four are grammatical, but only C unambiguously limits the day, which is the intended meaning."),
    (9, "Which sentence correctly uses a restrictive clause?", "My brother, who lives in Pune, is visiting.", "My brother who lives in Pune is visiting.", "My brother; who lives in Pune, is visiting.", "My brother who lives in Pune, is visiting.", "B",
     "Without commas the clause is restrictive: it identifies which brother among several."),
    (10, "Which sentence correctly maintains sequence of tenses?", "She said she is tired yesterday.", "She said she was tired.", "She says she was tired yesterday and is tired now too.", "She said she will be tired yesterday.", "B",
     "A past reporting verb normally shifts the reported clause into the past."),
    (10, "Which is correct?", "The data suggests a trend, and it are consistent.", "The data suggest a trend, and they are consistent.", "The datas suggest a trend.", "The data suggesting a trend.", "B",
     "In formal and scientific usage 'data' is a plural noun taking a plural verb."),
]

READING: list[Item] = [
    (1, "Read: 'The shop opens at 9 a.m. and closes at 6 p.m.' When does the shop close?", "9 a.m.", "6 p.m.", "It never closes", "The text does not say", "B",
     "The closing time is stated directly in the sentence."),
    (1, "Read: 'Meera has a red bicycle.' What colour is the bicycle?", "blue", "green", "red", "black", "C",
     "The colour is stated directly."),
    (2, "Read: 'Before switching on the machine, check the tray is empty.' What do you do first?", "Switch on the machine", "Check the tray", "Close the lid", "Press the button", "B",
     "'Before' reverses the order: checking the tray comes first."),
    (2, "A sign reads 'No entry except staff'. Who may enter?", "Anyone", "Nobody", "Only staff", "Only visitors", "C",
     "'Except staff' carves staff out of the prohibition."),
    (3, "Read: 'Despite the heavy rain, the team continued their practice.' What does this imply?", "The rain stopped them.", "They gave up.", "They persevered.", "They went indoors.", "C",
     "'Despite' signals that the obstacle did not prevent the action."),
    (3, "Where is the main idea of a paragraph usually found?", "In the middle", "At the end", "In the topic sentence", "In an example", "C",
     "Most paragraphs state the main idea in an opening topic sentence."),
    (4, "'The old clock tower stood as a silent guardian of the town.' Which device is used?", "Simile", "Metaphor", "Personification", "Hyperbole", "C",
     "Human qualities - guarding, silence - are given to an inanimate object."),
    (4, "Which statement is a fact rather than an opinion?", "The bridge was a waste of money.", "The bridge was completed in 2019.", "The bridge is ugly.", "The bridge should never have been built.", "B",
     "Only B can be checked against a record."),
    (5, "If an author's tone is 'cynical', they are likely expressing:", "Joy and hope", "Doubt and negativity", "Rage", "Grief", "B",
     "Cynicism is a distrustful, negative attitude toward motives."),
    (5, "Read: 'Ravi checked his watch for the third time and left before the speaker finished.' What can be inferred?", "Ravi was impatient.", "Ravi disliked the speaker.", "Ravi had no watch.", "The talk was short.", "A",
     "Repeated watch-checking and early departure support impatience; disliking the speaker is a guess the text does not support."),
    (6, "Which signal words indicate a compare-and-contrast structure?", "first, then, finally", "however, whereas, unlike", "because, therefore", "for example, such as", "B",
     "These words mark similarity and difference between two things."),
    (6, "A text that presents only one side and uses emotive adjectives is most likely intended to:", "inform neutrally", "persuade", "entertain", "instruct", "B",
     "One-sided framing plus loaded language is characteristic of persuasive writing."),
    (7, "'Cities with more libraries have lower crime.' What is the flaw in concluding libraries reduce crime?", "The data is fabricated", "Correlation does not establish causation", "The sample is too large", "Libraries are irrelevant to cities", "B",
     "Both may be caused by a third factor such as higher public spending."),
    (7, "Which is the best summary technique?", "Copy the first sentence of each paragraph", "State each main idea in your own words, keeping the connectives", "List every statistic", "Quote the conclusion", "B",
     "A summary must preserve the argument's logic, which copying first sentences loses."),
    (8, "Restating an opponent's argument in a weaker form in order to defeat it is called:", "false dilemma", "straw man", "appeal to authority", "circular reasoning", "B",
     "The straw man attacks a distorted version rather than the real argument."),
    (8, "'Crime rose 100%' is potentially misleading because:", "Percentages are always wrong", "The base figure may be tiny", "Crime cannot be measured", "100% is impossible", "B",
     "A rise from two cases to four is a 100% increase but barely a change."),
    (9, "When two sources disagree, the most useful first step is to:", "Pick the more recent one", "Identify the exact point of disagreement", "Average their conclusions", "Discard both", "B",
     "Disagreements are usually narrower than they appear and often turn on definitions."),
    (9, "In dense academic prose, the most effective first step in unpacking a sentence is to:", "look up every unfamiliar word", "find the main verb", "read the conclusion first", "count the clauses", "B",
     "Locating the main verb reveals the trunk sentence that everything else hangs from."),
    (10, "A text that does not address your question at all is best described as:", "ambiguous", "vague", "underdetermined", "contradictory", "C",
     "Underdetermination means the text simply does not settle the question, which readers often mistake for ambiguity."),
    (10, "The question 'When did policy X stop working?' is problematic mainly because it:", "is too long", "presupposes the policy once worked", "uses the past tense", "mentions a policy", "B",
     "The question smuggles in an unexamined assumption that the answer must accept."),
]

PUNCTUATION: list[Item] = [
    (1, "Which sentence is punctuated correctly?", "my name is anil", "My name is Anil.", "my Name is anil.", "My name is anil", "B",
     "A sentence needs an initial capital, a capitalised name, and a full stop."),
    (1, "Which end mark belongs here: 'Are you coming___'", ".", "?", ",", ";", "B",
     "A direct question takes a question mark."),
    (2, "Which sentence uses commas correctly?", "I bought apples, oranges, and, bananas.", "I bought apples oranges and bananas.", "I bought apples, oranges and bananas.", "I bought, apples, oranges and bananas.", "C",
     "Commas separate list items; none belongs after 'bought'."),
    (2, "Which is correct?", "She asked whether the bus was late?", "She asked whether the bus was late.", "She asked, whether the bus was late?", "She asked whether the bus was late!", "B",
     "An indirect question takes a full stop, not a question mark."),
    (3, "Identify the correct possessive: 'The toys belonging to the children.'", "The childrens toys", "The childrens' toys", "The children's toys", "The children toys", "C",
     "'Children' is already plural, so the possessive adds apostrophe-s."),
    (3, "Which sentence uses 'its' and 'it's' correctly?", "Its raining and the dog lost it's collar.", "It's raining and the dog lost its collar.", "Its raining and the dog lost its collar.", "It's raining and the dog lost it's collar.", "B",
     "'It's' expands to 'it is'; possessive 'its' takes no apostrophe."),
    (4, "Which sentence correctly punctuates the introductory phrase?", "After the meeting we went home.", "After the meeting, we went home.", "After, the meeting we went home.", "After the meeting; we went home.", "B",
     "An introductory phrase is followed by a comma."),
    (4, "Which correctly punctuates direct speech?", "She said \"the train leaves at six\".", "She said, \"The train leaves at six.\"", "She said: \"the train leaves at six\"", "She said \"The train leaves at six\"", "B",
     "A comma introduces the quotation and the full stop sits inside the closing mark."),
    (5, "When should you use a semicolon?", "To end a sentence", "To join two independent clauses", "Before every list", "To show possession", "B",
     "A semicolon joins two clauses that could each stand alone."),
    (5, "Which sentence is a comma splice?", "It rained, so we stayed inside.", "It rained; we stayed inside.", "It rained, we stayed inside.", "It rained. We stayed inside.", "C",
     "Two complete sentences cannot be joined by a comma alone."),
    (6, "Which sentence uses the colon correctly?", "We need: flour, sugar and eggs.", "We need three things: flour, sugar and eggs.", "We need three things; flour, sugar and eggs.", "We need, three things: flour, sugar and eggs.", "B",
     "What precedes a colon must be a complete sentence."),
    (6, "Which correctly separates list items that already contain commas?", "Anil, the designer, Fatima, the engineer, and Rex, the intern.", "Anil, the designer; Fatima, the engineer; and Rex, the intern.", "Anil the designer: Fatima the engineer: and Rex the intern.", "Anil, the designer. Fatima, the engineer. And Rex, the intern.", "B",
     "Semicolons keep the three people distinct where commas would read as six."),
    (7, "Which sentence changes meaning if the commas are removed?", "My brother, who lives in Pune, is visiting.", "It rained, heavily.", "Yes, thank you.", "Well, perhaps.", "A",
     "With commas the writer has one brother; without them, the clause identifies which brother."),
    (7, "Which correctly writes a decade?", "the 1990's", "the 1990s", "the 1990s'", "the 199's0", "B",
     "Decades are plural, not possessive, so no apostrophe is used."),
    (8, "Which uses nested quotation marks correctly?", "She said, \"He called it \"predictable\", which surprised me.\"", "She said, \"He called it 'predictable', which surprised me.\"", "She said, 'He called it 'predictable', which surprised me.'", "She said \"He called it predictable, which surprised me\".", "B",
     "Nested quotations alternate between double and single marks."),
    (8, "What distinguishes a hyphen from an en dash?", "Nothing", "Hyphens join words; en dashes mark ranges", "En dashes join words; hyphens mark ranges", "Hyphens are only for numbers", "B",
     "'Well-known' uses a hyphen; '2019-2024' uses an en dash."),
    (9, "In 'No person shall drive, park or leave standing any vehicle', the ambiguity concerns:", "the word 'person'", "whether 'standing' attaches to 'leave' alone or the whole series", "the tense of 'shall'", "the absence of a subject", "B",
     "Distributing the verb across the series changes what is actually prohibited."),
    (9, "Which is the most reliable proofreading technique for punctuation?", "Read faster", "Read the text backwards sentence by sentence", "Read it twice in a row", "Use spell-check", "B",
     "Reading backwards breaks the meaning-flow that makes you skim over errors."),
    (10, "In a document mixing British and American conventions, the primary problem is:", "One of them is incorrect", "Inconsistency, regardless of which is chosen", "British spelling is outdated", "American punctuation is informal", "B",
     "Both conventions are valid; switching between them within one document is the error."),
    (10, "In a bulleted list, which practice is correct?", "End some items with semicolons and others with nothing", "Apply one terminal-punctuation rule consistently across all items", "Always end every item with a full stop", "Never punctuate list items", "B",
     "Either convention works; mixing them within one list is the visible error."),
]

SPELLING: list[Item] = [
    (1, "Which word is spelled correctly?", "hows", "houze", "house", "hous", "C",
     "The /ow/ sound here is spelled 'ou', followed by silent e."),
    (1, "Which is the correct plural of 'book'?", "bookes", "books", "book's", "bookies", "B",
     "Most nouns form the plural by adding -s. An apostrophe never makes a plural."),
    (2, "Which word is spelled correctly?", "freind", "frend", "friend", "friynd", "C",
     "'Friend' keeps the i before the e despite the pronunciation."),
    (2, "What is the plural of 'box'?", "boxs", "boxes", "boxies", "box's", "B",
     "Words ending in x add -es."),
    (3, "Which is spelled correctly?", "recieve", "receive", "receve", "receeve", "B",
     "After 'c', the /ee/ sound is spelled 'ei'."),
    (3, "What is the plural of 'baby'?", "babys", "babyes", "babies", "babie's", "C",
     "Consonant + y becomes -ies in the plural."),
    (4, "Which is the correct -ing form of 'run'?", "runing", "running", "runningg", "runnin", "B",
     "A stressed consonant-vowel-consonant ending doubles the final consonant."),
    (4, "Which sentence uses the right word?", "Their going to loose the match.", "They're going to lose the match.", "There going to loose the match.", "They're going to loose the match.", "B",
     "'They're' means they are; 'lose' is the verb, 'loose' means not tight."),
    (5, "Which is spelled correctly?", "seperate", "seperete", "separate", "saperate", "C",
     "Separate has an 'a' in the middle - there is 'a rat' in separate."),
    (5, "Choose the correct word: 'Please ___ my apology.'", "except", "accept", "expect", "acsept", "B",
     "'Accept' means to receive; 'except' means to leave out."),
    (6, "Which is spelled correctly?", "definately", "definitly", "definitely", "definetly", "C",
     "Definitely contains the word 'finite'."),
    (6, "Choose the correct word: 'The new rule will ___ everyone.'", "effect", "affect", "afect", "efect", "B",
     "'Affect' is usually the verb; 'effect' is usually the noun."),
    (7, "Which is spelled correctly?", "accomodate", "acommodate", "accommodate", "acomodate", "C",
     "Accommodate is large enough to accommodate two c's and two m's."),
    (7, "Which sentence is correct?", "The principle gave a speech about honesty.", "The principal gave a speech about honesty.", "The principel gave a speech.", "The principled gave a speech about honesty.", "B",
     "The head of a school is the principal - your 'pal'. A principle is a rule."),
    (8, "Which is spelled correctly?", "concience", "conscience", "consience", "conshience", "B",
     "Conscience contains the word 'science'."),
    (8, "Which is the correct British spelling?", "traveled", "travelled", "travelld", "travailed", "B",
     "British English doubles a final l before a vowel ending; American English does not."),
    (9, "Which is the correct singular form?", "criteria", "criterion", "criterias", "criterium", "B",
     "'Criteria' is the plural; one standard is a criterion."),
    (9, "Which is spelled correctly?", "occurence", "occurrance", "occurrence", "ocurrence", "C",
     "Occurrence doubles both the c and the r, and ends in -ence."),
    (10, "Which sentence is correct?", "This phenomena is well documented.", "These phenomena are well documented.", "These phenomenas are well documented.", "This phenomenas is well documented.", "B",
     "'Phenomena' is plural; the singular is 'phenomenon'."),
    (10, "Which word is spelled correctly?", "liason", "liaison", "liasion", "liaisson", "B",
     "Liaison keeps the French spelling: l-i-a-i-s-o-n."),
]


BANK: dict[str, list[Item]] = {
    "Vocabulary": VOCABULARY,
    "Grammar": GRAMMAR,
    "Reading Comprehension": READING,
    "Punctuation": PUNCTUATION,
    "Spelling": SPELLING,
}


def seed():
    print("Dropping all existing tables...")
    models.Base.metadata.drop_all(bind=engine)

    print("Recreating tables with the current schema...")
    models.Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("Creating admin user...")
        hashed = bcrypt.hashpw("password123".encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        )
        db.add(
            models.User(
                username="admin",
                email="admin@example.com",
                hashed_password=hashed,
                preferred_language="en-IN",
            )
        )

        print("Creating subject...")
        subject = models.Subject(
            name="English Literacy",
            description=(
                "Adaptive diagnostic covering Vocabulary, Grammar, Reading "
                "Comprehension, Punctuation and Spelling across levels 1-10."
            ),
        )
        db.add(subject)
        db.commit()
        db.refresh(subject)

        print("Creating calibrated question bank...")
        count = 0
        for skill, items in BANK.items():
            for difficulty, text, a, b, c, d, correct, explanation in items:
                db.add(
                    models.Question(
                        subject_id=subject.id,
                        question_text=text,
                        option_a=a,
                        option_b=b,
                        option_c=c,
                        option_d=d,
                        correct_option=correct,
                        skill_tag=skill,
                        difficulty=difficulty,
                        explanation=explanation,
                    )
                )
                count += 1

        db.commit()
        print(f"Seeded {count} questions across {len(BANK)} skills, levels 1-10.")
        print("Database seeded successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
