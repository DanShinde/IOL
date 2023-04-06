
function setActiveNavButton() {
    // Get all the buttons with class "nav-link" inside the element with id "nav-pills"
    var buttons = document.querySelectorAll(".nav-link");
    // Get the path of the current URL
    var path = window.location.pathname;
    
    // Loop through all the buttons
    for (var i = 0; i < buttons.length; i++) {
      // Get the href attribute of the button
      var href = buttons[i].getAttribute("onclick");
      // Check if the href attribute matches the current path
    if (href.includes(path)) {
        // If it is, add the "active" class to the button
        buttons[i].classList.add("active");
      } else {
        // If it's not, remove the "active" class from the button
        buttons[i].classList.remove("active");
      }
    }
  }
  



  window.onload = function() {
    setActiveNavButton(); 
  };