window.onload = function() {
    var exportBtn = document.getElementById('export-iolist-btn');
    var project= document.getElementById("projectName");
        console.log(project.textContent);
    
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

    //   exportBtn.addEventListener('click', function(event) {
    //     xhttp = new XMLHttpRequest();
    //     var project= document.getElementById("projectName");
    //     console.log(project.textContent);
    //     projectName = project.textContent; 
    //     xhttp.onreadystatechange = function() {
    //         var a, today;
    //         if (xhttp.readyState === 4 && xhttp.status === 200) {
    //             a = document.createElement('a');
    //             a.href = window.URL.createObjectURL(xhttp.response);
    //             today = new Date();
    //             a.download = projectName +"_IO_List_R0"+ ".xls";
    //             a.style.display = 'none';
    //             document.body.appendChild(a);
    //             return a.click();
    //         }
    //     };
    //     xhttp.open("GET", "/toexcel", true);
    //     xhttp.setRequestHeader("Content-Type", "application/json");
    //     xhttp.responseType = 'blob';
    //     xhttp.send();
    // });
};

// 