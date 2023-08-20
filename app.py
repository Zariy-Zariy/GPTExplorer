from flask import Flask, render_template, redirect, request, session, abort, url_for
import jinja2 as jinja2
from flask_session import Session
import random
import string
import openai
import os
import threading
import shutil
import bs4
from time import sleep

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

def generate_webpage(api_key, instructions_html, user_input_html, instructions_css, timebomb_seconds = 5 * 60):
    website_id = "".join(random.choices(string.ascii_letters, k=25))
    website_path = f"./static/generated-pages/{website_id}"

    website_creator = GPT_to_file(instructions= instructions_html,
                                user_input= user_input_html, api_key= api_key, file_path=f"{website_path}/page.html")

    css_creator = GPT_to_file(instructions= instructions_css,
                                user_input= user_input_html, api_key= api_key, file_path=f"{website_path}/style.css")

    timebomb_function = threading.Thread(target=timebomb_folder, args=(website_path, timebomb_seconds,))
    timebomb_function.start()

    if website_creator.startswith("Error: "):
        return website_creator
    
    if css_creator.startswith("Error: "):
        return css_creator
    
    with open(f"{website_path}/page.html") as website:
        website_modifier = bs4.BeautifulSoup(website)

    css_link = website_modifier.new_tag("link", rel="stylesheet", type="text/css", href=f"{website_path}/style.css")

    website_modifier.head.append(css_link)
    link_tags = website_modifier.find_all("webpage")
    for link_tag in link_tags:
        new_tag = website_modifier.new_tag("a")
        new_tag.string = link_tag.string
        new_tag["href"] = f"./next-page?text={new_tag.string}&old-id={website_id}"

        link_tag.replace_with(new_tag)

    image_tags = website_modifier.find_all("image")
    for image_tag in image_tags:
        image_url = generate_image(api_key=api_key, prompt= str(image_tag.string))  
        print(image_tag.string)
        if image_url.startswith("Error: "):
            return image_url

        new_tag = website_modifier.new_tag("img")
        new_tag["src"] = image_url
        new_tag["alt"] = str(image_tag.string)

        image_tag.replace_with(new_tag)

    with open(f"{website_path}/page.html", "w") as website:
        website.write(str(website_modifier))

    return website_id

def message_GPT(instructions, user_prompt, api_key, temperature = 0.4):
    openai.api_key = api_key
    try:
        answer = openai.ChatCompletion.create(model="gpt-3.5-turbo", temperature = temperature, messages=[
            {
                "role": "system",
                "content": instructions
            },
            {
                "role": "user",
                "content": user_prompt
            }])
        
    except openai.error.AuthenticationError:
        return "Error: Authentication Error"
    
    except openai.error.Timeout:
        return "Error: The API timed out"
    
    except openai.error.APIError as e:
        return f"Error: OpenAI returned an error {e}"
    
    except openai.error.APIConnectionError:
        return "Error: The website failed to connect to OpenAI"
    
    except openai.error.InvalidRequestError:
        return "Error: The request was invalid"    
    
    except openai.error.PermissionError:
        return "Error: The request was not permitted"
    
    except openai.error.RateLimitError:
        return "Error: You exceeded your rate limit"
    
    answer = answer["choices"][0]["message"]["content"]
    return answer

def timebomb_folder(folder_path, duration):
    sleep(duration)
    shutil.rmtree(folder_path)

def GPT_to_file(file_path, instructions, user_input, api_key):
    
    output = message_GPT(instructions= instructions, user_prompt= user_input, api_key= api_key)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if output.startswith("Error:"):
        return output

    with open(file_path, "w") as output_file:
        output_file.write(output)

    return output

def generate_image(api_key, prompt):
    openai.api_key = api_key
    try:
        image = openai.Image.create(
            prompt= prompt,
            n=1,
            size="256x256"
        )
        
    except openai.error.AuthenticationError:
        return "Error: Authentication Error"
    
    except openai.error.Timeout:
        return "Error: The API timed out"
    
    except openai.error.APIError as e:
        return f"Error: OpenAI returned an error {e}"
    
    except openai.error.APIConnectionError:
        return "Error: The website failed to connect to OpenAI"
    
    except openai.error.InvalidRequestError:
        return "Error: The request was invalid"    
    
    except openai.error.PermissionError:
        return "Error: The request was not permitted"
    
    except openai.error.RateLimitError:
        return "Error: You exceeded your rate limit"
    
    image = image["data"][0]["url"]
    return image

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route("/", methods = ["POST", "GET"])
def index():
    if request.method == "POST":
        session["api_key"] = request.form.get("API key")
        session["user_prompt"] = request.form.get("description")

        if session["api_key"] is None:
            return redirect(url_for(".index", error = "API key not provided"))
        
        if session["user_prompt"] is None:
            return redirect(url_for(".index", error = "User prompt not provided"))

        return redirect("/first-webpage")
    else:           
        try:    
            return render_template("index.html", error = request.args["error"])
        except KeyError:
            return render_template("index.html")
    
@app.route("/first-webpage")
def generate_first_webpage():

    with open("./static/prompts/First HTML.txt") as html_prompt_file, open("./static/prompts/CSS.txt") as css_prompt_file:
        website = generate_webpage(api_key= session["api_key"], instructions_html= html_prompt_file.read(), user_input_html= session["user_prompt"],
                                    instructions_css= css_prompt_file.read())
    if website.startswith("Error:"):
        website = website.removeprefix("Error: ")
        return redirect(url_for(".index", error = website))

    return redirect(url_for(".access_webpage", id = website))

@app.route("/next-page")
def next_page():
    try:
        button_text = request.args["text"]
        old_id = request.args["old-id"]
    except KeyError:
        abort(422)

    try:
        with open(f"./static/generated-pages/{old_id}/page.html") as old_page, open("./static/prompts/Next HTML.txt") as instructions_HTML_file, open("./static/prompts/CSS.txt") as instructions_CSS_file:
            website = generate_webpage(api_key= session["api_key"],
                                        instructions_html= instructions_HTML_file.read(), 
                                        user_input_html= f"{old_page.read()} + Clicked '{button_text}'", 
                                        instructions_css= instructions_CSS_file.read())
    except OSError:
        abort(404)
     
    if website.startswith("Error:"):
        website = website.removePrefix("Error: ")
        return redirect(url_for(".index"), error = website)

    return redirect(url_for(".access_webpage", id = website))

@app.route("/generated-webpage")
def access_webpage():
    website_id = request.args["id"]
    website_path = f"./static/generated-pages/{website_id}/page.html"
    try:
        with open(website_path) as website:
            return website.read()
    except jinja2.exceptions.TemplateNotFound:
        return abort(404)
    


if __name__ == "__main__":
    app.run("0.0.0.0", debug=True)