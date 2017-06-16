from pyknp import Juman
import sys
import wordnet_jp
import itertools
import unicodedata
import heapq
from collections import defaultdict

juman = Juman()

def len_mora(s):
    table = [ 'ぁ','ぃ','ぅ','ぇ','ぉ','ゃ','ゅ','ょ' ]
    return sum([1 for x in s if (x not in table)])

def is_yomigana(c):
    name = unicodedata.name(c)
    return name.startswith("KATAKANA") or name.startswith("HIRAGANA")

def get_yomi(s):
    return ''.join((x.yomi for x in juman.analysis(s)))

class Node:
    def __init__(self, index, midasi, yomi, prevs):
        self.index = index
        self.midasi = midasi
        self.yomi = yomi
        self.mora = len_mora(yomi)
        self.less_5 = []
        self.exact_5 = []
        self.less_7 = []
        self.exact_7 = []

        if self.mora < 5:
            self.less_5.append([self])
        elif self.mora == 5:
            self.exact_5.append([self])
        elif self.mora < 7:
            self.less_7.append([self])
        elif self.mora == 7:
            self.exact_7.append([self])

        for prev in prevs:
            for history in prev.less_5:
                l = sum((x.mora for x in history)) + self.mora
                if l < 5:
                    self.less_5.append(history + [self])
                elif l == 5:
                    self.exact_5.append(history + [self])
                elif l < 7:
                    self.less_7.append(history + [self])
                elif l == 7:
                    self.exact_7.append(history + [self])
            for history in itertools.chain(prev.less_5, prev.exact_5, prev.less_7):
                l = sum((x.mora for x in history)) + self.mora
                if l < 7:
                    self.less_7.append(history + [self])
                elif l == 7:
                    self.exact_7.append(history + [self])

def create_node(index, word, prev, current):
    morphemes = juman.analysis(word)
    yomi = ''.join((x.yomi for x in morphemes)) 
    midasi = ''.join((x.midasi for x in morphemes))
    if all((is_yomigana(x) for x in yomi)):
        node = Node(index,midasi,yomi,prev)
        current.append(node)

for line in sys.stdin.readlines():
#for line in [ '同情するなら金をくれ' ]:
    line = line.strip()
    #print("語\t読み\t品詞")
    nodes = [[Node(0,"","",[])]]
    morphemes = juman.analysis(line)
    for (i,m) in enumerate(morphemes):
        #print("{0}\t{1}\t{2}".format(m.midasi,m.yomi,m.hinsi))
        #print("mora = {0}".format(len_mora(m.yomi)))
        #print(wordnet_jp.getSynonym(m.midasi))
        synonyms = wordnet_jp.getSynonym(m.midasi).values()
        synonyms = set(itertools.chain.from_iterable(synonyms))
        synonyms.add(m.midasi)

        current = []

        #create_node(m.yomi,nodes[-1],current)
        for s in synonyms:
            create_node(i,s,nodes[-1],current)

        nodes.append(current)
    
    paths5 = [set() for _ in range(len(nodes)) ]
    paths7 = [set() for _ in range(len(nodes)) ]

    morphemes_5 = defaultdict(set) 
    morphemes_7 = defaultdict(set)

    for node in nodes:
        for n in node:
            for history in n.exact_5:
                morphemes_5[(history[0].index,history[-1].index + 1)].add(''.join(x.midasi for x in history))

            for history in n.exact_7:
                morphemes_7[(history[0].index, history[-1].index + 1)].add(''.join((x.midasi for x in history)))

    positions = [(False,False) for _ in range(len(nodes))]

    for (f,t) in morphemes_5.keys():
        if f == 0:
            _,e = positions[t]
            positions[t] = (True,e)
        if t == len(nodes) - 1:
            b,_ = positions[f]
            positions[f] = (b,True) 

    for ((f,t),v) in morphemes_7.items():
        if positions[f][0] and positions[t][1]:
            print(' '.join(morphemes_5[(0,f)]))
            print(' '.join(v))
            print(' '.join(morphemes_5[(t,len(nodes) - 1)]))

    print()

