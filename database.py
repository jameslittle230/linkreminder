import os
import pickle
import codecs


class Database:

    filename = None
    data = None

    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        self.data = []
        try:
            open(self.filename, 'x')
        except:
            pass
        finally:
            with open(self.filename) as db_file:
                for line in db_file:
                    self.data.append(self.deserialize(line))

    def write(self):
        with open(self.filename, 'w') as db_file:
            for entry in self.data:
                db_file.write(self.serialize(entry))
                db_file.write("\n")

    def entries(self):
        return self.data

    def insert(self, object):
        self.data.append(object)

    def update(self, myHash, replacement_object=None):
        filter_results = list(filter(lambda x: x["hash"] == myHash, self.data))
        if len(filter_results) > 1:
            raise "Hashes in database are not unique"
        if len(filter_results) == 1:
            self.data.remove(filter_results[0])
            if replacement_object != None:
                self.data.append(replacement_object)
        if len(filter_results) == 0:
            print("Trying to delete an item that isn't in the database.")

    def remove(self, myHash):
        self.update(myHash, None)

    def serialize(self, object):
        return ''.join(codecs.encode(pickle.dumps(object), "base64").decode().split('\n'))

    def deserialize(self, string):
        return pickle.loads(codecs.decode(string.encode(), "base64"))
