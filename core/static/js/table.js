const items = document.querySelectorAll(".item");
const tablesort = document.querySelectorAll(".tablesort");

items.forEach(item => {
    item.addEventListener("dragstart", () => {
        //Adding delay 
        setTimeout(() => item.classList.add("dragging"),0);
        setTimeout(() => item.classList.add("table-warning"),0);
    });

    //Removing dragging class after drop
    item.addEventListener("dragend", () => {
        item.classList.remove("dragging");
        item.classList.remove("table-warning");
    });
});

const initSortableList = (e) => {
    //Getting all items ecept current dragging and making array of them.
    const siblings = [...tablesort.querySelectorAll(".item:not(.dragging)")];

    let nextSibling = siblings.find(siblings => {
        return e.clientY <= siblings.offsetTop + sibling.offsetHeight/2;
    });
}
tablesort.addEventListener("dragover", initSortableList);