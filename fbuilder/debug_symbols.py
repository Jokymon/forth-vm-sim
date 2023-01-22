class WordCollection:
    def __init__(self):
        self.word_ranges = []

    def add_word(self, word, start, end):
        self.word_ranges.append( (word, start, end) )

    def clear(self):
        self.word_ranges.clear()

    def dump_to_file(self, file_path):
        with open(file_path, "w") as dump_file:
            for word_range in self.word_ranges:
                dump_file.write(f"{word_range[0]},{word_range[1]},{word_range[2]}\n")