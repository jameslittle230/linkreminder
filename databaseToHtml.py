import os
import database


def generateHeaderRowFromKeys(keys):
    return '<thead><tr>' + \
        ''.join(list(map(lambda x: f"<th>{x}</th>", keys))) + '</tr></thead>'


def generateRowFromEntry(entry, keys):
    def maketd(key, entry):
        if key not in entry:
            return "<td>...</td>"
        if key != "href":
            return f"<td>{str(entry[key])[:32]}</td>"
        if key == "href":
            return f"<td><a href=\"{entry[key]}\">{str(entry[key])[:32]}</a></td>"

    return '<tr>' + ''.join(list(map(lambda k: maketd(k, entry), keys))) + "</tr>"


def generateHtml(database):
    keys = []
    keys_lists = list(map(lambda x: x.keys(), database.data))
    for keys_list in keys_lists:
        for key in keys_list:
            if key not in keys:
                keys.append(key)

    headerRow = generateHeaderRowFromKeys(keys)

    sortedData = sorted(database.data, key=lambda x: x["punt_until"])

    rows = '\n'.join(
        list(map(lambda e: generateRowFromEntry(e, keys), sortedData)))

    filedir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(filedir, 'tabletemplate.html')) as f:
        template = f.read()
        template = template.replace("(TABLE)", headerRow + rows)

        output_path = os.path.join(filedir, 'output.html')
        with open(output_path, 'w') as output_f:
            output_f.write(template)
            return output_path
