// $(document).ready(function () {
//     console.log('DataTables is here')
//     $('#example').DataTable();
// });

// Set the initial value of #rowcount to the number of rows in the table
$(document).ready(function() {
    $("#rowcount").html($(".filterable tr").length - 1);
  
    // Add a click event listener to the .btn-filter element
    $(".filterable .btn-filter").click(function() {
      var table = $(this).parents(".filterable");
      var filters = table.find(".filters input");
      var tbody = table.find(".table tbody");
  
      if (filters.prop("disabled")) {
        // If filters are disabled, enable them and focus on the first input field
        filters.prop("disabled", false);
        filters.first().focus();
      } else {
        // If filters are enabled, clear them and disable them
        filters.val("").prop("disabled", true);
        tbody.find(".no-result").remove();
        tbody.find("tr").show();
      }
  
      // Update the value of #rowcount to reflect the number of rows in the table
      $("#rowcount").html($(".filterable tr").length - 1);
    });
  
    // Listen for keyup events on the filter input fields
    $(".filterable .filters input").keyup(function(event) {
      // Ignore the Tab key
      if (event.keyCode === 9) return;
  
      var input = $(this);
      var value = input.val().toLowerCase();
      var table = input.parents(".filterable");
      var column = table.find(".filters th").index(input.parents("th"));
      var tbody = table.find(".table tbody");
      var rows = tbody.find("tr");
      var matches = rows.filter(function() {
        return $(this).find("td").eq(column).text().toLowerCase().indexOf(value) !== -1;
      });
  
      // Hide rows that don't match the search term and show rows that do match
      rows.hide();
      matches.show();
  
      // If there are no matching rows, add a "No result found" message to the table
      if (matches.length === 0) {
        tbody.prepend('<tr class="no-result text-center"><td colspan="' + table.find(".filters th").length + '">No result found</td></tr>');
      } else {
        tbody.find(".no-result").remove();
      }
  
      // Update the value of #rowcount to reflect the number of visible rows in the table
      $("#rowcount").html(rows.filter(":visible").length - 1);
  
      // Call the checkval() function
      checkval();
    });
  });
  
  // Define the checkval() function
  function checkval() {
    var visibleRows = $("tbody tr:visible").length;
    var message = visibleRows === 1 ? "No result found" : visibleRows - 1;
    $("#rowcount").html(message);
  }
  

console.log('DataTables is here')