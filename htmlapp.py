from flask import Flask, render_template, request
import sqlite3
import plotly.graph_objs as go
import checkpoint as cp

app = Flask(__name__)
DB_NAME = "drugs_utility.sqlite"


def load_data_for_plot(q):
    if q[0] == "PrescriptionCount" :
        x_y_sql = ''' SELECT State, SUM(PrescriptionCount)
                  FROM StateUtilization2018
                    JOIN DrugMolecules
                      ON StateUtilization2018.ProductId = DrugMolecules.Id
                  WHERE (Quarter=?) AND (DrugMolecules.Name=?) AND (State != "XX")
                  GROUP BY State
            '''
    elif q[0] == "UnitsReimbursed": 
        x_y_sql = ''' SELECT State, SUM(UnitsReimbursed)
                  FROM StateUtilization2018
                    JOIN DrugMolecules
                      ON StateUtilization2018.ProductId = DrugMolecules.Id
                  WHERE (Quarter=?) AND (DrugMolecules.Name=?) AND (State != "XX")
                  GROUP BY State
            '''
    elif q[0] == "AmountReimbursed" :
        x_y_sql = ''' SELECT State, SUM(AmountReimbursed)
                  FROM StateUtilization2018
                    JOIN DrugMolecules
                      ON StateUtilization2018.ProductId = DrugMolecules.Id
                  WHERE (Quarter=?) AND (DrugMolecules.Name=?) AND (State != "XX")
                  GROUP BY State
            '''
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    results = cur.execute(x_y_sql, q[1:]).fetchall()
    x_vals = [x[0] for x in results]
    y_vals = [y[1] for y in results]
    conn.close()
    return (x_vals, y_vals)

def check_database(drug_name) :
    q = ''' SELECT COUNT(*)
            FROM StateUtilization2018
            JOIN DrugMolecules
                ON StateUtilization2018.ProductId = DrugMolecules.Id
            WHERE DrugMolecules.Name = ?
            '''
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    result = cur.execute(q, [drug_name]).fetchall()
    print(result)
    if result[0][0] > 0 :
        return True
    else :
        return False


@app.route('/')
def index() :
    return render_template('index.html')


@app.route('/results', methods=['POST'])
def results() :
    drug_name = request.form['drug_name'].lower()

    if request.form['choice'] == 'choice1' :
        try :
            properties = cp.get_physical_properties(drug_name)
        except : 
            return render_template('nophysicochemical.html', name=drug_name)
        pic_url = cp.get_molecular_picture(drug_name)
        print(properties)
        property_key_list = ["MolecularWeight", "MolecularFormula", "XLogP",
                             "TPSA", "HBondDonorCount", "HBondAcceptorCount",
                             "RotatableBondCount"]
        variable_list = [None, None, None, None, None, None, None]
        for i in range(len(property_key_list)):
            if property_key_list[i] in properties.keys() :
                variable_list[i] = properties[property_key_list[i]]
        return render_template('physicochemical.html', name=drug_name, url=pic_url,
                    formula=variable_list[1], mw=variable_list[0], xlogp=variable_list[2], 
                    tpsa=variable_list[3], hbd=variable_list[4], hba=variable_list[5], rb=variable_list[6])
            
    elif request.form["choice"] == 'choice2' :
        rxcui = cp.get_rxcui(drug_name)
        if rxcui is not None :
            products = cp.get_products(rxcui).items()
            symptoms = cp.get_howandwhat(rxcui)["symptoms"]
            mechanisms = cp.get_howandwhat(rxcui)["mechanisms"]
        else : 
            return render_template('nophysicochemical.html', name=drug_name)
        return render_template("generic.html", name=drug_name, products=products, symptoms=symptoms,
            mechanisms=mechanisms)

    elif request.form["choice"] == "choice3" :
        warnings = cp.get_new_warning(drug_name)
        return render_template("warnings.html", name=drug_name, warnings=warnings)

    elif request.form["choice"] == "choice4" :
        if check_database(drug_name) :
            return render_template("plot_option.html", name=drug_name)
        else :
            return render_template('nophysicochemical.html', name=drug_name)


@app.route('/results/plot', methods=['POST'])       
def plot() :
    drug_name = request.form["drug_name"].lower()
    info = request.form["info"]
    quarter = request.form["quarter"]
    q = [info, int(quarter), drug_name]
    x_vals, y_vals = load_data_for_plot(q)
    if len(x_vals) != 0 :
        bars_data = go.Bar(x=x_vals, y=y_vals)
        fig = go.Figure(data=bars_data)
        div = fig.to_html(full_html=False)
    else :
        div = False
    return render_template("plot.html", name=drug_name, info=info, quarter=quarter, plot_div=div)


if __name__ == '__main__':
    app.run(debug=True)
