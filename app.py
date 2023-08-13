from flask import Flask, render_template, redirect, request, session, abort, url_for
import jinja2 as jinja2
from flask_session import Session
import random
import string
import openai
import threading

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

def message_GPT(prompt):
    answer = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{
            "role": "user",
            "content": prompt}])
    
    answer = answer["choices"][0]["message"]["content"]
    return answer

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route("/", methods = ["POST", "GET"])
def index():
    if request.method == "POST":
        session["api_key"] = request.form.get("API key")
        session["user_prompt"] = request.form.get("description")

        if session["api_key"] is None or 

        return redirect("/first-website")
    else:
        return render_template("index.html")
    
@app.route("/first-website")
def generate_first_website():
    openai.api_key = session["api_key"]

    prompt_file  = open("./static/prompts/First HTML.txt")
    website_code = message_GPT(prompt_file.read() + session["user_prompt"])

    website_id = "".join(random.choices(string.ascii_letters + string.digits, k=25))

    website_file = open(f"./templates/generated-pages/{website_id}.html", "w")
    website_file.write(website_code)
    website_file.close

    return redirect(url_for(".access_website", id = website_id))

@app.route("/generated-website")
def access_website():
    website = request.args["id"]
    try:
        return render_template(f"/generated-pages/{website}.html")
    except jinja2.exceptions.TemplateNotFound:
        return abort(404)


if __name__ == "__main__":
    app.run("0.0.0.0", debug=True)