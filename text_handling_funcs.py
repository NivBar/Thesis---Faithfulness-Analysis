import re


def remove_sentences_second(sentences):
    # Calculate the initial total number of words
    total_words = sum(len(sentence.split()) for sentence in sentences)

    # Check if total_words is already within the desired range or below 120
    if total_words <= 150:
        return sentences

    # Find and remove a sentence if total_words can be adjusted within the desired range
    while total_words > 150:
        for sentence in sorted(sentences, key=len):
            # Calculate the updated total number of words without the current sentence
            updated_total_words = total_words - len(sentence.split())
            if updated_total_words <= 150:
                total_words = updated_total_words
                sentences.remove(sentence)
                return sentences

        # Remove the shortest sentence if no sentence can be removed to meet the desired range or below 120
        if total_words > 150:
            shortest_sentence = min(sentences, key=lambda sentence: len(sentence))
            sentences.remove(shortest_sentence)
            total_words = total_words - len(shortest_sentence.split())
    return sentences


def count_words_complete_sentences(text):
    # Split the text into sentences using a regex pattern
    sentences = re.split(r'(?<=[.!?])\s+|\n', text)

    # Check if the last sentence is incomplete and remove it if necessary
    if sentences and sentences[-1].strip() and sentences[-1].strip()[-1] not in ['.', '!', '?']:
        sentences.pop()

    sentences_second = sentences.copy()

    # Check if truncation is necessary
    if sentences:
        word_count = sum(len(sentence.split()) for sentence in sentences)
        truncated_text = " ".join(sentences)

        while word_count > 150:
            if len(sentences) < 2:
                break
            sentences.pop()
            truncated_text = ' '.join(sentences)
            word_count = sum(len(sentence.split()) for sentence in sentences)

        if word_count < 120:
            # second try (less preferred)
            word_count_second = sum(len(sentence.split()) for sentence in sentences_second)
            sentences_second = remove_sentences_second(sentences_second)
            truncated_text_second = ' '.join(sentences_second)
            word_count_second_new = sum(len(sentence.split()) for sentence in sentences_second)
            # print(f"second try initiated, word counts - orig: {word_count_second}, new: {word_count_second_new}")

            if word_count_second_new >= 120 and word_count_second_new <= 150:
                return word_count_second_new, truncated_text_second + "." if truncated_text_second[
                                                                                 -1] != "." else truncated_text_second, True
            if word_count < 120:
                return len(text.split()), text, False

        if word_count >= 120 and word_count <= 150:
            return word_count, truncated_text + "." if truncated_text[-1] != "." else truncated_text, True

    # All sentences are complete
    word_count = len(text.split())
    return word_count, text, False
