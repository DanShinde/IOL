function openSearchPopup() {
    document.getElementById("searchPopup").style.display = "block";
}

function closeSearchPopup() {
    document.getElementById("searchPopup").style.display = "none";
}

function filterResults(AllIos) {
    let input = document.getElementById("searchInput").value.toLowerCase();
    let resultsList = document.getElementById("searchResults");
    resultsList.innerHTML = ""; 

    let filtered = AllIos.filter(io => io.tag.toLowerCase().includes(input));

    filtered.forEach(io => {
        let button = document.createElement("button");
        button.textContent = io.tag;
        button.className = "search-result-btn";
        button.onclick = function () {  
            sendSelectedIO(io.id, selectedIOModule, this); // 'this' now refers to the button
        };
        resultsList.appendChild(button);
    });
}


function sendSelectedIO(ioId, currentIoModule, element) {
    fetch('/sort/update_iomoduleName/', {  // Adjust the endpoint URL as needed
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({ 
            io_id: ioId, 
            new_iomodule: currentIoModule 
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAutoAlert("IO Shifted: " + element.textContent);
            element.remove();  // Remove the button after selection
            // closeSearchPopup();
        } else {
            alert("Error: " + data.message);
        }
    })
    .catch(error => console.error("Error:", error));
}
