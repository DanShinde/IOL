window.onload = function() {
    var modForm = document.getElementById('module-form');
    var addBtn = document.getElementById('add-signals-btn');
    var exportBtn = document.getElementById('export-iolist-btn');

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    modForm.addEventListener('submit', function(event) {
        event.preventDefault();
        var module_id = document.getElementById('module').value;
        var url = this.dataset.url + '?module=' + module_id;
        var xhr = new XMLHttpRequest();
        xhr.open('GET', url);
        xhr.onload = function() {
            if (xhr.status === 200) {
                var signals = JSON.parse(xhr.responseText)['signals'];
                console.log(signals)
                var diSignalsContainer = document.getElementById('di-signals-container');
                var doSignalsContainer = document.getElementById('do-signals-container');
                diSignalsContainer.innerHTML = 'DI';
                doSignalsContainer.innerHTML = 'DO';
                if (signals.length > 0) {
                    for (var i = 0; i < signals.length; i++) {
                        var signal = signals[i];
                        var signalItem = document.createElement('div');
                        var checkbox = document.createElement('input');
                        checkbox.type = 'checkbox';
                        checkbox.name = 'signals';
                        checkbox.value = signal['id'];
                        if (signal['initial_state'] === true){
                            checkbox.checked = true;
                        }                        
                        // console.log(signal['code'])
                        // console.log(signal['initial_state'])
                        signalItem.appendChild(checkbox);
                        var label = document.createElement('label');
                        label.htmlFor = 'signal-' + signal['id'];
                        label.appendChild(document.createTextNode(signal['code']));
                        signalItem.appendChild(label);
                        if (signal['signal_type'] === 'DI') {
                            diSignalsContainer.appendChild(signalItem);
                        } else if (signal['signal_type'] === 'DO') {
                            doSignalsContainer.appendChild(signalItem);
                        }
                    }
                } else {
                    diSignalsContainer.innerHTML = 'No signals found.';
                    doSignalsContainer.innerHTML = 'No signals found.';
                }
            }
        };
        xhr.send();
    });

    addBtn.addEventListener('click', function(event) {
        event.preventDefault(); // prevent form from submitting normally
        var module_name = $("#module_name").val();
        var selectedSignals = $("input[name='signals']:checked").map(function(){
          return $(this).val();
        }).get();
        console.log(module_name)
        console.log("selecetd signals")
        console.log(selectedSignals)
        $.ajax({
          type: "POST",
          url: "/add_signals/",
          data: JSON.stringify({'signals': selectedSignals, 'module_name': module_name }),
          dataType: "json",
          contentType: "application/json; charset=utf-8",
          headers: {"X-CSRFToken": getCookie("csrftoken")},
          success: function(response) {
            console.log("Selected signals sent to server.");
            var ioListTable = document.getElementById('io-list-table');
        ioListTable.innerHTML = '';
        var ioListData = JSON.parse(response.data);
        for (var i = 0; i < ioListData.length; i++) {
          var ioListRow = ioListTable.insertRow();
          var ioListFields = ioListData[i].fields;
          ioListRow.insertCell().innerHTML = i+1;
          ioListRow.insertCell().innerHTML = ioListFields['name'];
          ioListRow.insertCell().innerHTML = ioListFields['code'];
          ioListRow.insertCell().innerHTML = ioListFields['tag'];
          ioListRow.insertCell().innerHTML = ioListFields['signal_type'];
        }
      },
          error: function(xhr, status, error) {
            // handle error response
          }
        });
      });


      exportBtn.addEventListener('click', function(event) {
        xhttp = new XMLHttpRequest();
        var project= document.getElementById("projectName");

        projectName = project.textContent; 
        xhttp.onreadystatechange = function() {
            var a, today;
            if (xhttp.readyState === 4 && xhttp.status === 200) {
                a = document.createElement('a');
                a.href = window.URL.createObjectURL(xhttp.response);
                today = new Date();
                a.download = projectName +"_IO_List_R0"+ ".xls";
                a.style.display = 'none';
                document.body.appendChild(a);
                return a.click();
            }
        };
        xhttp.open("GET", "/toexcel", true);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.responseType = 'blob';
        xhttp.send();
    });
};