"""Lesson content, indexed by (skill, band).

Bands map to level pairs: 1 = levels 1-2, 2 = 3-4, 3 = 5-6, 4 = 7-8, 5 = 9-10
(see `leveling.band_for_level`). Every entry supplies a module objective and
three lessons. Each lesson carries a `read_aloud` line that the voice layer
uses for pronunciation practice, which is why they are full sentences rather
than fragments.
"""
from __future__ import annotations

from typing import TypedDict


class LessonSpec(TypedDict):
    title: str
    objective: str
    body: str
    read_aloud: str
    minutes: int


class ModuleSpec(TypedDict):
    title: str
    objective: str
    lessons: list[LessonSpec]


def _m(title: str, objective: str, lessons: list[LessonSpec]) -> ModuleSpec:
    return {"title": title, "objective": objective, "lessons": lessons}


def _l(title: str, objective: str, body: str, read_aloud: str, minutes: int = 8) -> LessonSpec:
    return {
        "title": title,
        "objective": objective,
        "body": body.strip(),
        "read_aloud": read_aloud,
        "minutes": minutes,
    }


CONTENT: dict[str, dict[int, ModuleSpec]] = {
    # ------------------------------------------------------------------ #
    "Vocabulary": {
        1: _m(
            "Everyday Words",
            "Recognise and use the 500 most common English words with confidence.",
            [
                _l(
                    "Words You Meet Every Day",
                    "Read and understand high-frequency words on sight.",
                    """
About half of everything written in English is built from just a few hundred words:
*the, and, is, have, go, come, make, take, day, time, people, work*. Reading gets
much easier once these stop needing to be sounded out.

**How to practise**

1. Read the list aloud, one word per second. Speed matters more than perfection.
2. Cover a word, say it from memory, then check.
3. Put three of them into one sentence about your own day.

**Try it:** build a sentence using *work*, *time*, and *people*.
""",
                    "I go to work at the same time every day and meet many people there.",
                ),
                _l(
                    "Naming Things Around You",
                    "Build a working vocabulary for home, food, travel and money.",
                    """
Vocabulary grows fastest when it is attached to something you can see. Walk through
a room and name five objects out loud. If you do not know the English word, note it
and look it up - that gap is exactly where learning happens.

**Word groups to start with**

- **Home:** door, window, kitchen, shelf, floor
- **Food:** rice, bread, water, salt, fruit
- **Money:** price, change, cost, cheap, expensive

**Try it:** describe what you ate today using four food words.
""",
                    "The price of bread and fruit went up, so I bought rice instead.",
                ),
                _l(
                    "Words That Describe",
                    "Use simple adjectives to add detail to a sentence.",
                    """
A describing word (adjective) tells you *which one* or *what kind*. Compare
"I bought a bag" with "I bought a **small red** bag" - the second sentence gives
the listener a picture.

**Common pairs to learn together**

| Word | Opposite |
|---|---|
| big | small |
| hot | cold |
| early | late |
| easy | hard |

Learning opposites in pairs roughly doubles what you retain from each session.
""",
                    "The small red bag was cheap, but the big blue one was expensive.",
                ),
            ],
        ),
        2: _m(
            "Word Families and Context",
            "Work out unfamiliar words from their parts and from surrounding text.",
            [
                _l(
                    "Guessing From Context",
                    "Infer a word's meaning from the sentence around it.",
                    """
You do not need a dictionary for every unknown word. The sentence usually leaves
clues.

> The path was so **treacherous** that two hikers slipped and had to turn back.

You do not need to know *treacherous* to see it means dangerous - the slipping and
turning back give it away.

**The three clue types**

1. **Definition clue** - the sentence explains it directly ("a *cartographer*, or map-maker").
2. **Contrast clue** - a word like *but* or *unlike* signals an opposite.
3. **Example clue** - a list follows ("*citrus* fruits such as oranges and lemons").
""",
                    "The path was so treacherous that two hikers slipped and had to turn back.",
                ),
                _l(
                    "Prefixes and Suffixes",
                    "Break long words into parts to unlock their meaning.",
                    """
Most long English words are short words wearing a hat and shoes.

**Prefixes** (front) change meaning: *un-* (not), *re-* (again), *pre-* (before),
*mis-* (wrongly), *dis-* (opposite of).

**Suffixes** (back) change the job the word does: *-ful* (full of), *-less*
(without), *-ly* (in that manner), *-tion* (the act of), *-able* (can be).

So **un + help + ful** = not full of help. **re + consider + ation** = the act of
thinking again.

**Try it:** what does *irreplaceable* mean, part by part?
""",
                    "The decision was unhelpful, so we asked for a reconsideration.",
                ),
                _l(
                    "Choosing the Right Word",
                    "Distinguish words that are close in meaning but not interchangeable.",
                    """
Near-synonyms carry different weight. *Said*, *shouted*, *muttered* and *admitted*
all report speech, but each tells you something different about the speaker.

| Weaker | Stronger |
|---|---|
| good | excellent |
| bad | terrible |
| big | enormous |
| sad | devastated |

Reach for the strong word only when you mean it. A writer who calls everything
*enormous* leaves themselves nowhere to go.
""",
                    "She muttered that the result was bad, then admitted it was terrible.",
                ),
            ],
        ),
        3: _m(
            "Precision and Register",
            "Choose words that match your meaning and your audience.",
            [
                _l(
                    "Formal and Informal Registers",
                    "Match word choice to the situation.",
                    """
Register is the difference between *"Sorry, can't make it"* and *"I regret that I
am unable to attend"*. Both are correct English; only one belongs in a job
application.

| Informal | Formal |
|---|---|
| get | receive, obtain |
| ask for | request |
| find out | determine |
| put off | postpone |
| a lot of | considerable |

Notice the pattern: informal English leans on two-word phrasal verbs, formal
English on single Latin-derived verbs.
""",
                    "I regret that I am unable to attend, so I would like to request a postponement.",
                ),
                _l(
                    "Collocations: Words That Travel Together",
                    "Use the natural word pairings that native speakers expect.",
                    """
Some word pairs are simply conventional. We *make* a decision but *do* homework.
We say *heavy rain*, not *strong rain*, yet *strong coffee*, not *heavy coffee*.
Neither follows a rule - both are learned as units.

**High-value collocations**

- make: a decision, progress, an effort, a mistake
- do: research, business, damage, your best
- take: responsibility, a risk, advantage, notice
- pay: attention, a compliment, a visit

Learning the whole phrase is more efficient than learning the verb alone.
""",
                    "We must make an effort, take responsibility, and pay attention to the details.",
                ),
                _l(
                    "Idioms in Context",
                    "Recognise common idioms and avoid reading them literally.",
                    """
An idiom means something its individual words do not. *Break the ice* has nothing
to do with ice; *let the cat out of the bag* involves no cat.

**Frequently seen in workplace and news writing**

- *cut corners* - do something cheaply and badly
- *on the same page* - in agreement
- *a grey area* - not clearly covered by the rules
- *bite the bullet* - accept something unpleasant and get on with it

When a literal reading makes no sense, suspect an idiom.
""",
                    "We were on the same page, so nobody had to cut corners on the report.",
                ),
            ],
        ),
        4: _m(
            "Nuance and Connotation",
            "Control the emotional and rhetorical colour of your word choices.",
            [
                _l(
                    "Denotation vs Connotation",
                    "Separate what a word means from what it suggests.",
                    """
*Thrifty*, *frugal* and *stingy* all denote spending little. Their connotations
diverge sharply: the first is admiring, the second neutral, the third an insult.

| Positive | Neutral | Negative |
|---|---|---|
| confident | self-assured | arrogant |
| determined | persistent | stubborn |
| slender | thin | scrawny |
| curious | inquisitive | nosy |

Skilled writers pick a column deliberately. Careless writers pick one by accident
and puzzle their readers.
""",
                    "He was not stubborn but determined, and the distinction mattered to everyone involved.",
                ),
                _l(
                    "Academic and Technical Vocabulary",
                    "Read and use the vocabulary of formal argument.",
                    """
Formal writing runs on a shared set of abstract nouns and hedging verbs. Knowing
them is most of what makes an academic paragraph readable.

- *criterion / criteria* - the standard a thing is judged by
- *paradigm* - the accepted framework for thinking about something
- *empirical* - based on observation rather than theory
- *corroborate* - to support with additional evidence
- *ostensibly* - apparently, but perhaps not really

Note the hedging: *suggests*, *indicates*, *appears to*. Formal writing rarely
claims certainty outright, and mistaking that caution for weakness is a common
reading error.
""",
                    "The empirical data appears to corroborate the hypothesis, though the criteria remain contested.",
                ),
                _l(
                    "Figurative Language",
                    "Interpret metaphor, simile and personification accurately.",
                    """
- **Simile** - a comparison using *like* or *as*: "quiet **as** a held breath".
- **Metaphor** - a comparison stated as fact: "the deadline **was** a wall".
- **Personification** - human qualities given to a non-human thing: "the market
  **panicked**".

The reading skill is to ask *what property is being transferred?* When a report
says "the policy has teeth", the transferred property is the ability to bite -
that is, to enforce consequences.
""",
                    "The market panicked, and the new policy suddenly had teeth.",
                ),
            ],
        ),
        5: _m(
            "Rhetorical Command",
            "Deploy vocabulary for precise persuasive and analytical effect.",
            [
                _l(
                    "Etymology as a Tool",
                    "Use word origins to decode unfamiliar technical vocabulary.",
                    """
Roughly 60% of English vocabulary comes from Latin and Greek, concentrated in
exactly the technical and academic words that look hardest.

| Root | Meaning | Words |
|---|---|---|
| *ben-* | good | benevolent, benign, benefit |
| *magn-* | great | magnify, magnanimous, magnitude |
| *ject-* | throw | reject, projection, conjecture |
| *loqu-* | speak | eloquent, loquacious, colloquial |

*Conjecture* is literally a throwing-together of ideas - a guess. Once you own a
root, you own a family of words rather than one.
""",
                    "His magnanimous response was eloquent, though the conjecture beneath it was benign at best.",
                ),
                _l(
                    "Precision Under Pressure",
                    "Select the single most accurate word rather than an approximate one.",
                    """
At this level the failure mode is not ignorance but approximation - reaching for
a word that is *nearly* right.

- *refute* means to disprove; *rebut* only means to argue against. Most writers who
  say *refute* mean *rebut*.
- *comprise* - the whole comprises the parts. "Is comprised of" inverts it.
- *disinterested* means impartial; *uninterested* means bored.
- *fortuitous* means by chance, not fortunate.

Each of these is a place where a careful reader will notice.
""",
                    "A disinterested judge may rebut an argument without being able to refute it.",
                ),
                _l(
                    "Building a Personal Lexicon",
                    "Establish a durable system for acquiring and retaining new words.",
                    """
Beyond this level, vocabulary growth is a systems problem, not a study problem.

**A system that works**

1. **Capture** - note any word you had to reread, with the sentence it appeared in.
   The sentence matters more than the definition.
2. **Space it** - review after one day, three days, a week, a month.
3. **Produce it** - write one original sentence. Recognition and production are
   different skills, and only production survives.
4. **Prune** - drop words you have never once needed. A lexicon is not a trophy case.

Twenty words a week retained beats a hundred forgotten.
""",
                    "Capture the sentence, space the review, produce your own example, and prune what you never use.",
                ),
            ],
        ),
    },
    # ------------------------------------------------------------------ #
    "Grammar": {
        1: _m(
            "Sentence Basics",
            "Build correct simple sentences with matching subjects and verbs.",
            [
                _l(
                    "What Makes a Sentence",
                    "Identify the subject and verb in a simple sentence.",
                    """
Every English sentence needs two things: a **subject** (who or what) and a **verb**
(what they do or are).

> **Rain** *fell*. - subject *rain*, verb *fell*.
> **The children** *are* hungry. - subject *the children*, verb *are*.

"Running down the street" is not a sentence. Who was running? Without a subject it
is only a fragment.

**Try it:** find the subject and verb in *"My brother works at the hospital."*
""",
                    "My brother works at the hospital, and the children are hungry.",
                ),
                _l(
                    "Subject-Verb Agreement",
                    "Match singular subjects to singular verbs.",
                    """
A singular subject takes a singular verb; a plural subject takes a plural verb.

| Singular | Plural |
|---|---|
| The dog **runs**. | The dogs **run**. |
| She **has** a book. | They **have** books. |
| It **is** ready. | They **are** ready. |

Notice the trap: for regular verbs the *singular* form is the one with -s, which is
the opposite of how nouns work.
""",
                    "The dog runs in the park while the other dogs run beside the river.",
                ),
                _l(
                    "Past, Present and Future",
                    "Use the three basic tenses correctly.",
                    """
- **Present:** I *walk* to school. (habit or fact)
- **Past:** I *walked* to school. (finished)
- **Future:** I *will walk* to school. (not yet)

Most past-tense verbs just add **-ed**. The most common verbs are irregular and must
be memorised:

| Present | Past |
|---|---|
| go | went |
| eat | ate |
| see | saw |
| take | took |
| come | came |
""",
                    "Yesterday I walked to school, today I go by bus, and tomorrow I will take a taxi.",
                ),
            ],
        ),
        2: _m(
            "Building Longer Sentences",
            "Join clauses correctly and keep tense consistent across a sentence.",
            [
                _l(
                    "Joining Ideas",
                    "Connect two complete ideas without creating a run-on.",
                    """
Two complete ideas can be joined three ways:

1. **Full stop:** "It rained. We stayed inside."
2. **Comma + joining word** (and, but, so, or, yet): "It rained, **so** we stayed inside."
3. **Semicolon:** "It rained; we stayed inside."

What you may **not** do is join them with only a comma - "It rained, we stayed
inside" is a comma splice, one of the most common errors in written English.
""",
                    "It rained heavily, so we stayed inside and finished the work early.",
                ),
                _l(
                    "Keeping Tense Consistent",
                    "Avoid drifting between past and present within a passage.",
                    """
Pick a tense and stay in it unless the timeline genuinely changes.

> ✗ She *walked* into the room and *sees* the letter on the table.
> ✓ She *walked* into the room and *saw* the letter on the table.

The legitimate exception is a genuine shift in time:

> She *remembered* the letter she *had received* the previous week.

Here *had received* is correct because it happened before the main past action.
""",
                    "She walked into the room and saw the letter she had received the previous week.",
                ),
                _l(
                    "Articles: a, an, the",
                    "Choose the right article, including where none is needed.",
                    """
- **a / an** - one of many, mentioned for the first time. *An* before a vowel *sound*
  (an hour, a university - go by sound, not spelling).
- **the** - a specific one, already known to the listener.
- **no article** - general plurals and uncountable nouns: "Books are expensive",
  "Water is free".

> I bought **a** book. **The** book was excellent.

First mention takes *a*; every mention after that takes *the*.
""",
                    "I bought a book at the market, and the book turned out to be excellent.",
                ),
            ],
        ),
        3: _m(
            "Structure and Modifiers",
            "Control clause structure, modifiers and the passive voice.",
            [
                _l(
                    "Dependent and Independent Clauses",
                    "Build complex sentences that punctuate correctly.",
                    """
An **independent clause** stands alone. A **dependent clause** starts with a word
like *because, although, when, if, while* and cannot.

The punctuation rule follows the order:

> **Although it was late**, we kept working. ← dependent first, comma needed
> We kept working **although it was late**. ← independent first, no comma

Getting this one rule right removes a large share of comma errors in formal
writing.
""",
                    "Although it was late, we kept working until the report was finished.",
                ),
                _l(
                    "Misplaced and Dangling Modifiers",
                    "Place descriptive phrases next to what they describe.",
                    """
A modifier attaches to whatever is nearest. Put it in the wrong place and the
sentence says something you did not mean:

> ✗ **Walking to the station**, the rain started.
> The rain was not walking. This is a *dangling* modifier.
> ✓ **Walking to the station**, I was caught by the rain.

> ✗ She **almost** drove her children to school every day. (she nearly drove them?)
> ✓ She drove her children to school **almost** every day.

*Only*, *almost*, *just* and *even* are the usual offenders - place them immediately
before what they limit.
""",
                    "Walking to the station, I was caught by the rain that had almost stopped.",
                ),
                _l(
                    "Active and Passive Voice",
                    "Choose voice deliberately rather than by accident.",
                    """
- **Active:** The committee *rejected* the proposal. (subject acts)
- **Passive:** The proposal *was rejected* by the committee. (subject receives)

Active is usually shorter and clearer. Passive earns its place when:

- the actor is unknown - "The window **was broken** overnight"
- the actor is irrelevant - "The samples **were stored** at 4°C"
- you deliberately want to de-emphasise the actor - "Mistakes **were made**"

That last one is why the passive has a reputation. Use it knowingly.
""",
                    "The committee rejected the proposal, although the samples were stored correctly.",
                ),
            ],
        ),
        4: _m(
            "Advanced Syntax",
            "Handle conditionals, subjunctives and parallel structure with control.",
            [
                _l(
                    "Conditionals",
                    "Express real, unlikely and impossible conditions accurately.",
                    """
| Type | Form | Meaning |
|---|---|---|
| Zero | If you *heat* ice, it *melts*. | always true |
| First | If it *rains*, I *will stay*. | likely future |
| Second | If I *had* time, I *would help*. | unlikely / hypothetical |
| Third | If I *had known*, I *would have called*. | impossible, past |

The commonest error is mixing forms: ✗ "If I *would have* known" - the *would* never
belongs in the *if* half.
""",
                    "If I had known about the delay, I would have called you much earlier.",
                ),
                _l(
                    "The Subjunctive",
                    "Use subjunctive forms in formal recommendations and hypotheticals.",
                    """
The subjunctive survives in two places in modern English.

**After verbs of demand, suggestion and requirement** - use the bare verb:

> The board recommends that he **resign** (not *resigns*).
> It is essential that every form **be** signed.

**In counterfactual wishes** - use *were* for all persons:

> If I **were** you, I would wait.
> She wishes she **were** back in Delhi.
""",
                    "It is essential that every form be signed before the deadline passes.",
                ),
                _l(
                    "Parallel Structure",
                    "Keep items in a list or comparison grammatically matched.",
                    """
Items joined by *and*, *or*, or a comparison must share the same grammatical form.

> ✗ She likes *swimming*, *to cycle*, and *she runs*.
> ✓ She likes *swimming*, *cycling*, and *running*.

The rule extends to paired constructions - *not only... but also*, *either... or*,
*both... and*. Whatever follows the first half must match what follows the second:

> ✗ He is not only skilled **but also** he works hard.
> ✓ He is not only skilled **but also** hardworking.
""",
                    "She likes swimming, cycling, and running, and she is not only skilled but also hardworking.",
                ),
            ],
        ),
        5: _m(
            "Style and Control",
            "Manipulate sentence structure for rhythm, emphasis and clarity.",
            [
                _l(
                    "Sentence Variety and Rhythm",
                    "Vary length and structure to control pace.",
                    """
Uniform sentence length flattens prose regardless of how correct it is. Short
sentences land. Longer sentences, especially those that gather several related
observations before resolving, create momentum and let a reader settle in.

**The technique:** after a long, complex sentence, cut hard to a short one. The
contrast does the emphasis for you, without italics or exclamation marks.

Read your paragraph aloud. Wherever you run out of breath, or where three sentences
in a row have the same shape, revise.
""",
                    "The argument gathered evidence from three separate studies, weighed the objections, and reached a careful conclusion. It was wrong.",
                ),
                _l(
                    "Cohesion Across Paragraphs",
                    "Use reference and transition to bind a text together.",
                    """
Cohesion is what makes sentences feel like a paragraph instead of a list.

**Three devices**

1. **Reference** - *this*, *these*, *such* pointing back to a prior idea. Always give
   *this* a noun: "this **finding**", not a bare "this".
2. **Old-to-new** - start a sentence with information already established, and put
   the new information at the end. Each sentence then hands off to the next.
3. **Transitions** - *however*, *consequently*, *by contrast*. Use them to signal a
   genuine logical turn, not as decoration.
""",
                    "This finding raises a further question; consequently, the second study was designed differently.",
                ),
                _l(
                    "Editing Your Own Writing",
                    "Apply a systematic revision pass to your own prose.",
                    """
Writing and editing are different jobs. Do not attempt them at once.

**A revision pass, in order**

1. **Structure** - is each paragraph about one thing? Move before you polish.
2. **Cut** - delete every word that survives its own removal. *In order to* → *to*.
   *Due to the fact that* → *because*. *It is important to note that* → nothing.
3. **Verbs** - convert nominalisations back to verbs: "made a decision" → "decided".
4. **Read aloud** - your ear catches what your eye skims.

Expect a first draft to shed 15-25% of its words without losing any content.
""",
                    "Delete every word that survives its own removal, then read the whole thing aloud.",
                ),
            ],
        ),
    },
    # ------------------------------------------------------------------ #
    "Reading Comprehension": {
        1: _m(
            "Reading for Meaning",
            "Understand short everyday texts and find stated information.",
            [
                _l(
                    "Finding the Facts",
                    "Locate information that is stated directly in a text.",
                    """
The first comprehension skill is simply finding what the text says.

> *The clinic opens at 9 a.m. on weekdays and closes at 1 p.m. on Saturdays. It is
> shut on Sundays.*

- When does it open on Tuesday? **9 a.m.**
- Can you visit on Sunday? **No.**

**Method:** read the question first, then scan for the matching word - *Sunday*,
*Saturday*, *opens*. The answer sits next to it.
""",
                    "The clinic opens at nine in the morning on weekdays and closes early on Saturdays.",
                ),
                _l(
                    "Sequence and Instructions",
                    "Follow the order of steps in a set of instructions.",
                    """
Instructions depend on order words: *first, then, next, after, before, finally*.

> *Before you switch on the machine, check that the tray is empty. Then close the
> lid. Finally, press the green button.*

Note that *before* reverses the order in which the steps appear - checking the tray
happens **first**, even though it is mentioned inside the same sentence as switching
on. Watch for *before*, *after* and *until*: they describe order independently of
where they sit in the sentence.
""",
                    "Before you switch on the machine, check that the tray is empty and close the lid.",
                ),
                _l(
                    "Reading Signs and Forms",
                    "Extract information from the short functional texts of daily life.",
                    """
Signs, labels and forms compress meaning by dropping words.

- *No entry except staff* = only staff may enter.
- *Best before 12/25* = quality guaranteed until that date.
- *Fees payable in advance* = pay before, not after.

**On forms**, three words repay learning precisely:

- **Surname** - family name
- **Block capitals** - ALL CAPITAL LETTERS
- **Delete as applicable** - cross out the options that do not apply to you
""",
                    "Please write your surname in block capitals and delete the options that do not apply.",
                ),
            ],
        ),
        2: _m(
            "Main Ideas and Inference",
            "Identify the central point of a passage and read between the lines.",
            [
                _l(
                    "Finding the Main Idea",
                    "State a paragraph's central point in one sentence.",
                    """
The main idea is what the whole paragraph is about - not the most interesting
detail in it.

Most paragraphs put it in the **topic sentence**, usually first. The rest of the
paragraph supports it with examples, reasons or evidence.

**A reliable test:** if you deleted a sentence, would the paragraph lose its point,
or only lose a detail? The sentence you cannot delete is the main idea.
""",
                    "The main idea is what the whole paragraph is about, not the most interesting detail in it.",
                ),
                _l(
                    "Drawing Inferences",
                    "Reach conclusions the text supports but does not state.",
                    """
An inference is supported by the text without being written in it.

> *Ravi checked his watch for the third time and started walking towards the door
> before the speaker had finished.*

The text never says Ravi was impatient or late. But checking a watch repeatedly and
leaving early supports both. What it does **not** support is that he disliked the
speaker - that would be a guess, not an inference.

**The discipline:** for every inference, point to the words that support it. No
words, no inference.
""",
                    "Ravi checked his watch for the third time and started walking towards the door.",
                ),
                _l(
                    "Fact and Opinion",
                    "Separate verifiable claims from judgements.",
                    """
- **Fact:** can be checked. "The bridge was completed in 2019."
- **Opinion:** expresses a judgement. "The bridge was a waste of money."

**Opinion signals:** *best, worst, should, ought, beautiful, unfair, clearly,
obviously.*

Watch for opinions dressed as facts: "Everyone knows the bridge was a waste" adds
*everyone knows* to a judgement, which does not make it checkable. This is one of
the most useful reading habits you can build.
""",
                    "The bridge was completed in 2019, though many still believe it was a waste of money.",
                ),
            ],
        ),
        3: _m(
            "Structure and Purpose",
            "Analyse how a text is organised and why the author wrote it.",
            [
                _l(
                    "Text Structure",
                    "Recognise the common organisational patterns.",
                    """
Recognising the pattern tells you what to expect next and what to remember.

| Pattern | Signals |
|---|---|
| Chronological | first, then, in 1998, subsequently |
| Compare / contrast | however, whereas, similarly, unlike |
| Cause / effect | because, therefore, as a result, leads to |
| Problem / solution | the difficulty is, one approach, this addresses |

In a compare-and-contrast text, expect a second side - if you have only read one,
you are not finished.
""",
                    "Unlike the earlier approach, this method addresses the difficulty directly and therefore scales better.",
                ),
                _l(
                    "Author's Purpose and Tone",
                    "Identify why a text was written and the attitude behind it.",
                    """
Every text is written **to inform**, **to persuade**, **to entertain**, or **to
instruct** - often more than one.

**Tone** is the author's attitude, carried by word choice. Compare:

> The proposal was *ambitious*. → approving
> The proposal was *reckless*. → disapproving
> The proposal *allocated 40 crore over three years*. → neutral

Persuasive writing is often signalled by emotive adjectives and by presenting only
one side. Neutral reporting names both sides and attributes claims.
""",
                    "The proposal was ambitious, though its critics preferred to call it reckless.",
                ),
                _l(
                    "Summarising",
                    "Condense a passage without losing its argument.",
                    """
A good summary is short, in your own words, and keeps the argument's shape.

**Method**

1. Find the main idea of each paragraph.
2. Drop examples, statistics and repetition - keep the claims.
3. Join them with the original connectives (*however*, *therefore*) so the logic
   survives.
4. Check: could someone who has not read the original follow your version?

**The common failure:** copying the first sentence of each paragraph. That produces
a list, not a summary, because the connections between the paragraphs are lost.
""",
                    "Find each paragraph's main idea, drop the examples, and keep the connections between them.",
                ),
            ],
        ),
        4: _m(
            "Critical Reading",
            "Evaluate arguments, evidence and rhetorical technique.",
            [
                _l(
                    "Evaluating Evidence",
                    "Judge whether the support offered actually supports the claim.",
                    """
An argument makes a **claim** and offers **evidence**. The reader's job is to check
whether the second reaches the first.

**Questions worth asking every time**

- **Relevance:** does this evidence bear on *this* claim, or a nearby one?
- **Sufficiency:** is one case enough for a general conclusion?
- **Source:** who produced it, and what result suited them?
- **Correlation vs cause:** two things moving together is not one causing the other.

> *Cities with more libraries have lower crime.*

Plausibly both are caused by higher public spending. The correlation is real; the
causal claim is unsupported.
""",
                    "Cities with more libraries have lower crime, but correlation is not the same as cause.",
                ),
                _l(
                    "Detecting Bias and Rhetoric",
                    "Notice loaded language, selective framing and common fallacies.",
                    """
**Loaded language** - *regime* vs *government*, *scheme* vs *programme*, *admitted*
vs *said*. Each pair reports the same fact with a different thumb on the scale.

**Selective framing** - a true statistic chosen to mislead. "Crime rose 100%" is
alarming until you learn it went from two cases to four.

**Common fallacies**

- *Straw man* - restating an opponent's argument in a weaker form, then defeating it
- *False dilemma* - presenting two options when others exist
- *Appeal to authority* - a credential offered instead of evidence
""",
                    "Crime rose one hundred per cent, which sounds alarming until you learn it rose from two cases to four.",
                ),
                _l(
                    "Synthesising Multiple Sources",
                    "Combine several texts into one coherent understanding.",
                    """
Real comprehension usually means reconciling sources that disagree.

**Method**

1. Establish each source's **claim** and **stance** separately before comparing.
2. Map where they **agree** - that is your reliable ground.
3. Locate the exact point of **disagreement**. It is usually narrower than it
   appears, and is often about definitions rather than facts.
4. Ask **why** they differ: different data, different timeframe, or different
   interests?
5. State a position that accounts for both, or explain clearly why one is better
   supported.
""",
                    "The sources agree on the data but differ on its interpretation, and the disagreement is narrower than it appears.",
                ),
            ],
        ),
        5: _m(
            "Analytical Reading",
            "Read dense, ambiguous and specialist texts with independent judgement.",
            [
                _l(
                    "Reading Dense Prose",
                    "Work through complex academic and legal text systematically.",
                    """
Dense prose is usually dense because of **nested clauses** and **abstract nouns**,
not vocabulary.

**Unpacking technique**

1. Find the **main verb** of the sentence first. Everything else hangs off it.
2. Bracket subordinate clauses mentally and read the trunk sentence alone.
3. Turn abstract nouns back into verbs: "the *implementation* of the *reduction*"
   → "reducing it".
4. Re-add the clauses one at a time.

Legal text adds a further habit: read the definitions section first. A defined term
in a contract means exactly what the contract says, and nothing else.
""",
                    "Find the main verb first, bracket the subordinate clauses, and turn the abstract nouns back into verbs.",
                ),
                _l(
                    "Ambiguity and Interpretation",
                    "Handle texts that sustain more than one valid reading.",
                    """
At this level, "what does the text mean?" sometimes has more than one defensible
answer - and the skill is to hold them at once rather than force a choice.

**Distinguish three things**

- **Ambiguity** - the text genuinely supports two readings.
- **Vagueness** - the text is imprecise, but in one direction.
- **Underdetermination** - the text simply does not address the question you brought.

The last is the one readers most often mistake for the first. Before arguing that a
text is ambiguous, check that it was trying to answer your question at all.
""",
                    "Before arguing that a text is ambiguous, check whether it was trying to answer your question at all.",
                ),
                _l(
                    "Reading Against the Grain",
                    "Interrogate a text's assumptions, silences and framing.",
                    """
Reading *with* the grain means following an argument on its own terms. Reading
*against* it means asking what the argument had to assume in order to work.

**Three questions**

1. **What is presupposed?** "When did policy X stop working?" presupposes it once did.
2. **What is absent?** Whose perspective would complicate this account, and why is
   it missing?
3. **What does the framing make unaskable?** A report framed entirely as cost per
   unit cannot raise questions of value that resist counting.

This is not cynicism. A text can be honest, well-evidenced, and still shaped by
what its author found it natural to ask.
""",
                    "Ask what the argument had to assume in order to work, and whose perspective is missing from it.",
                ),
            ],
        ),
    },
    # ------------------------------------------------------------------ #
    "Punctuation": {
        1: _m(
            "Sentence Boundaries",
            "Use capital letters and end punctuation reliably.",
            [
                _l(
                    "Capital Letters and Full Stops",
                    "Mark where sentences begin and end.",
                    """
Every sentence starts with a **capital letter** and ends with a **full stop**,
question mark or exclamation mark.

Capitals are also used for:

- names of people and places: *Priya*, *Mumbai*
- days and months: *Monday*, *April*
- the word **I**, always

> ✗ my friend priya lives in mumbai. we met on monday
> ✓ My friend Priya lives in Mumbai. We met on Monday.
""",
                    "My friend Priya lives in Mumbai, and we met there on Monday.",
                ),
                _l(
                    "Question and Exclamation Marks",
                    "Choose the right end mark for the sentence type.",
                    """
- **Full stop (.)** - a statement. *The bus is late.*
- **Question mark (?)** - a direct question. *Is the bus late?*
- **Exclamation mark (!)** - surprise or strong feeling. *The bus is here!*

**The one trap:** an *indirect* question takes a full stop, not a question mark.

> ✗ She asked whether the bus was late?
> ✓ She asked whether the bus was late.

Use exclamation marks sparingly. One in a paragraph carries weight; four carry none.
""",
                    "Is the bus late? She asked whether it would arrive before noon.",
                ),
                _l(
                    "Commas in Lists",
                    "Separate items in a series correctly.",
                    """
Commas separate three or more items in a list:

> I bought rice, dal, oil and salt.

The comma before the final *and* (the "Oxford comma") is optional in British usage
and standard in American usage. Pick one and be consistent.

It is worth using when it removes ambiguity:

> I thanked my parents, Meera and Rohit.

Without a comma before *and*, this can be read as saying your parents are named
Meera and Rohit.
""",
                    "I bought rice, dal, oil and salt, and then I thanked my parents, Meera, and Rohit.",
                ),
            ],
        ),
        2: _m(
            "Commas and Apostrophes",
            "Apply the common comma rules and form possessives correctly.",
            [
                _l(
                    "Apostrophes for Possession",
                    "Show ownership without confusing plurals.",
                    """
| Situation | Form | Example |
|---|---|---|
| singular owner | 's | the **dog's** bowl |
| plural ending in s | s' | the **dogs'** bowls |
| irregular plural | 's | the **children's** toys |

**Never** use an apostrophe to make a plural. *Apple's for sale* is wrong.

**The exception that catches everyone:** *its* (belonging to it) has no apostrophe.
*It's* always means *it is* or *it has*. If you cannot expand it to "it is", it takes
no apostrophe.
""",
                    "The children's toys were left near the dog's bowl, and it's still there.",
                ),
                _l(
                    "Commas That Change Meaning",
                    "Use commas to separate introductory and extra information.",
                    """
**After an introductory phrase:**

> After the meeting**,** we went home.

**Around extra, removable information:**

> My brother**,** who lives in Pune**,** is visiting.

The test: if removing the phrase leaves a complete, still-true sentence, it takes
commas on both sides. Note the difference this makes:

> My brother, who lives in Pune, is visiting. → I have one brother.
> My brother who lives in Pune is visiting. → I have several; this is the Pune one.
""",
                    "My brother, who lives in Pune, is visiting us after the meeting.",
                ),
                _l(
                    "Quotation Marks",
                    "Punctuate direct speech and quoted material.",
                    """
Direct speech goes inside quotation marks, with a comma introducing it:

> She said**,** "The train leaves at six."
> "The train leaves at six**,**" she said.

Note that the comma goes *inside* the closing quotation mark in the second example.

**Indirect speech takes no quotation marks at all:**

> She said that the train left at six.
""",
                    "She said, \"The train leaves at six,\" and then repeated it more slowly.",
                ),
            ],
        ),
        3: _m(
            "Advanced Punctuation",
            "Use semicolons, colons and dashes with precision.",
            [
                _l(
                    "Semicolons",
                    "Join closely related independent clauses.",
                    """
A semicolon joins two complete sentences that are closely related:

> The rain did not stop**;** the match was abandoned.

Both halves must be able to stand alone. If one cannot, you need a comma instead.

**The second use:** separating list items that already contain commas.

> The team includes Anil, the designer**;** Fatima, the engineer**;** and Rex, the intern.

Without semicolons that list reads as six people rather than three.
""",
                    "The rain did not stop; the match was abandoned before the second innings began.",
                ),
                _l(
                    "Colons",
                    "Introduce lists, explanations and quotations.",
                    """
A colon says *here it comes*. What precedes it must be a complete sentence.

> We need three things**:** flour, sugar and eggs.
> The reason was simple**:** nobody had checked the date.

> ✗ We need**:** flour, sugar and eggs. ("We need" is not a complete sentence.)

**Colon vs semicolon:** a colon points forward to what follows; a semicolon balances
two things of equal weight.
""",
                    "The reason was simple: nobody had checked the date before sending the invitations.",
                ),
                _l(
                    "Dashes, Brackets and Ellipses",
                    "Mark interruptions and omissions appropriately.",
                    """
- **Em dash (—)** - a sharp interruption or emphatic aside. *The answer — and nobody
  expected this — was yes.*
- **Brackets ( )** - a quieter aside, incidental detail. *The report (published in
  2019) says otherwise.*
- **Ellipsis (...)** - words omitted from a quotation. *"The findings ... were
  inconclusive."*

Same information, three volumes: dashes shout, brackets murmur, commas are neutral.
Choose by how much attention the aside deserves.
""",
                    "The answer — and nobody expected this — was yes, although the report (published in 2019) says otherwise.",
                ),
            ],
        ),
        4: _m(
            "Punctuation for Effect",
            "Use punctuation as a rhetorical instrument, not just a rulebook.",
            [
                _l(
                    "Rhythm and Pacing",
                    "Control reading speed through punctuation choice.",
                    """
Punctuation is the score for the reader's inner voice.

- **Full stops** slow the reader. Short. Sentences. Force. Pauses.
- **Commas** create a light lift.
- **Semicolons** hold two ideas in tension without releasing.
- **Colons** create anticipation, then deliver.
- **Dashes** break the rhythm entirely — which is exactly why they work sparingly.

A paragraph punctuated entirely with commas reads as a single breathless run.
Varying the marks varies the pace, and pace is most of what readers experience as
"good writing".
""",
                    "Full stops slow the reader; commas lift; a dash — used rarely — breaks the rhythm entirely.",
                ),
                _l(
                    "Punctuating Complex Lists and Citations",
                    "Handle nested and technical punctuation confidently.",
                    """
**Nested quotations** - alternate double and single marks:

> She said, "He described it as 'entirely predictable', which surprised me."

**Quoting inside a sentence** - punctuation follows the sentence's grammar, not the
quotation's:

> He called the plan "ambitious", then voted against it.

**Bulleted lists** - be consistent. Either every item ends with a semicolon and the
last with a full stop, or none carry terminal punctuation at all. Mixing the two
within one list is the visible error.
""",
                    "She said, \"He described it as 'entirely predictable', which surprised me.\"",
                ),
                _l(
                    "Common Professional Errors",
                    "Eliminate the punctuation mistakes that undermine formal writing.",
                    """
**The five that most often reach a published document**

1. **Comma splice** - "The deadline passed, we filed anyway." Use a semicolon or a
   full stop.
2. **Rogue apostrophe in decades** - *1990's* should be *1990s*.
3. **Hyphen vs en dash** - hyphens join words (*well-known*); en dashes mark ranges
   (*2019–2024*).
4. **Missing comma before a name in direct address** - "Thanks Priya" vs "Thanks,
   Priya."
5. **Space before punctuation** - never in English, though it is standard in French.

Each is small. Together they are what a careful reader registers as sloppiness.
""",
                    "The deadline passed; we filed anyway, and the 1990s data was well-known by then.",
                ),
            ],
        ),
        5: _m(
            "Editorial Standards",
            "Apply and defend a consistent house style.",
            [
                _l(
                    "Style Guides and Consistency",
                    "Work within an established editorial standard.",
                    """
Above the level of rules sits **convention**, and convention varies by house.
Oxford comma or not; *-ise* or *-ize*; numerals from ten or from one hundred. None
of these is right or wrong.

**What matters is consistency.** A document that switches conventions halfway
reads as unedited even when every individual choice is defensible.

**Practical approach:** pick a guide (Oxford, Chicago, AP, or your organisation's),
note the five or six points where it differs from your instinct, and keep that short
list beside you. You will not memorise a style guide; you only need the deltas.
""",
                    "Pick a style guide, note the handful of points where it differs from your instinct, and keep that list beside you.",
                ),
                _l(
                    "Punctuation in Technical and Legal Writing",
                    "Handle contexts where punctuation carries legal or logical weight.",
                    """
In most prose, a misplaced comma is an inelegance. In a contract or specification,
it is a liability.

> "No person shall drive, park or leave standing any vehicle."

Whether *standing* attaches to *leave* alone or to the whole series changes what is
prohibited. Real contract disputes have turned on exactly this.

**Defensive practices**

- Prefer numbered sub-clauses to long comma-separated series.
- Repeat the operative verb in each branch rather than relying on the reader to
  distribute it.
- Where a series could be read two ways, restructure - do not just add a comma.
""",
                    "Prefer numbered sub-clauses to long comma-separated series, and repeat the operative verb in each branch.",
                ),
                _l(
                    "Proofreading Systematically",
                    "Catch punctuation errors reliably rather than by luck.",
                    """
You cannot proofread by reading normally - your brain supplies what should be there.

**Techniques that actually work**

1. **Read backwards**, sentence by sentence. This destroys the meaning-flow that
   causes you to skim.
2. **Change the medium** - print it, or change the font. Novelty restores attention.
3. **Single-error passes** - one pass for apostrophes only, one for commas only.
   Looking for everything finds nothing.
4. **Read aloud** for rhythm errors; **search** for mechanical ones (`" "`, ` ,`,
   `..`).
5. **Leave it overnight** if you can. Nothing else recovers this much accuracy.
""",
                    "Read it backwards, change the font, do one pass per error type, and leave it overnight if you can.",
                ),
            ],
        ),
    },
    # ------------------------------------------------------------------ #
    "Spelling": {
        1: _m(
            "Sounds and Letters",
            "Spell common words by matching sounds to reliable letter patterns.",
            [
                _l(
                    "Common Sound Patterns",
                    "Use predictable letter combinations to spell everyday words.",
                    """
English spelling is irregular, but far from random. Some patterns hold most of the
time.

| Sound | Usual spelling | Examples |
|---|---|---|
| /ee/ | ee, ea | tree, seed, read, meat |
| /ay/ | ai, ay | rain, train, day, play |
| /oa/ | oa, ow | boat, road, slow, grow |
| /oo/ | oo | food, moon, book |

**Pattern within the pattern:** *ai* and *oa* usually sit in the middle of a word;
*ay* and *ow* usually sit at the end.
""",
                    "The train came down the road in the rain, and we played all day.",
                ),
                _l(
                    "The Silent E",
                    "Understand how a final e changes the vowel before it.",
                    """
A silent **e** at the end of a word makes the vowel before it say its own name.

| Short | Long |
|---|---|
| hat | hate |
| pin | pine |
| not | note |
| cut | cute |

Same letters, one extra **e**, entirely different word. This one rule accounts for a
large share of spelling confusion at this level, and it is worth over-practising.
""",
                    "He put on his hat, then wrote a note with a fine pen.",
                ),
                _l(
                    "Making Words Plural",
                    "Add plural endings correctly.",
                    """
- Most words: add **-s**. *book → books*
- Ending in s, x, ch, sh: add **-es**. *box → boxes, watch → watches*
- Consonant + y: change y to **i** and add -es. *baby → babies* (but *day → days*,
  because there is a vowel before the y)
- Some f endings: change to **v**. *leaf → leaves, knife → knives*

**Irregulars to memorise:** child → children, person → people, foot → feet,
tooth → teeth, mouse → mice.
""",
                    "The children carried boxes of leaves and put them under the trees.",
                ),
            ],
        ),
        2: _m(
            "Spelling Rules That Hold",
            "Apply the reliable rules for endings and doubling.",
            [
                _l(
                    "I Before E",
                    "Apply the rule and know when it fails.",
                    """
*I before E, except after C, when the sound is /ee/.*

- **ie:** believe, achieve, field, piece, relief
- **cei:** receive, ceiling, deceive, receipt

The rhyme only applies to the /ee/ sound. When the sound is /ay/, it is **ei**:
*eight, weight, neighbour, vein*.

**Genuine exceptions worth memorising:** *weird, seize, protein, caffeine, their,
foreign, science.*
""",
                    "I believe you will receive the receipt from your foreign neighbour by Friday.",
                ),
                _l(
                    "Doubling Consonants",
                    "Know when to double a final consonant before adding an ending.",
                    """
Double the final consonant when **all three** are true:

1. the word ends consonant-vowel-consonant,
2. the last syllable is stressed,
3. the ending starts with a vowel (*-ing, -ed, -er*).

- *run → run**n**ing*, *stop → sto**pp**ed*, *begin → begi**nn**ing* ✓
- *visit → visited* (stress on VIS-it, not the last syllable) ✗
- *open → opening* ✗

British English adds one exception: final **l** always doubles - *travel → travelled*,
*cancel → cancelled*. American English does not.
""",
                    "We stopped running and began travelling, but the meeting was cancelled.",
                ),
                _l(
                    "Adding Endings to Words in E and Y",
                    "Handle the two commonest ending changes.",
                    """
**Words ending in silent e** - drop the e before a vowel ending, keep it before a
consonant ending:

> hope → hoping, hoped *but* hopeful
> use → using, usable *but* useless

**Words ending in y** - consonant + y becomes i:

> happy → happier, happiness
> carry → carried, carries

Keep the y before **-ing**, always: *carry → carrying*, *study → studying*. Two i's
never sit together in English.
""",
                    "She was hoping to study, and carrying the books made her happier.",
                ),
            ],
        ),
        3: _m(
            "Confusables and Homophones",
            "Spell words that sound alike but differ in meaning.",
            [
                _l(
                    "The Big Three",
                    "Master their/there/they're, your/you're and its/it's.",
                    """
These three account for more spelling complaints than everything else combined -
and each has a one-second test.

| Word | Means | Test |
|---|---|---|
| **their** | belonging to them | swap in *our* |
| **there** | that place | contains *here* |
| **they're** | they are | expand it |
| **your** | belonging to you | swap in *my* |
| **you're** | you are | expand it |
| **its** | belonging to it | swap in *his* |
| **it's** | it is / it has | expand it |

> They're putting their bags over there.
""",
                    "They're putting their bags over there, and it's your turn to carry yours.",
                ),
                _l(
                    "Frequently Confused Pairs",
                    "Distinguish word pairs that spell-check will not catch.",
                    """
A spell-checker accepts every one of these, because each is a real word.

| Pair | Distinction |
|---|---|
| affect / effect | *affect* is usually the verb, *effect* the noun |
| accept / except | receive / leave out |
| principal / principle | the head person or main / a rule or belief |
| stationary / stationery | not moving / paper and pens |
| complement / compliment | completes / praises |
| lose / loose | mislay / not tight |
| advice / advise | the noun / the verb |

**Memory hook:** stationERy has an E for envelope; the princiPAL is your PAL.
""",
                    "The principal gave sound advice about the effect the new principle would have.",
                ),
                _l(
                    "British and American Spelling",
                    "Recognise both conventions and apply one consistently.",
                    """
| British | American |
|---|---|
| colour, favour | color, favor |
| centre, metre | center, meter |
| realise, organise | realize, organize |
| travelled, cancelled | traveled, canceled |
| defence, licence (n.) | defense, license |
| programme (TV) | program |

Neither is more correct. What matters is picking one per document. Indian English
generally follows British conventions, so *colour* and *centre* are the safer
default here - but set your word processor's language accordingly, because it will
otherwise quietly enforce the other.
""",
                    "I realised the colour of the centre panel had not been catalogued correctly.",
                ),
            ],
        ),
        4: _m(
            "Advanced Orthography",
            "Spell technical, borrowed and morphologically complex words.",
            [
                _l(
                    "Words With Silent Letters",
                    "Spell words whose pronunciation hides letters.",
                    """
Silent letters are usually fossils of an older pronunciation or a borrowed spelling.

| Silent | Words |
|---|---|
| b | debt, subtle, doubt, plumber |
| g | sign, foreign, campaign, gnaw |
| h | honest, rhythm, exhaust, ghost |
| p | receipt, psychology, pneumonia |
| c | scissors, muscle, science |

**The useful trick:** the letter often reappears in a related word, which anchors
the spelling. *Sign* → *signature*. *Muscle* → *muscular*. *Debt* → *debit*.
""",
                    "The plumber had no doubt about the subtle sign of exhaust in the foreign campaign.",
                ),
                _l(
                    "Suffix Choices",
                    "Choose between endings that sound identical.",
                    """
**-able vs -ible** - *-able* attaches to complete words (*comfort → comfortable*),
*-ible* to Latin roots that cannot stand alone (*poss- → possible*). Roughly 80%
reliable.

**-ance vs -ence** - usually follows the related adjective: *important → importance*,
*different → difference*.

**-tion / -sion / -cion** - *-tion* is the default; *-sion* follows d, s or l
(*decide → decision*, *expand → expansion*); *-cion* appears in only a handful of
words (*suspicion*, *coercion*).

Where the rule is uncertain, check. These are the errors that survive proofreading
because they look plausible.
""",
                    "The difference in his decision was noticeable, and the expansion remained possible.",
                ),
                _l(
                    "Borrowed and Technical Words",
                    "Spell loanwords and specialist terms accurately.",
                    """
English borrows spellings along with words, and the source language's rules come
with them.

- **French:** silent endings and *-eau*, *-oir* - *bureau, liaison, rendezvous,
  repertoire*
- **Greek:** *ph* for /f/, *rh*, *ch* for /k/ - *photograph, rhythm, chorus,
  psychology*
- **Latin:** plurals that are not -s - *criterion → criteria*, *phenomenon →
  phenomena*, *analysis → analyses*

That last group is where educated writers most often slip. *A criteria* and *this
phenomena* are both wrong, and both common.
""",
                    "The analysis of that phenomenon met every criterion in the bureau's repertoire.",
                ),
            ],
        ),
        5: _m(
            "Orthographic Mastery",
            "Spell with near-total accuracy and diagnose your own residual errors.",
            [
                _l(
                    "Diagnosing Your Own Error Patterns",
                    "Find the small set of rules behind most of your mistakes.",
                    """
At this level you no longer have a spelling problem in general - you have three or
four specific ones, repeating.

**Method**

1. Collect 30 of your own spelling errors from real writing. Not a test - real work.
2. Classify each: doubling, suffix choice, homophone, loanword, typo.
3. You will almost certainly find that two categories account for most of them.
4. Drill *those* categories only.

The characteristic mistake at advanced level is studying spelling in general when
your actual errors cluster in one narrow rule.
""",
                    "Collect thirty of your own errors, classify them, and you will find two categories cover most of them.",
                ),
                _l(
                    "When Spell-Check Fails",
                    "Catch the errors automated tools cannot see.",
                    """
A spell-checker verifies that a string is *a* word, not that it is *the* word.
Everything below passes cleanly:

- real-word errors: *form* for *from*, *manger* for *manager*, *pubic* for *public*
- homophone errors: *complement* for *compliment*
- correct spelling of the wrong name: *Steven* for *Stephen*
- consistent misspelling added to your custom dictionary years ago

**Defences:** read proper nouns aloud letter by letter; search the document for your
own known problem words; never accept an autocorrect suggestion without reading it.
""",
                    "A spell-checker confirms that a string is a word, not that it is the right word.",
                ),
                _l(
                    "Spelling in Professional Contexts",
                    "Maintain accuracy under deadline and across document types.",
                    """
Accuracy at scale is a process problem.

**What holds up under pressure**

- **A project glossary** - product names, client names, technical terms, agreed
  spellings. Written down once, consulted by everyone.
- **A final names-and-numbers pass** - a dedicated pass that checks *only* proper
  nouns, figures, dates and URLs. These are where errors cost most and where
  meaning-driven reading is least reliable.
- **Second-reader rule** - anything going outside the organisation is read by
  someone who did not write it.
- **Templates** - correctly-spelled boilerplate that is never retyped.

The reason this matters is not pedantry: a misspelled client name signals
carelessness about everything else in the document.
""",
                    "Keep a project glossary, run a final pass on names and numbers, and never let your own work go out unread.",
                ),
            ],
        ),
    },
}


def module_spec(skill: str, band: int) -> ModuleSpec:
    """Fetch content for a skill/band, falling back to the nearest available band."""
    by_band = CONTENT.get(skill)
    if not by_band:
        # Unknown skill tag: fall back to Reading Comprehension at the same band.
        by_band = CONTENT["Reading Comprehension"]
    if band in by_band:
        return by_band[band]
    nearest = min(by_band.keys(), key=lambda b: abs(b - band))
    return by_band[nearest]
