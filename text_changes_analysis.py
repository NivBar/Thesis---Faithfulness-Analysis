import re
from tqdm import tqdm
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable


def compare_texts_with_one_skip(text1, text2):
    words1 = text1.split()
    words2 = text2.split()

    # Direct comparison if lengths differ by more than 1, early return False
    if abs(len(words1) - len(words2)) > 1:
        return False

    # Function to check if two lists are equal allowing one skip
    def is_equal_with_one_skip(list1, list2):
        i, j = 0, 0
        skip_allowed = True
        while i < len(list1) and j < len(list2):
            if list1[i] == list2[j]:
                i += 1
                j += 1
            elif skip_allowed:
                skip_allowed = False
                if len(list1) > len(list2):
                    i += 1
                elif len(list1) < len(list2):
                    j += 1
                else:  # Equal length, try skipping from both, one should work
                    return is_equal_with_one_skip(list1[i + 1:], list2[j:]) or is_equal_with_one_skip(list1[i:],
                                                                                                      list2[j + 1:])
            else:
                return False
        return True

    return is_equal_with_one_skip(words1, words2)


def normalize_sentence(sentence):
    """Normalize sentences for comparison."""
    # Lowercase the sentence
    sentence = sentence.encode('utf-8').decode('utf-8').lower()
    # Remove punctuation
    sentence = re.sub(r'[^\w\s]', '', sentence)
    # Strip leading and trailing whitespace
    sentence = sentence.strip()
    return sentence


def compare_sentences(text1, text2):
    # Tokenize the texts into sentences
    sentences1 = [sentence.strip() for sentence in re.split(r'[.!?]', text1) if sentence.strip() != '']
    sentences2 = [sentence.strip() for sentence in re.split(r'[.!?]', text2) if sentence.strip() != '']

    # Normalize sentences
    normalized_sentences1 = [normalize_sentence(sentence) for sentence in sentences1]
    normalized_sentences2 = [normalize_sentence(sentence) for sentence in sentences2]

    # Compare normalized sentences and count matches
    matches = []

    for i, sentence in enumerate(normalized_sentences1):
        for j, sentence2 in enumerate(normalized_sentences2):
            if sentence == sentence2:
                matches.append((i, j))
                break
            if j == len(normalized_sentences2) - 1:
                for j, sentence2 in enumerate(normalized_sentences2):
                    if compare_texts_with_one_skip(sentence, sentence2):
                        matches.append((i, j))
                        break
                x = 1
    len_matches = len(matches)
    if len_matches == 0:
        x = 1
    # return f"{len_matches}/{len(normalized_sentences1)}", f"{len_matches}/{len(normalized_sentences2)}"
    return int(len(normalized_sentences1) - len_matches)


if __name__ == '__main__':
    # cp = 'test@F00'
    dfs = []
    cp_list = [f'test@F{ind}' for ind in ['00','02','05','10','12','15','20','22','25']]
    for cp in cp_list:
        print(cp)
        df = pd.read_csv(f'./TT_input/bot_followup_{cp}.csv').sample(frac=1)
        for idx, row in tqdm(df.iterrows(), total = df.shape[0]):
            changed = compare_sentences(row['text'], row['ref_doc'])
            df.at[idx, 'changed'] = changed
        # print(df.groupby('username')['changed'].mean())
        dfs.append(df.groupby('username')['changed'].mean().to_frame(cp))

        # Concatenate
    result_df = pd.concat(dfs, axis=1)
    normalized_df = result_df.apply(lambda x: (x - x.min()) / (x.max() - x.min()), axis=1)

    # Prepare the colormap
    cmap = plt.cm.coolwarm
    norm = Normalize(vmin=0, vmax=1)
    sm = ScalarMappable(cmap=cmap, norm=norm)

    # Plotting
    fig, ax = plt.subplots(figsize=(8, 3))  # Adjust the size as needed
    ax.axis('tight')
    ax.axis('off')
    the_table = ax.table(cellText=result_df.values, colLabels=result_df.columns,
                         rowLabels=result_df.index, cellLoc='center', loc='center')

    # Apply color to each cell based on normalized values
    for (i, j), val in np.ndenumerate(normalized_df.values):
        the_table[(i + 1, j)].set_facecolor(cmap(norm(val)))
        the_table[(i + 1, j)].set_text_props(text=f'{result_df.iloc[i, j]}')

    plt.show()