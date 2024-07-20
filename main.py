import urllib
import json
import os
import requests
from flask import Flask, render_template, request, jsonify
import fitz  


def do():
 f = open("centres-data.json", "rb")
 data = f.read()
 js = json.loads(data)
 for state in js["states"]:
    state_name = state["name"]
    path1 = f"/home/runner/Loader/states/{state_name}"
    if not os.path.exists(path1):
     os.mkdir(path1)
    centre_codes = []
    for city in state["cities"]:
        city_name = city["name"].replace("/", ",")
        path2 = f"/states/{state_name}/{city_name}"
        if not os.path.exists(path2):
         os.mkdir(r"" + path2)
        for centre in city["centres"]:
            centre_code = centre["code"]
            url = f"https://neetfs.ntaonline.in/NEET_2024_Result/{centre_code}.pdf"
            path3 = f"/states/{state_name}/{city_name}/{centre_code}.pdf"
            if not os.path.exists(path3):
              urllib.request.urlretrieve(url, path3)
            yield                  


def chunk(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]

def extract_marks_from_pdf(path):
    pdf_document = fitz.open(path)
    data = {}
    for page in pdf_document:
        lines = page.get_text().split("\n")
        s = lines.index("Srlno. Marks") + 1
        lines = lines[s:-1]
        spl = []
        for line in lines:
            if line.strip() == "Srlno. Marks":
                continue
            spl.append(line.strip())

        for sp in list(chunk(spl, 2)):
            data[sp[0]] = sp[1]
    return data

def analyze_marks(data, min_mark, max_mark=720):
    data = {k: int(v) for k, v in data.items()}
    filtered_data = {
        k: v
        for k, v in data.items() if min_mark <= v <= max_mark
    }

    return len(filtered_data), filtered_data

app = Flask(__name__,template_folder="public")
f = open("centres-data.json", "rb")
data =json.loads(f.read()) 

@app.route("/")
def home():
    states = []
    for state in data["states"]:
        state_name = state["name"]
        states.append(state_name)
    return render_template('index.html', states=states)

@app.route('/get_cities', methods=['POST'])
def get_cities():

    sta = request.form['state']
    cities = ["ALL"]
    for state in data["states"]:
        state_name = state["name"]
        if sta == state_name:
            for city in state["cities"]:
                cities.append(city["name"])
    return jsonify(cities)

@app.route('/get_results', methods=['POST'])
def get_results():
    state_name = request.form['state']
    city_name = request.form['city'].replace("/", ",")
    if city_name== "ALL":
        directory = f"states/{state_name}/"
        paths = []
        for i in os.walk(directory):
         for j in i[2]:
          if j.endswith('.pdf'):
            paths.append( os.path.join(i[0], j))

    else:
        dir = f"states/{state_name}/{city_name}"

        paths = [
      os.path.join(dir, f)
        for f in sorted(os.listdir(dir)) if f.endswith(".pdf")
    ]
    #print(paths)
    min_mark = int(request.form['min_mark'])
    max_mark = int(request.form['max_mark'])
    NoOfStudents = 0
    for path in paths:
        no, d = analyze_marks(extract_marks_from_pdf(path), min_mark, max_mark)
        NoOfStudents += no


    return jsonify(count_in_range=NoOfStudents, min_mark=min_mark, max_mark=max_mark)


if __name__ == "__main__":
    app.run(
        '0.0.0.0', port=os.environ['PORT'])
