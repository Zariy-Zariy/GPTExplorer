let old_html = ""
document.addEventListener("click", function(event){
    let body = document.getElementsByTagName("body");
    old_html = body.innerHTML;
    body.innerHTML = "<p aria-busy='true'>Generating the webpage...</p>"
});

window.addEventListener("unload", function(){
    body.innerHTML = old_html
});