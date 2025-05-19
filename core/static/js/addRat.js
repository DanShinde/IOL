// static/js/scripts.js
document.addEventListener('DOMContentLoaded', function () {
    const addRATButton = document.getElementById('add-rat-btn');
    const configPopup = document.getElementById('configPopup');
    const closeBtn = document.querySelector('.popup .close');
    const saveConfigBtn = document.getElementById('saveConfig');
    const availableSignals = document.getElementById('availableSignals');
    const pinMapping = document.getElementById('pinMapping');
    const moduleName = document.getElementById('module_name');

    if (!availableSignals || !pinMapping || !saveConfigBtn) {
        console.error("Required DOM elements not found.");
        return;
    }

    const signalsData = [
        { id: 1, code: "ROLLER_PROXY", device_type: "Proximity Sensor", signal_type: "DI"  },
        { id: 2, code: "WHEEL_PROXY", device_type: "Proximity Sensor", signal_type: "DI" },
        { id: 3, code: "PPS", device_type: "Retro Reflective Photo Sensor", signal_type: "DI" },
        { id: 4, code: "PORT1_DTS", device_type: "Retro Reflective Photo Sensor", signal_type: "DI" },
        { id: 4, code: "PORT2_DTS", device_type: "Retro Reflective Photo Sensor", signal_type: "DI" },
        { id: 4, code: "PORT3_DTS", device_type: "Retro Reflective Photo Sensor", signal_type: "DI" },
        { id: 5, code: "PORT4_DTS", device_type: "Retro Reflective Photo Sensor", signal_type: "DI" },
        { id: 7, code: "LIFTING_MDR_FWD", device_type: "Lift Mdr Fwd Command", signal_type: "DO" },
        { id: 8, code: "LIFTING_MDR_REV", device_type: "Lift Mdr Rev Command", signal_type: "DO" },
    ];

    const pinsData = ["Sen1", "Sen2", "In1", "In2", "In3", "In4", "Out1", "Out2", "Out3", "Out4"];

    const defaultAssignments = {
        "Sen1": "ROLLER_PROXY",
        "Sen2": "WHEEL_PROXY",
        "Out1": "LIFTING_MDR_FWD",
        "Out2": "LIFTING_MDR_REV",
        "In1": "PPS",
    };

    initializeUI();

    function initializeUI() {
        signalsData.forEach(signal => {
            const signalDiv = document.createElement('div');
            signalDiv.className = 'signal-item';
            signalDiv.setAttribute('draggable', true);
            signalDiv.setAttribute('data-signal-id', signal.id);
            signalDiv.innerHTML = `
                <strong>${signal.code}</strong><br>
                <small>${signal.device_type}</small>
            `;
            availableSignals.appendChild(signalDiv);
        });

        pinsData.forEach(pin => {
            const row = document.createElement('tr');
            const isDefaultPin = pin in defaultAssignments;
            console.log(pin, isDefaultPin);
            row.innerHTML = `
                <td>${pin}</td>
                <td class="pin-dropzone" style="margin:0.1 rem; padding:0.1rem;" data-pin="${pin}">${isDefaultPin ? '' : 'Drop signal here'}</td>
            `;
            pinMapping.appendChild(row);

            if (isDefaultPin) {
                const defaultSignal = signalsData.find(s => s.code === defaultAssignments[pin]);
                if (defaultSignal) {
                    const signalDiv = createAssignedSignalElement(defaultSignal, true);
                    row.lastElementChild.appendChild(signalDiv);
                }
            }
        });

        setupDnD();
    }

    function setupDnD() {
        const draggables = document.querySelectorAll('.signal-item');
        const dropzones = document.querySelectorAll('.pin-dropzone');

        draggables.forEach(draggable => {
            draggable.addEventListener('dragstart', handleDragStart);
            draggable.addEventListener('dragend', handleDragEnd);
        });

        dropzones.forEach(dropzone => {
            dropzone.addEventListener('dragover', handleDragOver);
            dropzone.addEventListener('drop', handleDrop);
            dropzone.addEventListener('dragenter', handleDragEnter);
            dropzone.addEventListener('dragleave', handleDragLeave);
        });
    }

    function createAssignedSignalElement(signal, isDefault = false) {
        const signalDiv = document.createElement('div');
        signalDiv.className = isDefault ? 'assigned-signal default-signal' : 'assigned-signal';
        signalDiv.innerHTML = `
            <strong>${signal.code}</strong>
            <small>${signal.device_type}</small>
            ${isDefault ? '' : '<span class="remove-signal">×</span>'}
        `;

        if (!isDefault) {
            signalDiv.querySelector('.remove-signal').addEventListener('click', (e) => {
                e.stopPropagation();
                signalDiv.parentElement.innerHTML = 'Drop signal here';
            });
        }

        return signalDiv;
    }

    let draggedItem = null;

    function handleDragStart(e) {
        draggedItem = this;
        this.classList.add('dragging');
    }

    function handleDragEnd(e) {
        this.classList.remove('dragging');
    }

    function handleDragOver(e) {
        e.preventDefault();
    }

    function handleDragEnter(e) {
        e.preventDefault();
        this.style.backgroundColor = '#e6f2ff';
    }

    function handleDragLeave(e) {
        this.style.backgroundColor = 'transparent';
    }

    function handleDrop(e) {
        e.preventDefault();
        this.style.backgroundColor = 'transparent';

        if (draggedItem && !this.querySelector('.assigned-signal')) {
            const signalId = draggedItem.getAttribute('data-signal-id');
            const signal = signalsData.find(s => s.id === parseInt(signalId));

            if (signal) {
                const assignedSignal = createAssignedSignalElement(signal);
                this.innerHTML = '';
                this.appendChild(assignedSignal);
            }
        }
    }

    function saveConfiguration() {
        const assignments = [];
        const rows = pinMapping.querySelectorAll('tr');

        rows.forEach(row => {
            const pin = (row.querySelector('td:first-child')?.textContent || '').trim() || 'unknown';
            const signalEl = row.querySelector('td:last-child .assigned-signal');
            if (signalEl) {
                code1 = signalEl.querySelector('strong')?.textContent || 'unknown';
            assignments.push({
                pin,
                code: code1,
                device_type: signalsData.find(s => s.code === code1).device_type,
                signal_type: signalsData.find(s => s.code === code1).signal_type
            });
            } else {
            assignments.push({ pin, signal: null });
            }
        });

        // build the payload
        const payload = {
            module_name: document.getElementById('module_name').value,
            panel_number: document.getElementById('panel_number').value,
            card: "Add RAT",
            assignments
        };

        console.log('Sending configuration:', payload);

        $.ajax({
            url: '/sort/add_dccard/',
            method: 'POST',
            contentType: 'application/json; charset=utf-8',
            data: JSON.stringify(payload),
            headers: {
            'X-CSRFToken': getCookie('csrftoken')
            },
            success: function(response) {
            alert('Configuration saved successfully!');
            if (configPopup) configPopup.style.display = 'none';
            // maybe update UI with response?
            console.log('Server response:', response);
            },
            error: function(xhr, status, err) {
            console.error('Save failed:', status, err);
            alert('Error saving configuration. Please try again.');
            }
        });
        }


        if (addRATButton) {
        addRATButton.addEventListener('click', () => {
            // use .value on a DOM <input>
            if (moduleName.value.trim() === '') {
            alert('Please enter a module name.');
            return;
            }
            configPopup.style.display = 'block';
        });
        }

    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            if (configPopup) configPopup.style.display = 'none';
        });
    }

    saveConfigBtn.addEventListener('click', saveConfiguration);

    window.addEventListener('click', (event) => {
        if (configPopup && event.target === configPopup) {
            configPopup.style.display = 'none';
        }
    });
});