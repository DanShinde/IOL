
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

  // console.log(response)
  //                     var counter = 0;
  //                     var iolists = JSON.parse(response.iolists);
  //                     $.each(iolists, function(index, iolist) {
  //                       var row = tbody.find('tr[data-pk="' + iolist.pk + '"]');
  //                       row.find('.name').text(iolist.name);
  //                       row.find('.code').text(iolist.code);
  //                       row.find('.tag').text(iolist.tag);
  //                       row.find('.signal_type').text(iolist.signal_type);
  //                       row.find('.device_type').text(iolist.device_type);
  //                       row.find('.panel_number').text(iolist.panel_number);
  //                       row.find('.terminal_number').text(iolist.terminal_number);
  //                       row.find('.location').text(iolist.location);
  //                       row.find('.Cluster').text(iolist.Cluster);
  //                       row.find('.order').text(iolist.order);
  //                       row.find('.cluster_number').text(iolist.cluster_number);
  //                       counter+=1;
  //                       console.log(row.find('.order').text());
  //                   });