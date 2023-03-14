window.onload = function() {
    var modForm = document.getElementById('module-form');
    var addBtn = document.getElementById('add-signals-btn');

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
                var diSignalsContainer = document.getElementById('di-signals-container');
                var doSignalsContainer = document.getElementById('do-signals-container');
                diSignalsContainer.innerHTML = 'DI';
                doSignalsContainer.innerHTML = 'DO';
                console.log(signals);
                if (signals.length > 0) {
                    for (var i = 0; i < signals.length; i++) {
                        var signal = signals[i];
                        var signalItem = document.createElement('div');
                        var checkbox = document.createElement('input');
                        checkbox.type = 'checkbox';
                        checkbox.name = 'signals';
                        checkbox.value = signal['id'];
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
            // handle success response
          },
          error: function(xhr, status, error) {
            // handle error response
          }
        });
      });
    };
