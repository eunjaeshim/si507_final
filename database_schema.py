import sqlite3
import csv

DB_NAME = 'drugs_utility.sqlite'

def create_db() :
    ''' Creates database from drugbank data and state drug utilization 2018 data.

    Parameters
    ----------
    None

    Returns
    -------
    None
    '''

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    drop_drugs_sql = 'DROP TABLE IF EXISTS "DrugMolecules"'
    drop_utilization_sql = 'DROP TABLE IF EXISTS "StateUtilization2018"'

    create_drugs_sql = '''
        CREATE TABLE IF NOT EXISTS "DrugMolecules" (
            "Id"            INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
            "Name"          TEXT NOT NULL,
            "DrugGroups"    TEXT NOT NULL
        )
    '''
    
    create_utilization_sql = '''
        CREATE TABLE IF NOT EXISTS "StateUtilization2018" (
            "Id"                INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
            "Quarter"           INTEGER NOT NULL,
            "State"             TEXT NOT NULL,
            "ProductId"         INTEGER,
            "UnitsReimbursed"   REAL NOT NULL,
            "AmountReimbursed"   REAL NOT NULL,
            "PrescriptionCount" REAL NOT NULL
        )
    '''

    cur.execute(drop_drugs_sql)
    cur.execute(drop_utilization_sql)
    cur.execute(create_drugs_sql)
    cur.execute(create_utilization_sql)
    conn.commit()
    conn.close()


def load_drugs() :
    file_contents = open('structure_links.csv', 'r')
    csv_reader = csv.reader(file_contents)
    next(csv_reader)

    insert_drug_sql = '''
        INSERT INTO DrugMolecules
        VALUES (NULL, ?, ?)
    '''

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    #counter = 0

    for row in csv_reader : 
        cur.execute(insert_drug_sql, [row[1].lower(),row[3]])
        #counter += 1
        #if counter == 500 : break  

    conn.commit()
    conn.close()


def load_utilization() :
    file_contents = open('State_Drug_Utilization_Data_2018.csv', 'r')
    csv_reader = csv.reader(file_contents)
    next(csv_reader)

    select_drugname_sql = '''
            SELECT Name FROM DrugMolecules
        '''

    select_drug_id_sql = '''
            SELECT Id FROM DrugMolecules
            WHERE Name = ?
        '''

    insert_utility_sql = '''
            INSERT INTO StateUtilization2018
            VALUES (NULL, ?, ?, ?, ?, ?, ?)
        '''

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    #counter = 0
    cur.execute(select_drugname_sql)
    names = [x[0] for x in cur.fetchall()]

    for row in csv_reader :
        if row[7].lower() not in names :
            continue
        else : 
            # get Id for drug product
            cur.execute(select_drug_id_sql, [row[7].lower()])
            res = cur.fetchone()
            product_id = None
            if res is not None :
                product_id = res[0]
            if row[6] == "XX" :
                continue
            cur.execute(insert_utility_sql, [
                row[6], #State
                row[1], #Quarter
                product_id, 
                row[9], #Units Reimbursed
                row[10], #Number of prescriptions
                row[11] # Amount reimbursed
            ])
            #counter += 1
            #if counter == 500 : break #TODO : will need to erase this

    conn.commit()
    conn.close()


if __name__ == '__main__':
    create_db()
    load_drugs()
    load_utilization()
