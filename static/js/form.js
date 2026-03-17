
let currentPage = 1;
let rowsPerPage = 10;
let rows, totalPages;
let currentTab = 1;
let originalRowsTable1, originalRowsTable2;
let column1Cells = [];
let column2Cells = [];
let column3Cells = [];
let column4Cells = [];
let column5Cells = [];
let column6Cells = [];
let column7Cells = [];
let column8Cells = [];
let column9Cells = [];
let column10Cells = [];
let column11Cells = [];
let column12Cells = [];
let column13Cells = [];
let column14Cells = [];
// CHANGE ME
// let columns = ['title_id', 'title_name', 'va_network', 'display_name', 'platform',
//     'daypart', 'cost_per_unit', 'impressions_per_unit', 'cpm', 'Clear'];
// let columnsMod = ['title_id', 'title_name', 'va_network', 'display_name', 'platform',
//     'daypart', 'cost_per_unit', 'impressions_per_unit', 'cpm'];

let columns = [
    'Network',
    'Daypart',
    'Daypart Type',
    'Number of spots',
    'Length',
    'CPM',
    'eCPM',
    'Unequiv VA Imps (Unit)',
    'Unequiv VA Imps (Total)',
    'Equiv VA Imps (Unit)',
    'Equiv VA Imps (Total)',
    'Equiv eCPM',
    'Unequiv Age-Gender Imps (Unit)',
    'Unequiv Age-Gender Imps (Total)',
    'Equiv Age-Gender Imps (Unit)',
    'Equiv Age-Gender Imps (Total)',
    'Unit Cost',
    'Total Cost',
    'Action'
    ];


let columns2 = ['title_id', 'title_name', 'va_network', 'display_name', 'platform',
    'daypart', 'cost_per_unit', 'impressions_per_unit', 'cpm', 'Action'];    

let columnsMod = [
    'Network',
    'Daypart',
    'Daypart Type',
    'Number of spots',
    'Length',
    'CPM',
    'eCPM',
    'Unequiv VA Imps (Unit)',
    'Unequiv VA Imps (Total)',
    'Equiv VA Imps (Unit)',
    'Equiv VA Imps (Total)',
    'Equiv eCPM',
    'Unequiv Age-Gender Imps (Unit)',
    'Unequiv Age-Gender Imps (Total)',
    'Equiv Age-Gender Imps (Unit)',
    'Equiv Age-Gender Imps (Total)',
    'Unit Cost',
    'Total Cost'
    ];

    
let columnsModTbl2 = ['title_id', 'title_name', 'va_network', 'display_name', 'platform',
        'daypart', 'cost_per_unit', 'impressions_per_unit', 'cpm'];    

function addToChange(button) {
    const row = button.parentElement.parentElement;
    const clone = row.cloneNode(true);
    const actionCell = clone.querySelector('td:last-child');
    actionCell.innerHTML = ''; // Clear the content of the Action cell
    const clearButton = document.createElement('button');
    clearButton.type = 'button';
    clearButton.className = 'btn btn-warning btn-sm';
    clearButton.textContent = 'Clear';
    clearButton.onclick = function() {
        this.parentElement.parentElement.remove();
    };
    actionCell.appendChild(clearButton);
    document.querySelector('#add-table tbody').appendChild(clone);
}

function removeFromChange(button) {
    const row = button.parentElement.parentElement;
    const clone = row.cloneNode(true);
    const actionCell = clone.querySelector('td:last-child');
    actionCell.innerHTML = ''; // Clear the content of the Action cell
    const clearButton = document.createElement('button');
    clearButton.type = 'button';
    clearButton.className = 'btn btn-warning btn-sm';
    clearButton.textContent = 'Clear';
    clearButton.onclick = function() {
        this.parentElement.parentElement.remove();
    };
    actionCell.appendChild(clearButton);
    document.querySelector('#remove-table tbody').appendChild(clone);
}


function addNewRow() {
    const addTable = document.querySelector('#add-table tbody');
    const newRow = document.createElement('tr');
     // Adjust these column names as necessary
    columns.forEach((col, index) => {
        const newCell = document.createElement('td');
        if (col === 'Action') {
            const clearButton = document.createElement('button');
            clearButton.type = 'button';
            clearButton.className = 'btn btn-warning btn-sm';
            clearButton.textContent = 'Clear';
            clearButton.onclick = function() {
                this.parentElement.parentElement.remove();
            };
            newCell.appendChild(clearButton);
        } else {
            const input = document.createElement('input');
            input.type = 'text';
            input.className = `form-control ${col.toLowerCase()}-${index}`;
            input.required = true;
            newCell.appendChild(input);
        }
        newRow.appendChild(newCell);
    });
    addTable.appendChild(newRow);
}



function initializePagination() {
    // Always refresh the rows from DOM when initializing
    if (currentTab === 1) {
        originalRowsTable1 = document.querySelectorAll('#table-container .main-table tbody tr');
        rows = originalRowsTable1;
    } else {
        originalRowsTable2 = document.querySelectorAll('#table-container-tab2 .main-table tbody tr');
        rows = originalRowsTable2;
    }

    totalPages = Math.ceil(rows.length / rowsPerPage);
    
    console.log(`[initializePagination] Total rows: ${rows.length}, Total pages: ${totalPages}, Rows per page: ${rowsPerPage}`);
    
    currentPage = 1; // Reset to the first page
    showPage(currentPage, false, false);
}


function updatePaginationButtons() {
    document.getElementById('prev-page').disabled = currentPage === 1;
    document.getElementById('next-page').disabled = currentPage === totalPages || totalPages === 0;
}

function showPage(page, filter, rows) {
    const tableContainer = currentTab === 1 ? document.getElementById('table-container') : document.getElementById('table-container-tab2');
    
    // Find or create scroll wrapper
    let scrollWrapper = tableContainer.querySelector('.table-scroll-wrapper');
    if (!scrollWrapper) {
        scrollWrapper = document.createElement('div');
        scrollWrapper.className = 'table-scroll-wrapper';
        tableContainer.innerHTML = '';
        tableContainer.appendChild(scrollWrapper);
    } else {
        scrollWrapper.innerHTML = ''; // Clear only the wrapper content
    }
    
    if (!filter){
        rows = currentTab === 1 ? originalRowsTable1 : originalRowsTable2;
    }

    const start = (page - 1) * rowsPerPage;
    const end = page * rowsPerPage;
    const paginatedRows = Array.from(rows).slice(start, end);

    // Update page counter
    const currentPageElement = document.querySelector('.currentPageCounter');
    const totalPageElement = document.querySelector('.totalPageCounter');
    currentPageElement.textContent = currentPage;
    totalPageElement.textContent = totalPages;

    const table = document.createElement('table');
    table.className = 'table table-bordered main-table';
    table.id = 'main-table'; // Ensure the ID is set

    const thead = document.createElement('thead');
    const tbody = document.createElement('tbody');

    // Create table header
    const headerRow = document.createElement('tr');

    if (currentTab === 1) {
        columns.forEach(col => {
            const th = document.createElement('th');
            th.textContent = col;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
    }
    else{
        columns2.forEach(col => {
            const th = document.createElement('th');
            th.textContent = col;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
    }
   

    // Append rows to tbody
    paginatedRows.forEach(row => {
        tbody.appendChild(row.cloneNode(true));
    });

    table.appendChild(thead);
    table.appendChild(tbody);
    scrollWrapper.appendChild(table); // Append to wrapper instead of container
    updatePaginationButtons();
    currentTab === 1 ? initializeAutocomplete(1) : initializeAutocomplete(2); // adapts to whatever tab you're on
}


function nextPage() {
    if (currentPage < totalPages) {
        currentPage++;
        showPage(currentPage, false, false);
    }
}

function prevPage() {
    if (currentPage > 1) {
        currentPage--;
        showPage(currentPage, false, false);
    }
}

function switchTab() {
    currentTab = currentTab === 1 ? 2 : 1;

    document.getElementById('table-container').style.display = currentTab === 1 ? '' : 'none';
    document.getElementById('table-container-tab2').style.display = currentTab === 2 ? '' : 'none';
    
    const table = document.getElementById('filter-table');
    const inputRow = table.querySelector('thead tr:nth-child(2)');
    const headerRow = table.querySelector('thead tr:first-child');

    // Clear existing input and header rows
    inputRow.innerHTML = '';
    headerRow.innerHTML = '';

    let headersArray = currentTab === 2 ? columnsModTbl2 : columnsMod;

    headersArray.forEach((headerText, _) => {
        // Create new header cell
        const newHeader = document.createElement('th');
        newHeader.textContent = headerText;
        headerRow.appendChild(newHeader);

        // Create new input cell
        const newCell = document.createElement('td');
        const newInput = document.createElement('input');
        newInput.type = 'text';
        newInput.placeholder = `Filter ${headerText} here...`
        newCell.appendChild(newInput);
        inputRow.appendChild(newCell);
    });

    // If there are more header cells than in headersArray, remove the extras
    while (headerRow.children.length > headersArray.length) {
        headerRow.removeChild(headerRow.lastChild);
    }

    while (inputRow.children.length > headersArray.length) {
        inputRow.removeChild(inputRow.lastChild);
    }
    currentTab === 1 ? initializeAutocomplete(1) : initializeAutocomplete(2); 
}



function filterRows() {
    const table = document.getElementById('filter-table');
    const filterCriteria = {};
    const headers = Array.from(table.querySelectorAll('thead tr:first-child th')).map(th => th.textContent);

    // Select the second row in thead which contains the input fields
    const inputRow = table.querySelector('thead tr:nth-child(2)');
    
    Array.from(inputRow.querySelectorAll('td input')).forEach((input, index) => {
        const headerKey = headers[index];
        const inputValue = input.value.trim();
        if (inputValue !== '') {
            filterCriteria[headerKey] = inputValue.toLowerCase();
        }
    });

    // Filter the rows
    rowsToUse = currentTab === 1 ? originalRowsTable1 : originalRowsTable2
    const filteredRows = Array.from(rowsToUse).filter(row => {
        return Object.entries(filterCriteria).every(([key, value]) => {
            const cellIndex = headers.indexOf(key);
            const cellInput = row.querySelectorAll('td input')[cellIndex];
            if (!cellInput) {
                return false;
            }
            const cellValue = cellInput.value.toLowerCase().trim();
            return cellValue === (value);
        });
    });
    // Update the table with filtered rows
    updateTable(filteredRows);
    currentPage = 1;
    rows = filteredRows;
    console.log(`Running showPages. rows.length = ${rows.length} & rowsPerPage = ${rowsPerPage}`)
    totalPages = Math.ceil(rows.length / rowsPerPage);
    showPage(currentPage, true, rows);
}

function updateTable(filteredRows) {
    const tableBody = document.querySelector('#main-table tbody');
    tableBody.innerHTML = '';
    filteredRows.forEach(row => {
        tableBody.appendChild(row.cloneNode(true));
    });
}

function getUniqueTableEntries(tabNumber) {
    const rootRows = tabNumber === 1 ? originalRowsTable1 : originalRowsTable2;
    const cols = currentTab === 1 ? columnsMod : columnsModTbl2
    column1Cells = [];
    column2Cells = [];
    column3Cells = [];
    column4Cells = [];
    column5Cells = [];
    column6Cells = [];
    column7Cells = [];
    column8Cells = [];
    column9Cells = [];
    column10Cells = [];
    column11Cells = [];
    column12Cells = [];
    column13Cells = [];
    column14Cells = [];
    const uniqueCellsPerColumn = [column1Cells, column2Cells, column3Cells,column4Cells,column5Cells,column6Cells,column7Cells,column8Cells,column9Cells,column10Cells,column11Cells,column12Cells,column13Cells,column14Cells];
    rootRows.forEach(row => {
        cols.forEach((_, index) => {
            const cellInput = row.querySelectorAll('td input')[index];
            const cellValue = cellInput.value.toLowerCase().trim();
            const uniqueCells = uniqueCellsPerColumn[index];
            if (cellValue !== undefined && uniqueCells !== undefined) {
                if (!uniqueCells.includes(cellValue)) {
                    uniqueCells.push(cellValue);
                }
            }
        });
    });
    return uniqueCellsPerColumn;
}

function autocomplete(inp, arr) {

    /*the autocomplete function takes two arguments,
    the text field element and an array of possible autocompleted values:*/
    var currentFocus;
    /*execute a function when someone writes in the text field:*/
    inp.addEventListener("input", function(e) {
        var a, b, i, val = this.value;
        /*close any already open lists of autocompleted values*/
        closeAllLists();
        if (!val) { return false;}
        currentFocus = -1;
        /*create a DIV element that will contain the items (values):*/
        a = document.createElement("DIV");
        a.setAttribute("id", this.id + "autocomplete-list");
        a.setAttribute("class", "autocomplete-items");
        /*append the DIV element as a child of the autocomplete container:*/
        this.parentNode.appendChild(a);
        /*for each item in the array...*/
        for (i = 0; i < arr.length; i++) {
          /*check if the item starts with the same letters as the text field value:*/
          if (arr[i].substr(0, val.length).toUpperCase() == val.toUpperCase()) {
            /*create a DIV element for each matching element:*/
            b = document.createElement("DIV");
            /*make the matching letters bold:*/
            b.innerHTML = "<strong>" + arr[i].substr(0, val.length) + "</strong>";
            b.innerHTML += arr[i].substr(val.length);
            /*insert a input field that will hold the current array item's value:*/
            b.innerHTML += "<input type='hidden' value='" + arr[i] + "'>";
            /*execute a function when someone clicks on the item value (DIV element):*/
                b.addEventListener("click", function(e) {
                /*insert the value for the autocomplete text field:*/
                inp.value = this.getElementsByTagName("input")[0].value;
                /*close the list of autocompleted values,
                (or any other open lists of autocompleted values:*/
                closeAllLists();
            });
            a.appendChild(b);
          }
        }
    });
    /*execute a function presses a key on the keyboard:*/
    inp.addEventListener("keydown", function(e) {
        var x = document.getElementById(this.id + "autocomplete-list");
        if (x) x = x.getElementsByTagName("div");
        if (e.keyCode == 40) {
          /*If the arrow DOWN key is pressed,
          increase the currentFocus variable:*/
          currentFocus++;
          /*and and make the current item more visible:*/
          addActive(x);
        } else if (e.keyCode == 38) { //up
          /*If the arrow UP key is pressed,
          decrease the currentFocus variable:*/
          currentFocus--;
          /*and and make the current item more visible:*/
          addActive(x);
        } else if (e.keyCode == 13) {
          /*If the ENTER key is pressed, prevent the form from being submitted,*/
          e.preventDefault();
          if (currentFocus > -1) {
            /*and simulate a click on the "active" item:*/
            if (x) x[currentFocus].click();
          }
        }
    });
    function addActive(x) {
      /*a function to classify an item as "active":*/
      if (!x) return false;
      /*start by removing the "active" class on all items:*/
      removeActive(x);
      if (currentFocus >= x.length) currentFocus = 0;
      if (currentFocus < 0) currentFocus = (x.length - 1);
      /*add class "autocomplete-active":*/
      x[currentFocus].classList.add("autocomplete-active");
    }
    function removeActive(x) {
      /*a function to remove the "active" class from all autocomplete items:*/
      for (var i = 0; i < x.length; i++) {
        x[i].classList.remove("autocomplete-active");
      }
    }
    function closeAllLists(elmnt) {
      /*close all autocomplete lists in the document,
      except the one passed as an argument:*/
      var x = document.getElementsByClassName("autocomplete-items");
      for (var i = 0; i < x.length; i++) {
        if (elmnt != x[i] && elmnt != inp) {
        x[i].parentNode.removeChild(x[i]);
      }
    }
  }
  }

// Takes tabNumber -- either 1 or 2 to indicate which uniques to grab
function initializeAutocomplete(tabNumber) {
    const uniqueCellsPerColumn = getUniqueTableEntries(tabNumber);
    const inputs = document.querySelectorAll("#filter-table input[type='text']");

    inputs.forEach((input, index) => {
        autocomplete(input, uniqueCellsPerColumn[index]);
    });
}

// Serialize table data for transport
function serializeTable(tableId) {
    const table = document.getElementById(tableId);
    const data = [];
    const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent);

    table.querySelectorAll('tbody tr').forEach(row => {
        const rowData = {};
        Array.from(row.querySelectorAll('td')).forEach((cell, index) => {
            rowData[headers[index]] = cell.querySelector('input') ? cell.querySelector('input').value : cell.textContent;
        });
        data.push(rowData);
    });
    return data;
}

function validateForm() {
    const requiredFields = document.querySelectorAll('#campaignForm input[required]');
    for (let field of requiredFields) {
        if (!field.value) {
            alert('Please fill out all required fields.');
            return false; // Prevent form submission
        }
    }
    return true; // Allow form submission
}

function saveScheduler(){
    originalButton = document.querySelector('#save > button');
        const newButton = document.createElement('button');
        newButton.className = 'btn btn-primary';
        newButton.type = 'button';
        newButton.disabled = true;
        const spinnerSpan = document.createElement('span');
        spinnerSpan.className = 'spinner-border spinner-border-sm';
        spinnerSpan.setAttribute('role', 'status');
        spinnerSpan.setAttribute('aria-hidden', 'true');
        newButton.appendChild(spinnerSpan);
        newButton.appendChild(document.createTextNode(' Loading...'));
        originalButton.replaceWith(newButton);

        const table1Data = serializeMainTable();
        const toAdd = serializeTable('add-table');
        const toRemove = serializeTable('remove-table');
        const budget = document.querySelector('#budget').value;
        const startDate = document.querySelector('#start_date').value;
        const endDate = document.querySelector('#end_date').value;
        const darkWeeks = document.querySelector('#dark_weeks').value;
        const schedulerName = document.querySelector('#scheduler_name').value;
        const selectedInput = document.querySelector('input[name="csvFiles"]:checked');
        const selectedDataset = selectedInput ? selectedInput.value : null;
        const loadScheduler = document.querySelector('#load_scheduler').value;

        // Capture custom minimum checkbox and value
        const useCustomMinimum = document.getElementById('use_custom_minimum')?.checked || false;
        const networkMinimumOverride = useCustomMinimum ? 
            (parseFloat(document.getElementById('network_minimum_override')?.value) || 0) : null;

        const payload = {
            table1: table1Data,
            toAdd: toAdd,
            toRemove: toRemove,
            budget:budget,
            start_date:startDate,
            end_date:endDate,
            dark_weeks:darkWeeks,
            selectedDataset:selectedDataset,
            load_scheduler:loadScheduler,
            use_custom_minimum: useCustomMinimum,
            network_minimum_override: networkMinimumOverride
        };

        fetch('/save_scheduler', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(response => response.json()) 
        .then(data => {
                if ('error' in data) {
                    document.getElementById('save_results').innerHTML = `An error occured: ${data['error']}`;
                    newButton.replaceWith(originalButton);
                }
                else {
                    document.getElementById('save_results').innerHTML = `Successfully saved the scheduler as <b>${schedulerName}!</b>`;
                    newButton.replaceWith(originalButton);
                }
        })
        .catch(error => {
            document.getElementById('save_results').innerHTML = `An error occured: ${error.message}`;
            newButton.replaceWith(originalButton);

        });
}


function ingestFormData() {

    if (validateForm() === true) {
        // Create loader button
        originalButton = document.querySelector('#campaignForm > button');
        const newButton = document.createElement('button');
        newButton.className = 'btn btn-primary';
        newButton.type = 'button';
        newButton.disabled = true;
        const spinnerSpan = document.createElement('span');
        spinnerSpan.className = 'spinner-border spinner-border-sm';
        spinnerSpan.setAttribute('role', 'status');
        spinnerSpan.setAttribute('aria-hidden', 'true');
        newButton.appendChild(spinnerSpan);
        newButton.appendChild(document.createTextNode(' Loading...'));
        originalButton.replaceWith(newButton);

        const table1Data = serializeMainTable();
        const toAdd = serializeTable('add-table');
        const toRemove = serializeTable('remove-table');
        const budget = document.querySelector('#budget').value;
        const startDate = document.querySelector('#start_date').value;
        const endDate = document.querySelector('#end_date').value;
        const darkWeeks = document.querySelector('#dark_weeks').value;
        const selectedInput = document.querySelector('input[name="csvFiles"]:checked');
        const selectedDataset = selectedInput ? selectedInput.value : null;
        const loadScheduler = document.querySelector('#load_scheduler').value;

        const payload = {
            table1: table1Data,
            toAdd: toAdd,
            toRemove: toRemove,
            budget:budget,
            start_date:startDate,
            end_date:endDate,
            dark_weeks:darkWeeks,
            selectedDataset:selectedDataset,
            load_scheduler:loadScheduler
        };

        fetch('/do_math', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(response => {
            
            // Distinguish between an error or raw HTML (success)
            const contentType = response.headers.get('Content-Type');
            if (contentType && contentType.includes('application/json')) {
                return response.json();
            } else {
                return response.text();
            }
        })
        .then(data => {

            if (typeof data === 'object' && data !== null && 'error' in data) {
                document.querySelector('.alert.alert-success[role="alert"]').innerHTML = `<b>An error occurred: </b> ${data['error']}`;
                document.querySelector('.alert.alert-success[role="alert"]').className = "alert alert-danger";
                newButton.replaceWith(originalButton);
            } else {
                document.getElementById('success').innerHTML = `
                    <div class="alert alert-success" role="alert">
                        Form submitted successfully.
                    </div>
                    ${data}
                `;
                // Reset rows
                originalRowsTable1 = document.querySelectorAll('#table-container .main-table tbody tr');
                initializePagination();
                showPage(currentPage);
                newButton.replaceWith(originalButton);

            }
        })
        .catch(error => {
            document.querySelector('.alert.alert-success[role="alert"]').innerHTML = `<b>An error occurred: </b> ${error.message}`;
            document.querySelector('.alert.alert-success[role="alert"]').className = "alert alert-danger";
            newButton.replaceWith(originalButton);
        });
    }
}

function serializeMainTable() {
    const table = document.querySelector('.main-table'); // Adjust this selector if needed
    const headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent.trim());
    const data = [];

    originalRowsTable1.forEach(row => {
        const rowData = {};
        Array.from(row.querySelectorAll('td')).forEach((cell, index) => {
            rowData[headers[index]] = cell.querySelector('input') ? cell.querySelector('input').value : cell.textContent.trim();
        });
        data.push(rowData);
    });
    return data;
}

function downloadResults(){

    data = serializeMainTable();
    budget = document.querySelector('#budget').value;
    startDate = document.querySelector('#start_date').value;
    endDate = document.querySelector('#end_date').value;
    const darkWeeks = document.querySelector('#dark_weeks').value;
    const loadScheduler = document.querySelector('#load_scheduler').value;

    const payload = JSON.stringify({
        data: data,
        budget: budget,
        start_date:startDate,
        end_date:endDate,
        dark_weeks:darkWeeks,
        load_Scheduler:loadScheduler
    });
        
    
    fetch('/download_ranker', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `ranker-${startDate}-to-${endDate}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    })
    .catch(error => {
        console.error('There was a problem with the fetch operation:', error);
        alert('Error downloading results. Please check the console for details.');
    });
}

// Wait for the DOM to be fully loaded before calling ingestFormData
document.addEventListener('DOMContentLoaded', () => {
    // Attach event listener to the button or form submission
    const submitButton = document.getElementById('submitButton');
    submitButton.addEventListener('click', ingestFormData);

});

function viewBackupNetworks() {
    // Get primary networks from current table
    const primaryNetworks = getPrimaryNetworksList();
    
    if (primaryNetworks.length === 0) {
        alert('No primary networks found with allocated spots');
        return;
    }
    
    // Get current form data from the DOM
    const formData = getCurrentFormData();
    
    // Send JSON data via fetch instead of form submission
    fetch('/generate_backup_networks', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            ...formData,
            exclude_networks: primaryNetworks
        })
    })
    .then(response => response.text())
    .then(html => {
        // Open backup results in new window/tab
        const newWindow = window.open('', '_blank');
        newWindow.document.write(html);
        newWindow.document.close();
    })
    .catch(error => {
        console.error('Error generating backup networks:', error);
        alert('Error generating backup networks: ' + error.message);
    });
}

function getPrimaryNetworksList() {
    const networks = new Set();
    
    originalRowsTable1.forEach(row => {
        const networkCell = row.querySelector('td:first-child input');
        if (networkCell && networkCell.value && networkCell.value.trim()) {
            const spotsCell = row.querySelector('td:nth-child(4) input');
            if (spotsCell && spotsCell.value) {
                const spotCount = parseFloat(spotsCell.value.replace(/,/g, ''));
                if (spotCount > 0) {
                    networks.add(networkCell.value.trim());
                }
            }
        }
    });
    
    console.log('Primary networks found:', Array.from(networks));
    return Array.from(networks);
}

function getCurrentFormData() {
    const useCustomMinimum = document.querySelector('#use_custom_minimum')?.checked || false;
    return {
        budget: document.querySelector('#budget')?.value || 1000000,
        start_date: document.querySelector('#start_date')?.value || '2025-01-01',
        end_date: document.querySelector('#end_date')?.value || '2025-12-31',
        dark_weeks: document.querySelector('#dark_weeks')?.value || 0,
        selectedDataset: document.querySelector('input[name="csvFiles"]:checked')?.value || 'default',
        load_scheduler: document.querySelector('#load_scheduler')?.value || '',
        spots_15s: document.querySelector('#spots_15s')?.value || 0,
        spots_30s: document.querySelector('#spots_30s')?.value || 100,
        spots_60s: document.querySelector('#spots_60s')?.value || 0,
        spots_75s: document.querySelector('#spots_75s')?.value || 0,
        spots_90s: document.querySelector('#spots_90s')?.value || 0,
        include_hispanic: document.querySelector('#include_hispanic')?.checked || false,
        original_client_budget: document.querySelector('#client_budget')?.value || 0,
        final_net_media_budget: document.querySelector('#budget')?.value || 0,
        use_custom_minimum: useCustomMinimum,
        network_minimum_override: useCustomMinimum ? 
            (parseFloat(document.querySelector('#network_minimum_override')?.value) || 0) : null,
        require_broadcast: document.querySelector('#require_broadcast')?.checked || false    
    };
}