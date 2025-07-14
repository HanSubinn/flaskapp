from flask import Flask, render_template, jsonify 
from flask_cors import CORS 
from dotenv import load_dotenv 
import os 
import requests 
import MySQLdb 
 
load_dotenv() 
 
app = Flask(__name__) 
CORS(app) 
 
def get_db_connection(): 
    return MySQLdb.connect( 
        user=os.getenv("DB_USER"), 
        passwd=os.getenv("DB_PASSWORD"), 
        host=os.getenv("DB_HOST"), 
        db=os.getenv("DB_NAME"), 
        charset='utf8' 
    ) 
 
@app.route("/") 
def index(): 
    return render_template("index.html") 
 
@app.route("/api/data") 
def api_data(): 
    response = requests.get("https://jsonplaceholder.typicode.com/todos/1") 
    return jsonify(response.json()) 
 
@app.route("/db") 
def db_test(): 
    conn = get_db_connection() 
    cursor = conn.cursor() 
    cursor.execute("SELECT 'Flask에서 MySQL 연결 성공!'") 
    result = cursor.fetchone() 
    conn.close() 
    return jsonify({"result": result[0]}) 
if __name__ == "__main__": 
    app.run(debug=True) 